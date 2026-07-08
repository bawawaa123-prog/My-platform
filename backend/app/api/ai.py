import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status,Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.api.auth import get_current_user
from app.db.session import get_db
from app.graphs.ticket_agent_graph import TicketAgentGraph
from app.graphs.ticket_multi_agent_graph import TicketMultiAgentGraph
from app.models.user import User
from app.schemas.agent import AgentRunLogPage, AgentRunLogRead, LatestAgentRunsByType
from app.schemas.ai import (
    AIMultiAgentPendingReviewRead,
    AIMultiAgentProcessRead,
    AIReplyDraftRead,
    AIWorkflowPendingReviewRead,
    AIWorkflowProcessRead,
    AIWorkflowResumeRequest,
    TicketClassification,
)
from app.services.agent_run_service import AgentRunService
from app.services.rag_service import RagService
from app.services.ticket_service import TicketService


router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/tickets/{ticket_id}/classify", response_model=TicketClassification)
def classify_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TicketClassification:
    # 单独暴露分类接口，方便前端先做分诊展示，
    # 不必每次都跑完整工作流。
    return TicketService(db).classify_ticket(ticket_id, current_user)


@router.post("/tickets/{ticket_id}/generate-reply", response_model=AIReplyDraftRead)
def generate_ticket_reply(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIReplyDraftRead:
    # 这里直接走 RAG 服务生成回复草稿，并把来源与置信度一起返回。
    ticket = TicketService(db).get_ticket(ticket_id)
    run_id = str(uuid4())
    suggestion = RagService(db).generate_ticket_reply(
        ticket,
        source_workflow="single_agent_rag",
        source_run_id=run_id,
    )

    # 持久化 AgentRunLog，使 Agent Run History 可追溯单 Agent 执行
    AgentRunService(db).upsert_run_log(
        ticket_id=ticket_id,
        run_id=run_id,
        run_type="single_agent_rag",
        status="completed",
        input_json={"ticket_id": ticket_id},
        output_json={
            "suggestion_id": suggestion.id,
            "suggested_content": suggestion.suggested_content,
            "confidence": suggestion.confidence,
            "source_workflow": "single_agent_rag",
            "source_run_id": run_id,
        },
        audit_trail_json=[],
        created_by=current_user.id,
    )

    return suggestion


@router.get("/tickets/{ticket_id}/suggestions", response_model=list[AIReplyDraftRead])
def list_ticket_suggestions(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AIReplyDraftRead]:
    TicketService(db).get_ticket(ticket_id)
    suggestions = RagService(db).suggestion_repository.list_reply_suggestions_by_ticket_id(ticket_id)
    return [AIReplyDraftRead.model_validate(suggestion) for suggestion in suggestions]


@router.get("/tickets/{ticket_id}/reviewed-suggestions", response_model=list[AIReplyDraftRead])
def list_reviewed_suggestions(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AIReplyDraftRead]:
    """Return all reviewed (approved/edited/rejected) reply suggestions for Final Review."""
    TicketService(db).get_ticket(ticket_id)
    suggestions = RagService(db).suggestion_repository.list_reviewed_reply_suggestions_by_ticket_id(ticket_id)
    return [AIReplyDraftRead.model_validate(suggestion) for suggestion in suggestions]


@router.post("/tickets/{ticket_id}/process", response_model=AIWorkflowProcessRead)
def process_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIWorkflowProcessRead:
    # 这是单流程 LangGraph 的“一键跑完”入口，适合没有人工中断的场景。
    TicketService(db).get_ticket(ticket_id)
    try:
        state = TicketAgentGraph(db).invoke(ticket_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Ticket workflow execution failed (ticket_id=%s): %s", ticket_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ticket workflow execution failed. Please try again later.",
        ) from exc
    return AIWorkflowProcessRead.model_validate(state["final_output"])


@router.post("/tickets/{ticket_id}/process/start", response_model=AIWorkflowPendingReviewRead)
def start_ticket_process(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIWorkflowPendingReviewRead:
    # start/resume 这一组接口对应带 interrupt 的工作流：
    # start 跑到人工审核节点就暂停，并返回待审核上下文。
    TicketService(db).get_ticket(ticket_id)
    try:
        return TicketAgentGraph(db).start(ticket_id, created_by_user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Ticket workflow start failed (ticket_id=%s): %s", ticket_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ticket workflow start failed. Please try again later.",
        ) from exc


@router.post("/tickets/{ticket_id}/process/resume", response_model=AIWorkflowProcessRead)
def resume_ticket_process(
    ticket_id: int,
    payload: AIWorkflowResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIWorkflowProcessRead:
    # resume 负责把审核动作重新灌回 LangGraph，让流程继续向 finalize 推进。
    TicketService(db).get_ticket(ticket_id)
    try:
        return TicketAgentGraph(db).resume(
            workflow_id=payload.workflow_id(),
            ticket_id=ticket_id,
            action=payload.action,
            reviewer_user_id=current_user.id,
            final_content=payload.final_content,
            reject_reason=payload.reject_reason,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Ticket workflow resume failed (ticket_id=%s): %s", ticket_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ticket workflow resume failed. Please try again later.",
        ) from exc


@router.post("/tickets/{ticket_id}/multi-agent-process/start", response_model=AIMultiAgentPendingReviewRead)
def start_multi_agent_ticket_process(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIMultiAgentPendingReviewRead:
    # 这是项目亮点入口：固定顺序 Multi-Agent 分析，并在人工审核前暂停。
    TicketService(db).get_ticket(ticket_id)
    try:
        return TicketMultiAgentGraph(db).start(ticket_id, created_by_user_id=current_user.id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Multi-agent workflow start failed (ticket_id=%s): %s", ticket_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multi-agent workflow start failed. Please try again later.",
        ) from exc


@router.post("/tickets/{ticket_id}/multi-agent-process/resume", response_model=AIMultiAgentProcessRead)
def resume_multi_agent_ticket_process(
    ticket_id: int,
    payload: AIWorkflowResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIMultiAgentProcessRead:
    # 与单流程 resume 对称：把审核决策送回 Multi-Agent 图，
    # 让 human_review -> finalize 走完并持久化审核结果。
    TicketService(db).get_ticket(ticket_id)
    try:
        return TicketMultiAgentGraph(db).resume(
            workflow_id=payload.workflow_id(),
            ticket_id=ticket_id,
            action=payload.action,
            reviewer_user_id=current_user.id,
            final_content=payload.final_content,
            reject_reason=payload.reject_reason,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Multi-agent workflow resume failed (ticket_id=%s): %s", ticket_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multi-agent workflow resume failed. Please try again later.",
        ) from exc


@router.get("/tickets/{ticket_id}/agent-runs", response_model=list[AgentRunLogRead])
def list_ticket_agent_runs(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    run_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[AgentRunLogRead]:
    TicketService(db).get_ticket(ticket_id)
    run_logs = AgentRunService(db).list_by_ticket_id(
        ticket_id=ticket_id,
        run_type=run_type,
        status=status_filter
    )
    return [AgentRunLogRead.model_validate(run_log) for run_log in run_logs]


@router.get(
    "/tickets/{ticket_id}/agent-runs/latest-by-type",
    response_model=LatestAgentRunsByType,
)
def list_latest_agent_runs_by_type(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LatestAgentRunsByType:
    """Return the latest AgentRunLog for each workflow type under the given ticket.

    Unlike the paginated list endpoint, this endpoint does not depend on
    limit/offset, so it reliably returns the newest run of each type even when
    the ticket has many runs.
    """
    TicketService(db).get_ticket(ticket_id)
    runs = AgentRunService(db).get_latest_by_workflow_types(ticket_id)
    return LatestAgentRunsByType(
        single_agent_rag=AgentRunLogRead.model_validate(runs["single_agent_rag"]) if runs["single_agent_rag"] else None,
        single_agent_workflow=AgentRunLogRead.model_validate(runs["single_agent_workflow"]) if runs["single_agent_workflow"] else None,
        multi_agent=AgentRunLogRead.model_validate(runs["multi_agent"]) if runs["multi_agent"] else None,
    )


@router.get("/agent-runs/{run_id}", response_model=AgentRunLogRead)
def get_agent_run(
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRunLogRead:
    run_log = AgentRunService(db).get_by_run_id(run_id)
    return AgentRunLogRead.model_validate(run_log)


@router.get("/tickets/{ticket_id}/agent-runs/page", response_model=AgentRunLogPage)
def list_ticket_agent_runs_page(
    ticket_id: int,
    run_type: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AgentRunLogPage:
    TicketService(db).get_ticket(ticket_id)
    run_logs = AgentRunService(db).list_page_by_id(
        ticket_id=ticket_id,
        run_type=run_type,
        status=status_filter,
        limit=limit,
        offset=offset
    )
    return AgentRunLogPage(
        items=[AgentRunLogRead.model_validate(run_log) for run_log in run_logs["items"]],
        total=run_logs["total"],
        limit=run_logs["limit"],
        offset=run_logs["offset"],
    )
