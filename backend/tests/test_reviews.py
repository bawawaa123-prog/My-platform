from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.ai_suggestion import AISuggestion


def login_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _inject_suggestion(db: Session, ticket_id: int) -> AISuggestion:
    suggestion = AISuggestion(
        ticket_id=ticket_id,
        suggestion_type="reply",
        suggested_content="Suggested reply for review RBAC test.",
        reasoning_summary="Created by test.",
        sources_json=[],
        confidence=0.8,
        status="draft",
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


@pytest.fixture
def agent_headers(client: TestClient) -> dict[str, str]:
    return login_headers(client, "agent@example.com", "agent123")


@pytest.fixture
def viewer_headers(client: TestClient) -> dict[str, str]:
    return login_headers(client, "viewer@example.com", "viewer123")


# ---------------------------------------------------------------------------
# admin tests
# ---------------------------------------------------------------------------


def test_admin_can_approve_suggestion(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Admin can approve a draft suggestion."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])

    response = client.post(
        f"/api/reviews/{suggestion.id}/approve",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == suggestion.id
    assert data["status"] == "approved"


def test_admin_can_reject_suggestion(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Admin can reject a draft suggestion with a reason."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])

    response = client.post(
        f"/api/reviews/{suggestion.id}/reject",
        json={"reject_reason": "Not suitable for customer reply."},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == suggestion.id
    assert data["status"] == "rejected"
    assert data["reject_reason"] == "Not suitable for customer reply."


# ---------------------------------------------------------------------------
# agent tests
# ---------------------------------------------------------------------------


def test_agent_can_approve_suggestion(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Agent can approve a draft suggestion."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])

    response = client.post(
        f"/api/reviews/{suggestion.id}/approve",
        json={},
        headers=agent_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == suggestion.id
    assert data["status"] == "approved"


def test_agent_can_edit_suggestion(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Agent can edit a draft suggestion with custom content."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])

    response = client.post(
        f"/api/reviews/{suggestion.id}/edit",
        json={"final_content": "Edited final response from agent."},
        headers=agent_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == suggestion.id
    assert data["status"] == "edited"
    assert data["final_content"] == "Edited final response from agent."


# ---------------------------------------------------------------------------
# viewer RBAC rejection tests
# ---------------------------------------------------------------------------


REVIEW_ENDPOINTS = [
    pytest.param("approve", {}, id="approve"),
    pytest.param("edit", {"final_content": "Viewer should not edit."}, id="edit"),
    pytest.param("reject", {"reject_reason": "Viewer should not reject."}, id="reject"),
]


@pytest.mark.parametrize("action,payload", REVIEW_ENDPOINTS)
def test_viewer_cannot_review_suggestion(
    client: TestClient,
    viewer_headers: dict[str, str],
    create_ticket: Callable[..., dict],
    action: str,
    payload: dict,
) -> None:
    """Viewer gets 403 on all review endpoints."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])

    response = client.post(
        f"/api/reviews/{suggestion.id}/{action}",
        json=payload,
        headers=viewer_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Reviewer role required"


@pytest.mark.parametrize("action,payload", REVIEW_ENDPOINTS)
def test_unauthenticated_user_cannot_review_suggestion(
    client: TestClient,
    create_ticket: Callable[..., dict],
    action: str,
    payload: dict,
) -> None:
    """Unauthenticated user gets 401 on all review endpoints."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])

    response = client.post(
        f"/api/reviews/{suggestion.id}/{action}",
        json=payload,
    )
    assert response.status_code == 401


def create_suggestion(
    db: Session,
    *,
    ticket_id: int,
    suggestion_type: str = "reply",
    status: str = "draft",
) -> AISuggestion:
    """Flexible helper to create an AISuggestion with configurable type and status."""
    suggestion = AISuggestion(
        ticket_id=ticket_id,
        suggestion_type=suggestion_type,
        suggested_content="Suggested reply for pending queue test.",
        reasoning_summary="Created by test.",
        sources_json=[],
        confidence=0.8,
        status=status,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


# ---------------------------------------------------------------------------
# pending-suggestions queue tests (Step 5)
# ---------------------------------------------------------------------------


def test_list_pending_suggestions_requires_auth(
    client: TestClient,
) -> None:
    """Unauthenticated request returns 401."""
    response = client.get("/api/reviews/pending-suggestions")
    assert response.status_code == 401


def test_list_pending_suggestions_returns_draft_reply_suggestions(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Draft reply suggestion appears in the pending queue."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_suggestion(db, ticket_id=ticket["id"])

    response = client.get(
        "/api/reviews/pending-suggestions",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    assert any(
        item["id"] == suggestion.id
        and item["ticket_id"] == ticket["id"]
        and item["ticket_title"] == ticket["title"]
        and item["suggestion_type"] == "reply"
        and item["status"] == "draft"
        and item["suggested_content"] is not None
        and item["confidence"] is not None
        for item in data["items"]
    )


def test_list_pending_suggestions_excludes_reviewed_suggestions(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Approved / edited / rejected suggestions should not appear in pending queue."""
    ticket = create_ticket()
    with next(get_db()) as db:
        s_draft = create_suggestion(db, ticket_id=ticket["id"], status="draft")
        s_approved = create_suggestion(db, ticket_id=ticket["id"], status="approved")
        s_edited = create_suggestion(db, ticket_id=ticket["id"], status="edited")
        s_rejected = create_suggestion(db, ticket_id=ticket["id"], status="rejected")
        reviewed_ids = {s_approved.id, s_edited.id, s_rejected.id}
        draft_id = s_draft.id

    response = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids = {item["id"] for item in data["items"]}

    assert draft_id in returned_ids
    assert reviewed_ids.isdisjoint(returned_ids)
    assert all(item["status"] == "draft" for item in data["items"])


def test_list_pending_suggestions_excludes_non_reply_suggestions(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Only suggestion_type='reply' should appear in pending queue."""
    ticket = create_ticket()
    with next(get_db()) as db:
        s_classification = create_suggestion(
            db, ticket_id=ticket["id"], suggestion_type="classification", status="draft"
        )
        s_reply = create_suggestion(
            db, ticket_id=ticket["id"], suggestion_type="reply", status="draft"
        )
        reply_id = s_reply.id
        classification_id = s_classification.id

    response = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids = {item["id"] for item in data["items"]}

    assert reply_id in returned_ids
    assert classification_id not in returned_ids
    assert all(item["suggestion_type"] == "reply" for item in data["items"])


def test_list_pending_suggestions_filters_by_ticket_id(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """ticket_id filter should only return suggestions for that ticket."""
    ticket_a = create_ticket()
    ticket_b = create_ticket()
    with next(get_db()) as db:
        s_a = create_suggestion(db, ticket_id=ticket_a["id"])
        s_b = create_suggestion(db, ticket_id=ticket_b["id"])
        s_a_id = s_a.id
        s_b_id = s_b.id

    response = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket_a['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    returned_ids = {item["id"] for item in data["items"]}

    assert s_a_id in returned_ids
    assert s_b_id not in returned_ids
    assert all(item["ticket_id"] == ticket_a["id"] for item in data["items"])


def test_list_pending_suggestions_paginates_results(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """limit / offset pagination works and total reflects unfiltered count."""
    ticket = create_ticket()
    with next(get_db()) as db:
        for _ in range(3):
            create_suggestion(db, ticket_id=ticket["id"])

    response = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket['id']}&limit=2&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2


def test_list_pending_suggestions_respects_offset(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Different offsets return different items."""
    ticket = create_ticket()
    with next(get_db()) as db:
        for _ in range(3):
            create_suggestion(db, ticket_id=ticket["id"])

    page1 = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket['id']}&limit=1&offset=0",
        headers=auth_headers,
    )
    page2 = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket['id']}&limit=1&offset=1",
        headers=auth_headers,
    )
    assert page1.status_code == 200
    assert page2.status_code == 200
    items1 = page1.json()["items"]
    items2 = page2.json()["items"]
    if items1 and items2:
        assert items1[0]["id"] != items2[0]["id"]


def test_list_pending_suggestions_offset_beyond_total_returns_empty_items(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Offset beyond total returns empty items list."""
    ticket = create_ticket()
    with next(get_db()) as db:
        create_suggestion(db, ticket_id=ticket["id"])

    response = client.get(
        f"/api/reviews/pending-suggestions?ticket_id={ticket['id']}&limit=20&offset=999",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 999


@pytest.mark.parametrize(
    "query_string",
    [
        pytest.param("limit=0", id="limit=0"),
        pytest.param("limit=101", id="limit=101"),
        pytest.param("offset=-1", id="offset=-1"),
        pytest.param("ticket_id=0", id="ticket_id=0"),
    ],
)
def test_list_pending_suggestions_invalid_query_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
    query_string: str,
) -> None:
    """Invalid query parameters return 422."""
    response = client.get(
        f"/api/reviews/pending-suggestions?{query_string}",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_viewer_can_list_pending_suggestions_but_cannot_review(
    client: TestClient,
    viewer_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Viewer can view pending queue but gets 403 on review actions."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_suggestion(db, ticket_id=ticket["id"])

    # Viewer can list pending suggestions
    list_resp = client.get(
        "/api/reviews/pending-suggestions",
        headers=viewer_headers,
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert any(item["id"] == suggestion.id for item in data["items"])

    # Viewer cannot approve
    approve_resp = client.post(
        f"/api/reviews/{suggestion.id}/approve",
        json={},
        headers=viewer_headers,
    )
    assert approve_resp.status_code == 403


def test_viewer_rejected_by_rbac_does_not_change_suggestion_status(
    client: TestClient,
    viewer_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """RBAC 403 rejection should not modify the suggestion's status."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = _inject_suggestion(db, ticket_id=ticket["id"])
        suggestion_id = suggestion.id

    response = client.post(
        f"/api/reviews/{suggestion_id}/approve",
        json={},
        headers=viewer_headers,
    )
    assert response.status_code == 403

    # Re-read from DB to confirm no side effects
    with next(get_db()) as db:
        refreshed = db.get(AISuggestion, suggestion_id)
    assert refreshed is not None
    assert refreshed.status == "draft"
    assert refreshed.reviewed_by is None
    assert refreshed.reviewed_at is None


# ---------------------------------------------------------------------------
# Step 6 — 审核后追加 ticket message 测试
# ---------------------------------------------------------------------------


def list_ticket_messages(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
) -> list[dict]:
    response = client.get(
        f"/api/tickets/{ticket_id}/messages",
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def create_draft_reply_suggestion(
    db: Session,
    *,
    ticket_id: int,
    suggested_content: str = "Suggested reply for review RBAC test.",
) -> AISuggestion:
    suggestion = AISuggestion(
        ticket_id=ticket_id,
        suggestion_type="reply",
        suggested_content=suggested_content,
        reasoning_summary="Created by test.",
        sources_json=[],
        confidence=0.8,
        status="draft",
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


def test_approve_suggestion_appends_ticket_message(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Approve without custom content -> message content uses suggested_content."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_draft_reply_suggestion(
            db, ticket_id=ticket["id"], suggested_content="AI approved response."
        )
        suggestion_id = suggestion.id

    before = list_ticket_messages(client, ticket["id"], agent_headers)

    response = client.post(
        f"/api/reviews/{suggestion_id}/approve",
        json={},
        headers=agent_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["final_content"] == "AI approved response."

    after = list_ticket_messages(client, ticket["id"], agent_headers)
    assert len(after) == len(before) + 1

    assert any(
        m["sender_type"] == "agent" and m["content"] == "AI approved response."
        for m in after
    )


def test_approve_suggestion_with_custom_content_appends_custom_message(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Approve with custom final_content -> message content uses final_content."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_draft_reply_suggestion(
            db, ticket_id=ticket["id"], suggested_content="Original AI response."
        )
        suggestion_id = suggestion.id

    before = list_ticket_messages(client, ticket["id"], agent_headers)

    response = client.post(
        f"/api/reviews/{suggestion_id}/approve",
        json={"final_content": "Custom approved response."},
        headers=agent_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["final_content"] == "Custom approved response."

    after = list_ticket_messages(client, ticket["id"], agent_headers)
    assert len(after) == len(before) + 1

    assert any(
        m["content"] == "Custom approved response."
        for m in after
    )
    # original suggested_content should NOT appear as a separate message
    assert not any(
        m["content"] == "Original AI response."
        for m in after[len(before):]
    )


def test_edit_suggestion_appends_ticket_message_with_final_content(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Edit with final_content -> message content uses the edited content."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_draft_reply_suggestion(
            db, ticket_id=ticket["id"], suggested_content="Original AI response."
        )
        suggestion_id = suggestion.id

    before = list_ticket_messages(client, ticket["id"], agent_headers)

    response = client.post(
        f"/api/reviews/{suggestion_id}/edit",
        json={"final_content": "Edited human response."},
        headers=agent_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "edited"
    assert data["final_content"] == "Edited human response."

    after = list_ticket_messages(client, ticket["id"], agent_headers)
    assert len(after) == len(before) + 1

    assert any(
        m["sender_type"] == "agent" and m["content"] == "Edited human response."
        for m in after
    )


def test_reject_suggestion_does_not_append_ticket_message(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Reject should NOT create a ticket message."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_draft_reply_suggestion(
            db, ticket_id=ticket["id"], suggested_content="Rejected AI response."
        )
        suggestion_id = suggestion.id

    before = list_ticket_messages(client, ticket["id"], agent_headers)

    response = client.post(
        f"/api/reviews/{suggestion_id}/reject",
        json={"reject_reason": "Not suitable for customer."},
        headers=agent_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "rejected"

    after = list_ticket_messages(client, ticket["id"], agent_headers)
    assert len(after) == len(before)

    assert not any(
        m["content"] == "Rejected AI response." for m in after
    )


def test_reviewed_suggestion_cannot_append_duplicate_message(
    client: TestClient,
    agent_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Re-reviewing an already-approved suggestion fails and does not duplicate the message."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_draft_reply_suggestion(
            db,
            ticket_id=ticket["id"],
            suggested_content="Only one message should be created.",
        )
        suggestion_id = suggestion.id

    # First review succeeds
    first = client.post(
        f"/api/reviews/{suggestion_id}/approve",
        json={},
        headers=agent_headers,
    )
    assert first.status_code == 200

    after_first = list_ticket_messages(client, ticket["id"], agent_headers)

    # Second review of same suggestion should fail
    second = client.post(
        f"/api/reviews/{suggestion_id}/approve",
        json={},
        headers=agent_headers,
    )
    assert second.status_code == 400
    assert "already been reviewed" in second.json()["detail"]

    after_second = list_ticket_messages(client, ticket["id"], agent_headers)
    assert len(after_second) == len(after_first)

    # The message content should appear exactly once
    matching = [
        m for m in after_second
        if m["content"] == "Only one message should be created."
    ]
    assert len(matching) == 1


def test_viewer_cannot_append_ticket_message_by_reviewing(
    client: TestClient,
    viewer_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Viewer gets 403 and no ticket message is created."""
    ticket = create_ticket()
    with next(get_db()) as db:
        suggestion = create_draft_reply_suggestion(
            db, ticket_id=ticket["id"], suggested_content="Viewer should not create message."
        )
        suggestion_id = suggestion.id

    before = list_ticket_messages(client, ticket["id"], viewer_headers)

    response = client.post(
        f"/api/reviews/{suggestion_id}/approve",
        json={},
        headers=viewer_headers,
    )
    assert response.status_code == 403

    after = list_ticket_messages(client, ticket["id"], viewer_headers)
    assert len(after) == len(before)

    with next(get_db()) as db:
        refreshed = db.get(AISuggestion, suggestion_id)
    assert refreshed is not None
    assert refreshed.status == "draft"
