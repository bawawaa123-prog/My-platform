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
