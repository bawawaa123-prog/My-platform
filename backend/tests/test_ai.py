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
