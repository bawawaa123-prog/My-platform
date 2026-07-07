"""
Centralised constants for AI suggestion / agent-run source workflows.

Every module that creates or queries AISuggestion / AgentRunLog rows should
import from here instead of hard-coding string literals.
"""

# --- source_workflow values stored on AISuggestion ---------------------------
SINGLE_AGENT_RAG = "single_agent_rag"
SINGLE_AGENT_WORKFLOW = "single_agent_workflow"
MULTI_AGENT = "multi_agent"
MANUAL = "manual"

VALID_SOURCE_WORKFLOWS = frozenset({
    SINGLE_AGENT_RAG,
    SINGLE_AGENT_WORKFLOW,
    MULTI_AGENT,
    MANUAL,
})

# --- run_type values stored on AgentRunLog ----------------------------------
# They mirror source_workflow values so the two tables can be joined by
# source_run_id ↔ run_id.
RUN_TYPE_SINGLE_AGENT_RAG = "single_agent_rag"
RUN_TYPE_SINGLE_AGENT_WORKFLOW = "single_agent_workflow"
RUN_TYPE_MULTI_AGENT = "multi_agent"

# Legacy alias — older rows may still carry run_type="workflow".
# Frontend should display these as "Single-Agent Workflow (Legacy)".
RUN_TYPE_WORKFLOW_LEGACY = "workflow"


def normalize_source_workflow(value: str | None) -> str:
    """Return a canonical source_workflow, mapping legacy values forward."""
    if not value or value == "single_agent":
        return SINGLE_AGENT_RAG
    if value == "workflow":
        return SINGLE_AGENT_WORKFLOW
    return value
