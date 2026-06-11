from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def register_prompts(mcp: FastMCP) -> None:
    @mcp.prompt(
        name="classify_ticket_prompt",
        description="Build a reusable ticket-classification instruction for enterprise support triage.",
        tags={"ticket", "classification", "triage"},
    )
    def classify_ticket_prompt(
        title: str,
        content: str,
        customer_name: str,
        customer_email: str,
        category: str = "other",
        priority: str = "medium",
    ) -> str:
        """Create the LLM prompt used for structured ticket classification."""
        return _load_prompt_template("classify_ticket.txt").format(
            title=title,
            content=content,
            customer_name=customer_name,
            customer_email=customer_email,
            category=category,
            priority=priority,
        )

    @mcp.prompt(
        name="generate_reply_prompt",
        description="Build a reusable customer-reply drafting instruction with RAG context.",
        tags={"ticket", "reply", "rag"},
    )
    def generate_reply_prompt(
        title: str,
        content: str,
        customer_name: str,
        customer_email: str,
        category: str = "other",
        priority: str = "medium",
        sentiment: str = "neutral",
        ai_summary: str = "",
        recommended_department: str = "",
        confidence: float = 0.15,
        low_confidence_reason: str = "None",
        sources_block: str = "No sources found.",
        supplemental_context: str = "None",
    ) -> str:
        """Create the LLM prompt used for RAG reply-draft generation."""
        return _load_prompt_template("generate_reply.txt").format(
            title=title,
            content=content,
            customer_name=customer_name,
            customer_email=customer_email,
            category=category,
            priority=priority,
            sentiment=sentiment,
            ai_summary=ai_summary,
            recommended_department=recommended_department,
            confidence=confidence,
            low_confidence_reason=low_confidence_reason,
            sources_block=sources_block,
            supplemental_context=supplemental_context,
        )

    @mcp.prompt(
        name="summarize_ticket_prompt",
        description="Build a reusable prompt for summarizing a support ticket for internal handoff.",
        tags={"ticket", "summary", "handoff"},
    )
    def summarize_ticket_prompt(
        title: str,
        content: str,
        customer_name: str,
        customer_email: str,
        target_audience: str = "support_agent",
    ) -> str:
        """Create a reusable ticket-summary instruction."""
        return _load_prompt_template("summarize_ticket.txt").format(
            title=title,
            content=content,
            customer_name=customer_name,
            customer_email=customer_email,
            target_audience=target_audience,
        )

    @mcp.prompt(
        name="risk_review_prompt",
        description="Build a reusable prompt for reviewing support-ticket risk before customer reply approval.",
        tags={"ticket", "risk", "review"},
    )
    def risk_review_prompt(
        title: str,
        content: str,
        category: str = "other",
        priority: str = "medium",
        draft_reply: str = "",
        knowledge_confidence: float = 0.15,
        knowledge_sources: str = "No sources found.",
    ) -> str:
        """Create a reusable risk-review instruction for support workflows."""
        return _load_prompt_template("risk_review.txt").format(
            title=title,
            content=content,
            category=category,
            priority=priority,
            draft_reply=draft_reply,
            knowledge_confidence=knowledge_confidence,
            knowledge_sources=knowledge_sources,
        )


def _load_prompt_template(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text(encoding="utf-8")
