from collections.abc import Callable

from fastapi.testclient import TestClient


def test_list_audit_logs_requires_auth(
    client: TestClient,
) -> None:
    """GET /api/audit-logs without auth returns 401."""
    response = client.get("/api/audit-logs")
    assert response.status_code == 401


def test_list_audit_logs_returns_create_ticket_logs(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Creating a ticket produces a create_ticket audit log."""
    ticket = create_ticket(title="Audit test ticket")

    response = client.get("/api/audit-logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"items", "total", "limit", "offset"}
    assert any(
        item["action"] == "create_ticket"
        and item["target_type"] == "ticket"
        and item["target_id"] == ticket["id"]
        for item in data["items"]
    )


def test_list_audit_logs_filters_by_action(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/audit-logs?action=update_ticket returns only update_ticket logs."""
    ticket = create_ticket(title="Filter by action test")
    client.patch(
        f"/api/tickets/{ticket['id']}",
        json={"priority": "high"},
        headers=auth_headers,
    )

    response = client.get(
        "/api/audit-logs?action=update_ticket",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["action"] == "update_ticket" for item in data["items"])


def test_list_audit_logs_filters_by_target_type_and_target_id(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Filter by target_type=ticket and specific target_id."""
    ticket_a = create_ticket(title="Ticket A")
    ticket_b = create_ticket(title="Ticket B")

    response = client.get(
        f"/api/audit-logs?target_type=ticket&target_id={ticket_a['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["target_type"] == "ticket" for item in data["items"])
    assert all(item["target_id"] == ticket_a["id"] for item in data["items"])
    assert not any(item["target_id"] == ticket_b["id"] for item in data["items"])


def test_list_audit_logs_filters_by_user_id(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Filter by user_id returns logs from that user."""
    create_ticket(title="User filter test")

    response = client.get("/api/audit-logs", headers=auth_headers)
    assert response.status_code == 200
    all_items = response.json()["items"]
    # pick the first log with a non-null user_id
    sample_user_id = None
    for item in all_items:
        if item["user_id"] is not None:
            sample_user_id = item["user_id"]
            break
    assert sample_user_id is not None, "No audit log with user_id available"

    response = client.get(
        f"/api/audit-logs?user_id={sample_user_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(item["user_id"] == sample_user_id for item in data["items"])


def test_list_audit_logs_paginates_results(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Pagination: limit returns at most that many items, total is unaffected."""
    for i in range(3):
        create_ticket(title=f"Paginate test {i}")

    response = client.get(
        "/api/audit-logs?limit=2&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2


def test_list_audit_logs_respects_offset(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Different offsets return different audit log items."""
    for i in range(3):
        create_ticket(title=f"Offset test {i}")

    r0 = client.get(
        "/api/audit-logs?limit=1&offset=0",
        headers=auth_headers,
    )
    r1 = client.get(
        "/api/audit-logs?limit=1&offset=1",
        headers=auth_headers,
    )
    assert r0.status_code == 200
    assert r1.status_code == 200
    items0 = r0.json()["items"]
    items1 = r1.json()["items"]
    if items0 and items1:
        assert items0[0]["id"] != items1[0]["id"]


def test_list_audit_logs_offset_beyond_total_returns_empty_items(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Offset beyond total returns empty items but total remains correct."""
    create_ticket(title="Beyond offset test")

    response = client.get(
        "/api/audit-logs?limit=50&offset=999",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] >= 1
    assert data["limit"] == 50
    assert data["offset"] == 999


def test_list_audit_logs_invalid_limit_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """limit=0 and limit=101 both return 422."""
    r0 = client.get(
        "/api/audit-logs?limit=0&offset=0",
        headers=auth_headers,
    )
    assert r0.status_code == 422

    r1 = client.get(
        "/api/audit-logs?limit=101&offset=0",
        headers=auth_headers,
    )
    assert r1.status_code == 422


def test_list_audit_logs_invalid_offset_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """offset=-1 returns 422 (ge=0)."""
    response = client.get(
        "/api/audit-logs?limit=50&offset=-1",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_audit_logs_invalid_id_filters_return_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """target_id=0 and user_id=0 both return 422 (ge=1)."""
    r0 = client.get(
        "/api/audit-logs?target_id=0",
        headers=auth_headers,
    )
    assert r0.status_code == 422

    r1 = client.get(
        "/api/audit-logs?user_id=0",
        headers=auth_headers,
    )
    assert r1.status_code == 422
