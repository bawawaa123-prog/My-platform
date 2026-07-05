"""Quick end-to-end verification: run single-agent workflow with review,
then check that AgentRunLog entries with run_type='workflow' are created."""

import pytest
from fastapi.testclient import TestClient


def start_single_agent_workflow(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
) -> dict:
    """Start the single-agent workflow with interrupt."""
    response = client.post(
        f"/api/ai/tickets/{ticket_id}/process/start",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def resume_single_agent_workflow(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
    payload: dict,
) -> dict:
    """Resume the single-agent workflow."""
    response = client.post(
        f"/api/ai/tickets/{ticket_id}/process/resume",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def list_agent_runs_page(
    client: TestClient,
    ticket_id: int,
    headers: dict[str, str],
    params: dict | None = None,
) -> dict:
    """List agent runs with page endpoint."""
    response = client.get(
        f"/api/ai/tickets/{ticket_id}/agent-runs/page",
        params=params or {},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


class TestSingleAgentWorkflowRunLog:
    """Verify that single-agent workflow creates & updates AgentRunLog entries."""

    def test_single_agent_start_creates_interrupted_run_log(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        create_ticket,
    ) -> None:
        """After workflow start, an AgentRunLog with run_type='workflow', status='interrupted' should exist."""
        ticket = create_ticket(
            title="Verify single-agent run log",
            content="Test that AgentRunLog is created for single-agent workflow.",
        )

        pending = start_single_agent_workflow(client, ticket["id"], auth_headers)
        workflow_id = pending["run_id"]
        assert workflow_id

        # Check agent-runs page filtered by run_type='workflow'
        page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "workflow", "limit": 20, "offset": 0},
        )
        assert page["total"] >= 1, "Expected at least 1 workflow run log entry"

        matched = next((r for r in page["items"] if r["run_id"] == workflow_id), None)
        assert matched is not None, f"Workflow run_id={workflow_id} not found in agent runs"
        assert matched["run_type"] == "workflow"
        assert matched["status"] == "interrupted"
        assert matched["ticket_id"] == ticket["id"]

    def test_single_agent_approve_updates_to_completed(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        create_ticket,
    ) -> None:
        """After workflow resume with approve, the AgentRunLog should be updated to completed."""
        ticket = create_ticket(
            title="Verify single-agent resume creates completed run log",
            content="Approve test for single-agent workflow.",
        )

        pending = start_single_agent_workflow(client, ticket["id"], auth_headers)
        workflow_id = pending["run_id"]

        resume_single_agent_workflow(
            client, ticket["id"], auth_headers,
            {"action": "approve", "run_id": workflow_id},
        )

        page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "workflow", "limit": 20, "offset": 0},
        )
        matched = next((r for r in page["items"] if r["run_id"] == workflow_id), None)
        assert matched is not None
        assert matched["run_type"] == "workflow"
        assert matched["status"] == "completed"
        assert matched["output_json"]["reviewed_suggestion"]["status"] == "approved"

    def test_single_agent_edit_updates_to_completed(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        create_ticket,
    ) -> None:
        """After workflow resume with edit, the AgentRunLog should be updated to completed."""
        ticket = create_ticket(
            title="Verify single-agent edit creates completed run log",
            content="Edit test for single-agent workflow.",
        )

        pending = start_single_agent_workflow(client, ticket["id"], auth_headers)
        workflow_id = pending["run_id"]

        resume_single_agent_workflow(
            client, ticket["id"], auth_headers,
            {"action": "edit", "run_id": workflow_id, "final_content": "Edited content for test."},
        )

        page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "workflow", "limit": 20, "offset": 0},
        )
        matched = next((r for r in page["items"] if r["run_id"] == workflow_id), None)
        assert matched is not None
        assert matched["run_type"] == "workflow"
        assert matched["status"] == "completed"

    def test_single_agent_reject_updates_to_completed(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        create_ticket,
    ) -> None:
        """After workflow resume with reject, the AgentRunLog should be updated to completed."""
        ticket = create_ticket(
            title="Verify single-agent reject creates completed run log",
            content="Reject test for single-agent workflow.",
        )

        pending = start_single_agent_workflow(client, ticket["id"], auth_headers)
        workflow_id = pending["run_id"]

        resume_single_agent_workflow(
            client, ticket["id"], auth_headers,
            {"action": "reject", "run_id": workflow_id, "reject_reason": "Test rejection."},
        )

        page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "workflow", "limit": 20, "offset": 0},
        )
        matched = next((r for r in page["items"] if r["run_id"] == workflow_id), None)
        assert matched is not None
        assert matched["run_type"] == "workflow"
        assert matched["status"] == "completed"

    def test_workflow_filter_shows_only_workflow_runs(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        create_ticket,
    ) -> None:
        """Verify that filtering by run_type='workflow' excludes multi_agent runs."""
        ticket = create_ticket(
            title="Verify workflow filter isolation",
            content="This ticket should have both workflow and multi_agent runs.",
        )

        # Run single-agent workflow
        pending = start_single_agent_workflow(client, ticket["id"], auth_headers)
        resume_single_agent_workflow(
            client, ticket["id"], auth_headers,
            {"action": "approve", "run_id": pending["run_id"]},
        )

        # Run multi-agent workflow too
        multi_response = client.post(
            f"/api/ai/tickets/{ticket['id']}/multi-agent-process/start",
            headers=auth_headers,
        )
        assert multi_response.status_code == 200
        multi_run_id = multi_response.json()["run_id"]
        resume_response = client.post(
            f"/api/ai/tickets/{ticket['id']}/multi-agent-process/resume",
            json={"action": "approve", "run_id": multi_run_id},
            headers=auth_headers,
        )
        assert resume_response.status_code == 200

        # Filter by workflow only
        workflow_page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "workflow", "limit": 20, "offset": 0},
        )
        for item in workflow_page["items"]:
            assert item["run_type"] == "workflow", f"Expected run_type='workflow', got '{item['run_type']}'"
        assert workflow_page["total"] >= 1

        # Filter by multi_agent only
        multi_page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "multi_agent", "limit": 20, "offset": 0},
        )
        for item in multi_page["items"]:
            assert item["run_type"] == "multi_agent", f"Expected run_type='multi_agent', got '{item['run_type']}'"
        assert multi_page["total"] >= 1

        # All filter shows both
        all_page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"limit": 20, "offset": 0},
        )
        assert all_page["total"] >= workflow_page["total"] + multi_page["total"]


class TestGenerateReplyRunLog:
    """Verify that the generate-reply endpoint creates AgentRunLog entries."""

    def test_generate_reply_creates_workflow_run_log(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        create_ticket,
    ) -> None:
        """After generate-reply, an AgentRunLog with run_type='workflow', status='completed' should exist."""
        ticket = create_ticket(
            title="Verify generate-reply run log",
            content="Test that generate-reply creates AgentRunLog.",
        )

        # Call generate-reply (the frontend Single-Agent flow)
        response = client.post(
            f"/api/ai/tickets/{ticket['id']}/generate-reply",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        suggestion = response.json()

        # Check agent-runs page filtered by run_type='workflow'
        page = list_agent_runs_page(
            client, ticket["id"], auth_headers,
            {"run_type": "workflow", "limit": 20, "offset": 0},
        )
        assert page["total"] >= 1, "Expected at least 1 workflow run log entry from generate-reply"

        # Verify the most recent workflow run has the correct data
        matched = page["items"][0]
        assert matched["run_type"] == "workflow"
        assert matched["status"] == "completed"
        assert matched["ticket_id"] == ticket["id"]
        assert matched["output_json"]["suggestion_id"] == suggestion["id"]
        assert matched["output_json"]["suggested_content"] == suggestion["suggested_content"]
