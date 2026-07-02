from collections.abc import Callable

from fastapi.testclient import TestClient


def test_ticket_crud_and_message_flow(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    create_response = client.post(
        "/api/tickets",
        json={
            "title": "Invoice correction needed",
            "content": "The customer needs the company tax number updated on the invoice.",
            "customer_name": "Bob",
            "customer_email": "bob@example.com",
            "category": "invoice",
            "priority": "medium",
            "source": "manual",
        },
        headers=auth_headers,
    )

    assert create_response.status_code == 200
    created_ticket = create_response.json()
    ticket_id = created_ticket["id"]
    assert created_ticket["status"] == "open"
    assert created_ticket["title"] == "Invoice correction needed"

    list_response = client.get("/api/tickets", headers=auth_headers)
    assert list_response.status_code == 200
    assert any(ticket["id"] == ticket_id for ticket in list_response.json())

    detail_response = client.get(f"/api/tickets/{ticket_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["customer_email"] == "bob@example.com"

    update_response = client.patch(
        f"/api/tickets/{ticket_id}",
        json={
            "priority": "high",
            "status": "in_progress",
        },
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["priority"] == "high"
    assert update_response.json()["status"] == "in_progress"

    message_response = client.post(
        f"/api/tickets/{ticket_id}/messages",
        json={
            "sender_type": "agent",
            "content": "We are validating the invoice details before updating the record.",
        },
        headers=auth_headers,
    )
    assert message_response.status_code == 200
    assert message_response.json()["sender_name"] == "admin"

    messages_response = client.get(
        f"/api/tickets/{ticket_id}/messages",
        headers=auth_headers,
    )
    assert messages_response.status_code == 200
    messages = messages_response.json()
    assert len(messages) == 1
    assert messages[0]["content"].startswith("We are validating")


# ---------------------------------------------------------------------------
# Filter tests: status / priority / category Query 参数过滤
# ---------------------------------------------------------------------------


def test_list_tickets_filter_by_status(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets?status=open only returns open tickets."""
    open_ticket = create_ticket(title="Open ticket", category="payment", priority="low")
    resolved_ticket = create_ticket(
        title="Resolved ticket", category="payment", priority="low"
    )
    client.patch(
        f"/api/tickets/{resolved_ticket['id']}",
        json={"status": "resolved"},
        headers=auth_headers,
    )

    response = client.get("/api/tickets?status=open", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert any(item["id"] == open_ticket["id"] for item in items)
    assert not any(item["id"] == resolved_ticket["id"] for item in items)
    assert all(item["status"] == "open" for item in items)


def test_list_tickets_filter_by_priority(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets?priority=urgent only returns urgent tickets."""
    urgent_ticket = create_ticket(
        title="Urgent issue", priority="urgent", category="technical"
    )
    medium_ticket = create_ticket(
        title="Medium issue", priority="medium", category="technical"
    )

    response = client.get("/api/tickets?priority=urgent", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert any(item["id"] == urgent_ticket["id"] for item in items)
    assert not any(item["id"] == medium_ticket["id"] for item in items)
    assert all(item["priority"] == "urgent" for item in items)


def test_list_tickets_filter_by_category(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets?category=payment only returns payment tickets."""
    payment_ticket = create_ticket(
        title="Payment ticket", category="payment", priority="medium"
    )
    refund_ticket = create_ticket(
        title="Refund ticket", category="refund", priority="medium"
    )

    response = client.get("/api/tickets?category=payment", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert any(item["id"] == payment_ticket["id"] for item in items)
    assert not any(item["id"] == refund_ticket["id"] for item in items)
    assert all(item["category"] == "payment" for item in items)


def test_list_tickets_filter_combined(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets?status=open&priority=urgent&category=payment combo."""
    match_ticket = create_ticket(
        title="Match", category="payment", priority="urgent"
    )
    wrong_priority = create_ticket(
        title="Wrong priority", category="payment", priority="low"
    )
    wrong_category = create_ticket(
        title="Wrong category", category="refund", priority="urgent"
    )
    wrong_status = create_ticket(
        title="Wrong status", category="payment", priority="urgent"
    )
    client.patch(
        f"/api/tickets/{wrong_status['id']}",
        json={"status": "in_progress"},
        headers=auth_headers,
    )

    response = client.get(
        "/api/tickets?status=open&priority=urgent&category=payment",
        headers=auth_headers,
    )
    assert response.status_code == 200
    items = response.json()
    assert any(item["id"] == match_ticket["id"] for item in items)
    assert not any(
        item["id"] in {wrong_priority["id"], wrong_category["id"], wrong_status["id"]}
        for item in items
    )
    assert all(
        item["status"] == "open"
        and item["priority"] == "urgent"
        and item["category"] == "payment"
        for item in items
    )


def test_list_tickets_filter_invalid_status_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """GET /api/tickets?status=invalid_status returns 422."""
    response = client.get(
        "/api/tickets?status=invalid_status", headers=auth_headers
    )
    assert response.status_code == 422


def test_list_tickets_no_filter_returns_all(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets with no params returns tickets normally."""
    ticket_a = create_ticket(title="Ticket A")
    ticket_b = create_ticket(title="Ticket B")

    response = client.get("/api/tickets", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert any(item["id"] == ticket_a["id"] for item in items)
    assert any(item["id"] == ticket_b["id"] for item in items)


# ---------------------------------------------------------------------------
# Pagination tests: /api/tickets/page
# ---------------------------------------------------------------------------


def test_list_tickets_page_returns_items_total_limit_offset(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets/page?limit=2&offset=0 returns correct pagination structure."""
    create_ticket(title="Ticket 1")
    create_ticket(title="Ticket 2")
    create_ticket(title="Ticket 3")

    response = client.get(
        "/api/tickets/page?limit=2&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"items", "total", "limit", "offset"}
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2


def test_list_tickets_page_respects_limit(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets/page?limit=1 returns exactly 1 item, total unaffected."""
    create_ticket(title="A")
    create_ticket(title="B")

    response = client.get(
        "/api/tickets/page?limit=1&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 2


def test_list_tickets_page_respects_offset(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """GET /api/tickets/page with different offsets returns different items."""
    create_ticket(title="First")
    create_ticket(title="Second")
    create_ticket(title="Third")

    response_0 = client.get(
        "/api/tickets/page?limit=1&offset=0",
        headers=auth_headers,
    )
    response_1 = client.get(
        "/api/tickets/page?limit=1&offset=1",
        headers=auth_headers,
    )
    assert response_0.status_code == 200
    assert response_1.status_code == 200
    assert response_0.json()["items"][0]["id"] != response_1.json()["items"][0]["id"]


def test_list_tickets_page_combines_filters_and_pagination(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Filters + pagination combo: total reflects filter, items respect limit."""
    for i in range(3):
        create_ticket(
            title=f"Payment issue {i}",
            category="payment",
            priority="urgent",
        )
    create_ticket(
        title="Invoice question",
        category="invoice",
        priority="medium",
    )

    response = client.get(
        "/api/tickets/page?status=open&category=payment&priority=urgent&limit=2&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["status"] == "open"
        assert item["category"] == "payment"
        assert item["priority"] == "urgent"


def test_list_tickets_page_offset_beyond_total_returns_empty_items(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Offset beyond total returns empty items but total remains correct."""
    create_ticket(title="Only ticket")

    response = client.get(
        "/api/tickets/page?limit=20&offset=999",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 999


def test_list_tickets_page_invalid_limit_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """limit=0 returns 422 (ge=1)."""
    response = client.get(
        "/api/tickets/page?limit=0&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_tickets_page_invalid_limit_too_large_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """limit=101 returns 422 (le=100)."""
    response = client.get(
        "/api/tickets/page?limit=101&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_tickets_page_invalid_offset_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """offset=-1 returns 422 (ge=0)."""
    response = client.get(
        "/api/tickets/page?limit=20&offset=-1",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_tickets_page_invalid_filter_returns_422(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    """Invalid filter param returns 422."""
    response = client.get(
        "/api/tickets/page?status=invalid_status&limit=20&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_list_tickets_legacy_endpoint_still_returns_list(
    client: TestClient,
    auth_headers: dict[str, str],
    create_ticket: Callable[..., dict],
) -> None:
    """Old GET /api/tickets still returns a plain list, not a page object."""
    create_ticket(title="Legacy test")

    response = client.get("/api/tickets", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "items" not in (data if isinstance(data, dict) else {})
