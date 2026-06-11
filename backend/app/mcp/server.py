from __future__ import annotations

from fastmcp import FastMCP

from app.db.session import SessionLocal
from app.mcp.prompts import register_prompts
from app.mcp.resources import register_resources
from app.schemas.knowledge import KnowledgeSearchResult
from app.schemas.ticket import SimilarTicketRead, TicketRead
from app.services.analytics_service import AnalyticsService
from app.services.knowledge_service import KnowledgeService
from app.services.mcp_agent_service import MCPAgentService
from app.services.ticket_service import TicketService
from app.services.ticket_similarity_service import TicketSimilarityService


mcp = FastMCP(name="Enterprise Support Agent MCP")

register_resources(mcp)
register_prompts(mcp)


@mcp.tool
def search_knowledge_base(query: str, top_k: int = 5) -> list[dict]:
    """Search the enterprise knowledge base for relevant text chunks.

    Args:
        query: Natural-language search query for SOPs, FAQs, or internal guides.
        top_k: Maximum number of matching chunks to return.
    """
    db = SessionLocal()
    try:
        results = KnowledgeService(db).search_knowledge(query=query, top_k=top_k)
        return [KnowledgeSearchResult.model_validate(result).model_dump(mode="json") for result in results]
    finally:
        db.close()


@mcp.tool
def get_ticket_detail(ticket_id: int) -> dict:
    """Get the full detail of a single support ticket by ID.

    Args:
        ticket_id: Unique numeric ticket identifier.
    """
    db = SessionLocal()
    try:
        ticket = TicketService(db).get_ticket(ticket_id)
        return TicketRead.model_validate(ticket).model_dump(mode="json")
    finally:
        db.close()


@mcp.tool
def list_open_tickets(limit: int = 20) -> list[dict]:
    """List currently open or in-progress tickets for queue review.

    Args:
        limit: Maximum number of tickets to return.
    """
    db = SessionLocal()
    try:
        tickets = TicketService(db).list_open_tickets(limit=limit)
        return [TicketRead.model_validate(ticket).model_dump(mode="json") for ticket in tickets]
    finally:
        db.close()


@mcp.tool
def search_similar_tickets(ticket_id: int, top_k: int = 5) -> list[dict]:
    """Find resolved historical tickets similar to the given ticket.

    Args:
        ticket_id: Current ticket ID used as the similarity query source.
        top_k: Maximum number of historical tickets to return.
    """
    db = SessionLocal()
    try:
        results = TicketSimilarityService(db).list_similar_tickets(ticket_id, top_k=top_k)
        return [SimilarTicketRead.model_validate(result).model_dump(mode="json") for result in results]
    finally:
        db.close()


@mcp.tool
def get_analytics_overview() -> dict:
    """Return a lightweight operational overview of tickets and AI usage."""
    db = SessionLocal()
    try:
        return AnalyticsService(db).get_overview()
    finally:
        db.close()


@mcp.tool
def run_multi_agent_ticket_process(ticket_id: int, dry_run: bool = True) -> dict:
    """Run the enterprise multi-agent ticket analysis workflow.

    Args:
        ticket_id: Ticket to analyze with the multi-agent workflow.
        dry_run: When true, return a preview without persisting workflow side effects.
    """
    # MCP 侧默认强调 dry_run，避免外部 AI Client 一上来就改动数据库状态。
    db = SessionLocal()
    try:
        return MCPAgentService(db).run_multi_agent_ticket_process(ticket_id=ticket_id, dry_run=dry_run)
    finally:
        db.close()


@mcp.tool
def get_agent_audit_trail(ticket_id: int) -> dict:
    """Get the latest multi-agent audit trail recorded for a ticket.

    Args:
        ticket_id: Ticket ID whose latest multi-agent run trail should be returned.
    """
    db = SessionLocal()
    try:
        return MCPAgentService(db).get_agent_audit_trail(ticket_id=ticket_id)
    finally:
        db.close()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
