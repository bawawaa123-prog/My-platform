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
