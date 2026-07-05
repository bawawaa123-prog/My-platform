from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.db.base import utc_now
from app.utils.datetime_utils import UTCDatetime, ensure_utc


def test_utc_now_returns_aware_datetime() -> None:
    """utc_now() should return a timezone-aware UTC datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert str(now.tzinfo) == "UTC"


def test_ensure_utc_preserves_aware_datetime() -> None:
    """Aware datetimes should keep their timezone."""
    dt = datetime(2026, 7, 4, 12, 30, 0, tzinfo=timezone.utc)
    result = ensure_utc(dt)
    assert result == dt
    assert result.tzinfo is not None


def test_ensure_utc_adds_utc_to_naive() -> None:
    """Naive datetimes should get UTC timezone assigned."""
    dt = datetime(2026, 7, 4, 12, 30, 0)
    result = ensure_utc(dt)
    assert result.tzinfo is not None
    assert str(result.tzinfo) == "UTC"
    assert result.hour == 12  # value unchanged, only timezone added


def test_ensure_utc_handles_none() -> None:
    """None should pass through."""
    assert ensure_utc(None) is None


def test_utcdatetime_serializes_with_timezone(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Create a ticket and verify created_at includes UTC timezone offset."""
    response = client.post(
        "/api/tickets",
        json={
            "title": "Timezone test ticket",
            "content": "Testing timezone serialization.",
            "customer_name": "Test",
            "customer_email": "test@example.com",
            "category": "other",
            "priority": "medium",
            "source": "manual",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    created_at = data["created_at"]
    # Must include UTC timezone indicator
    assert created_at.endswith("+00:00") or created_at.endswith("Z") or "+00:00" in created_at, (
        f"created_at '{created_at}' missing UTC timezone"
    )


def test_ticket_list_returns_utc_datetimes(client: TestClient, auth_headers: dict[str, str]) -> None:
    """List tickets and verify all datetime fields have timezone info."""
    # Create a ticket first
    client.post(
        "/api/tickets",
        json={
            "title": "List timezone test",
            "content": "Testing list endpoint.",
            "customer_name": "Test",
            "customer_email": "test@example.com",
            "category": "other",
            "priority": "medium",
            "source": "manual",
        },
        headers=auth_headers,
    )
    response = client.get("/api/tickets/page", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0, "expected at least one ticket in page"
    ticket = data["items"][0]
    for field in ("created_at", "updated_at"):
        value = ticket.get(field)
        assert value is not None, f"{field} should not be None"
        assert value.endswith("+00:00") or value.endswith("Z") or "+00:00" in value, (
            f"ticket.{field} '{value}' missing UTC timezone"
        )


def test_suggestion_timestamps_all_utc(client: TestClient, auth_headers: dict[str, str]) -> None:
    """Generate an AI reply, approve it, and verify all three datetime fields have UTC timezone."""
    # 1. Create ticket
    resp = client.post(
        "/api/tickets",
        json={
            "title": "Suggestion TZ test",
            "content": "Testing all suggestion timestamps.",
            "customer_name": "Tester",
            "customer_email": "tester@test.com",
            "category": "other",
            "priority": "medium",
            "source": "manual",
        },
        headers=auth_headers,
    )
    ticket_id = resp.json()["id"]

    # 2. Generate AI reply
    resp = client.post(f"/api/ai/tickets/{ticket_id}/generate-reply", headers=auth_headers)
    assert resp.status_code == 200
    sug = resp.json()

    # created_at and updated_at must have UTC timezone
    for field in ("created_at", "updated_at"):
        val = sug[field]
        assert val is not None, f"suggestion.{field} should not be None"
        has_tz = val.endswith("+00:00") or val.endswith("Z") or "+00:00" in val
        assert has_tz, f"suggestion.{field} '{val}' missing UTC timezone"

    # reviewed_at is None before approve
    assert sug["reviewed_at"] is None, "reviewed_at should be None before approve"

    # 3. Approve the suggestion
    resp = client.post(
        f"/api/reviews/{sug['id']}/approve",
        json={"final_content": "Approved content for timezone test."},
        headers=auth_headers,
    )
    assert resp.status_code == 200, f"Approve failed: {resp.json()}"
    reviewed = resp.json()

    # 4. All three fields must have UTC timezone
    for field in ("created_at", "updated_at", "reviewed_at"):
        val = reviewed.get(field)
        assert val is not None, f"reviewed.{field} should not be None"
        has_tz = val.endswith("+00:00") or val.endswith("Z") or "+00:00" in val
        assert has_tz, f"reviewed.{field} '{val}' missing UTC timezone"

    # 5. Verify updated_at >= created_at (updated_at was updated on approve)
    assert reviewed["updated_at"] >= reviewed["created_at"], (
        f"updated_at ({reviewed['updated_at']}) should be >= created_at ({reviewed['created_at']})"
    )

    # 6. Verify reviewed_at >= created_at (reviewed_at is the latest event)
    assert reviewed["reviewed_at"] >= reviewed["created_at"], (
        f"reviewed_at ({reviewed['reviewed_at']}) should be >= created_at ({reviewed['created_at']})"
    )

    # 7. Verify all three timestamps are within the same reasonable time window (within 5 seconds)
    from datetime import datetime, timezone
    for field in ("created_at", "updated_at", "reviewed_at"):
        ts = datetime.fromisoformat(reviewed[field].replace("Z", "+00:00"))
        assert ts.tzinfo is not None, f"Parsed {field} lost timezone"


def test_suggestion_list_returns_utc_timestamps(client: TestClient, auth_headers: dict[str, str]) -> None:
    """List suggestions for a ticket and verify all have UTC timezone info."""
    # Create ticket
    resp = client.post(
        "/api/tickets",
        json={
            "title": "List Suggestion TZ test",
            "content": "Testing list suggestion timestamps.",
            "customer_name": "ListTest",
            "customer_email": "listtest@test.com",
            "category": "other",
            "priority": "medium",
            "source": "manual",
        },
        headers=auth_headers,
    )
    ticket_id = resp.json()["id"]

    # Generate reply
    client.post(f"/api/ai/tickets/{ticket_id}/generate-reply", headers=auth_headers)

    # List suggestions
    resp = client.get(f"/api/ai/tickets/{ticket_id}/suggestions", headers=auth_headers)
    assert resp.status_code == 200
    suggestions = resp.json()
    assert len(suggestions) > 0

    for sug in suggestions:
        for field in ("created_at", "updated_at"):
            val = sug.get(field)
            assert val is not None, f"suggestion.{field} should not be None"
            has_tz = val.endswith("+00:00") or val.endswith("Z") or "+00:00" in val
            assert has_tz, f"suggestion.{field} '{val}' missing UTC timezone"
