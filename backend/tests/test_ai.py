from fastapi.testclient import TestClient


def test_mock_ticket_classification_uses_local_fallback_rules(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    ticket = create_ticket(
        title="Urgent refund dispute",
        content="Customer requests an urgent refund ASAP and is angry about the failed charge.",
    )

    response = client.post(
        f"/api/ai/tickets/{ticket['id']}/classify",
        headers=auth_headers,
    )

    assert response.status_code == 200
    classification = response.json()
    assert classification["category"] == "refund"
    assert classification["priority"] == "urgent"
    assert classification["sentiment"] == "angry"
    assert classification["need_human"] is True
    assert classification["recommended_department"] == "billing"


def test_generate_reply_creates_mock_suggestion_with_sources(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    upload_response = client.post(
        "/api/knowledge/upload",
        data={"title": "Order Payment Recovery Guide"},
        files={
            "file": (
                "payment_guide.md",
                (
                    b"If payment succeeds but the order stays pending, verify the callback logs, "
                    b"confirm order synchronization, and manually requeue the order update."
                ),
                "text/markdown",
            )
        },
        headers=auth_headers,
    )
    assert upload_response.status_code == 200

    ticket = create_ticket(
        title="Order still pending after payment",
        content="The customer completed payment, but the order status did not update.",
    )

    reply_response = client.post(
        f"/api/ai/tickets/{ticket['id']}/generate-reply",
        headers=auth_headers,
    )

    assert reply_response.status_code == 200
    reply = reply_response.json()
    assert reply["status"] == "draft"
    assert reply["suggested_content"].startswith("[MOCK:0.2]")
    assert 0.15 <= reply["confidence"] <= 0.95
    assert len(reply["sources_json"]) >= 1

    suggestions_response = client.get(
        f"/api/ai/tickets/{ticket['id']}/suggestions",
        headers=auth_headers,
    )
    assert suggestions_response.status_code == 200
    suggestions = suggestions_response.json()
    assert len(suggestions) == 1
    assert suggestions[0]["id"] == reply["id"]


# ============================================================================
# Helpers for Multi-Agent start/resume tests
# ============================================================================


def start_multi_agent(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
) -> dict:
    """Start the Multi-Agent workflow and return the pending_review response."""
    response = client.post(
        f"/api/ai/tickets/{ticket_id}/multi-agent-process/start",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def resume_multi_agent(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
    payload: dict,
) -> dict:
    """Resume the Multi-Agent workflow with a review decision."""
    response = client.post(
        f"/api/ai/tickets/{ticket_id}/multi-agent-process/resume",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def list_agent_runs(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
) -> list[dict]:
    """List AgentRunLog records for a ticket."""
    response = client.get(
        f"/api/ai/tickets/{ticket_id}/agent-runs",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def list_ticket_messages(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
) -> list[dict]:
    """List ticket messages (conversation history)."""
    response = client.get(
        f"/api/tickets/{ticket_id}/messages",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


# ============================================================================
# Test 1: start returns pending_review and writes interrupted AgentRunLog
# ============================================================================


def test_multi_agent_start_returns_pending_review_and_interrupted_run_log(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that start() returns pending_review with all 7 agent results,
    a draft reply, an audit trail, and that an AgentRunLog is created with
    status=interrupted."""
    ticket = create_ticket(
        title="Urgent payment issue",
        content="Customer paid successfully but the order is still pending.",
        category="payment",
        priority="urgent",
    )

    result = start_multi_agent(client, ticket["id"], auth_headers)

    # Core workflow fields
    assert result["status"] == "pending_review"
    assert result["pending_node"] == "human_review"
    assert result["run_id"]
    assert result["thread_id"] == result["run_id"]
    assert result["ticket"]["id"] == ticket["id"]

    # All 7 agent results present
    assert "supervisor_result" in result
    assert "triage_result" in result
    assert "knowledge_result" in result
    assert "similar_case_result" in result
    assert "reply_result" in result
    assert "risk_result" in result
    assert "workflow_result" in result

    # Draft reply
    assert result["draft_reply"]["status"] == "draft"
    assert result["draft_reply"]["suggestion_type"] == "reply"

    # Audit trail
    assert isinstance(result["audit_trail"], list)
    assert len(result["audit_trail"]) >= 1

    # AgentRunLog check: a run log with status=interrupted must exist
    runs = list_agent_runs(client, ticket["id"], auth_headers)
    matched = next(run for run in runs if run["run_id"] == result["run_id"])
    assert matched["run_type"] == "multi_agent"
    assert matched["status"] == "interrupted"
    assert matched["ticket_id"] == ticket["id"]


# ============================================================================
# Test 2: resume approve completes the run and appends a ticket message
# ============================================================================


def test_multi_agent_resume_approve_completes_run_without_ticket_message(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resume(approve) sets the run status to completed and does NOT
    append any agent-type ticket message to the conversation history."""
    ticket = create_ticket(
        title="Refund request after failed payment",
        content="Customer asks for help with a failed payment and refund.",
        category="refund",
        priority="high",
    )

    pending = start_multi_agent(client, ticket["id"], auth_headers)
    run_id = pending["run_id"]

    before_messages = list_ticket_messages(client, ticket["id"], auth_headers)

    final = resume_multi_agent(
        client,
        ticket["id"],
        auth_headers,
        {"action": "approve", "run_id": run_id},
    )

    assert final["review_decision"]["action"] == "approve"
    assert final["reviewed_suggestion"]["status"] == "approved"

    # No new message should be appended — conversation history is for real communication
    after_messages = list_ticket_messages(client, ticket["id"], auth_headers)
    assert len(after_messages) == len(before_messages)

    # AgentRunLog should now be completed
    runs = list_agent_runs(client, ticket["id"], auth_headers)
    matched = next(run for run in runs if run["run_id"] == run_id)
    assert matched["status"] == "completed"
    assert matched["run_type"] == "multi_agent"
    assert matched["output_json"]["reviewed_suggestion"]["status"] == "approved"


# ============================================================================
# Test 3: resume edit uses final_content for the ticket message
# ============================================================================


def test_multi_agent_resume_edit_saves_final_content_without_ticket_message(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resume(edit) stores the human-edited final_content in the
    reviewed suggestion, and does NOT append a ticket message."""
    ticket = create_ticket(
        title="Order status did not update",
        content="Customer paid but order remains pending.",
        category="payment",
        priority="high",
    )

    pending = start_multi_agent(client, ticket["id"], auth_headers)
    run_id = pending["run_id"]

    before_messages = list_ticket_messages(client, ticket["id"], auth_headers)

    final_content = "Edited final multi-agent reply for the customer."

    final = resume_multi_agent(
        client,
        ticket["id"],
        auth_headers,
        {
            "action": "edit",
            "run_id": run_id,
            "final_content": final_content,
        },
    )

    assert final["review_decision"]["action"] == "edit"
    assert final["reviewed_suggestion"]["status"] == "edited"
    assert final["reviewed_suggestion"]["final_content"] == final_content

    # No new message should be appended
    after_messages = list_ticket_messages(client, ticket["id"], auth_headers)
    assert len(after_messages) == len(before_messages)
    assert not any(message["content"] == final_content for message in after_messages)

    # AgentRunLog must be completed
    runs = list_agent_runs(client, ticket["id"], auth_headers)
    matched = next(run for run in runs if run["run_id"] == run_id)
    assert matched["status"] == "completed"


# ============================================================================
# Test 4: resume reject completes without appending a ticket message
# ============================================================================


def test_multi_agent_resume_reject_completes_without_ticket_message(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resume(reject) completes the workflow and marks the
    suggestion as rejected, but does NOT append a ticket message."""
    ticket = create_ticket(
        title="Complaint requires manual handling",
        content="Customer is angry and asks for escalation.",
        category="other",
        priority="urgent",
    )

    pending = start_multi_agent(client, ticket["id"], auth_headers)
    run_id = pending["run_id"]

    before_messages = list_ticket_messages(client, ticket["id"], auth_headers)

    final = resume_multi_agent(
        client,
        ticket["id"],
        auth_headers,
        {
            "action": "reject",
            "run_id": run_id,
            "reject_reason": "The draft is not appropriate for this customer.",
        },
    )

    assert final["review_decision"]["action"] == "reject"
    assert final["reviewed_suggestion"]["status"] == "rejected"

    # No new message should appear after reject
    after_messages = list_ticket_messages(client, ticket["id"], auth_headers)
    assert len(after_messages) == len(before_messages)

    # AgentRunLog must still be completed
    runs = list_agent_runs(client, ticket["id"], auth_headers)
    matched = next(run for run in runs if run["run_id"] == run_id)
    assert matched["status"] == "completed"


# ============================================================================
# Test 5: edit requires final_content (422)
# ============================================================================


def test_multi_agent_resume_edit_requires_final_content(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resume(edit) without final_content returns 422."""
    ticket = create_ticket(
        title="Edit requires final content",
        content="Customer needs a response.",
    )

    pending = start_multi_agent(client, ticket["id"], auth_headers)

    response = client.post(
        f"/api/ai/tickets/{ticket['id']}/multi-agent-process/resume",
        json={"action": "edit", "run_id": pending["run_id"]},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ============================================================================
# Test 6: reject requires reject_reason (422)
# ============================================================================


def test_multi_agent_resume_reject_requires_reject_reason(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resume(reject) without reject_reason returns 422."""
    ticket = create_ticket(
        title="Reject requires reason",
        content="Customer needs a response.",
    )

    pending = start_multi_agent(client, ticket["id"], auth_headers)

    response = client.post(
        f"/api/ai/tickets/{ticket['id']}/multi-agent-process/resume",
        json={"action": "reject", "run_id": pending["run_id"]},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ============================================================================
# Test 7: wrong ticket_id returns 400
# ============================================================================


def test_multi_agent_resume_wrong_ticket_returns_400(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resuming with a run_id that belongs to a different ticket
    returns 400."""
    ticket_a = create_ticket(title="Ticket A")
    ticket_b = create_ticket(title="Ticket B")

    pending = start_multi_agent(client, ticket_a["id"], auth_headers)

    response = client.post(
        f"/api/ai/tickets/{ticket_b['id']}/multi-agent-process/resume",
        json={"action": "approve", "run_id": pending["run_id"]},
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "does not belong to the requested ticket" in response.json()["detail"]


# ============================================================================
# Test 8: duplicate resume returns error without duplicating the message
# ============================================================================


def test_multi_agent_resume_duplicate_returns_error_without_duplicate_message(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket,
) -> None:
    """Verify that resuming an already-completed run returns 400/404 and does
    NOT create a duplicate ticket message."""
    ticket = create_ticket(
        title="Duplicate multi-agent resume",
        content="Make sure duplicate resume does not create duplicate message.",
    )

    pending = start_multi_agent(client, ticket["id"], auth_headers)
    run_id = pending["run_id"]

    # First resume — should succeed
    first_response = client.post(
        f"/api/ai/tickets/{ticket['id']}/multi-agent-process/resume",
        json={"action": "approve", "run_id": run_id},
        headers=auth_headers,
    )
    assert first_response.status_code == 200, first_response.text

    messages_after_first = list_ticket_messages(client, ticket["id"], auth_headers)

    # Second resume with the same run_id — must return an error
    second_response = client.post(
        f"/api/ai/tickets/{ticket['id']}/multi-agent-process/resume",
        json={"action": "approve", "run_id": run_id},
        headers=auth_headers,
    )
    assert second_response.status_code in {400, 404}, second_response.text

    # No extra message should have been created
    messages_after_second = list_ticket_messages(client, ticket["id"], auth_headers)
    assert len(messages_after_second) == len(messages_after_first)
