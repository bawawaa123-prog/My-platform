from pathlib import Path
from datetime import UTC, datetime

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_message import TicketMessage
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.ticket_message_repository import TicketMessageRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ai import TicketClassification
from app.schemas.ticket import TicketCreate, TicketRead, TicketUpdate
from app.schemas.ticket_message import TicketMessageCreate
from app.services.audit_service import AuditService
from app.services.llm_service import LLMGenerationError, get_llm_client
from app.services.ticket_similarity_service import TicketSimilarityService


class TicketService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TicketRepository(db)
        self.user_repository = UserRepository(db)
        self.message_repository = TicketMessageRepository(db)
        self.audit_service = AuditService(db)
        self.llm_client = get_llm_client()

    def create_ticket(self, payload: TicketCreate, created_by: User) -> Ticket:
        # 创建工单时同步补 embedding 和 audit_log，
        # 保证后续“相似工单推荐”和“审计追踪”立刻可用。
        ticket = Ticket(
            title=payload.title,
            content=payload.content,
            customer_name=payload.customer_name,
            customer_email=payload.customer_email,
            category=payload.category,
            priority=payload.priority,
            status="open",
            source=payload.source,
            created_by=created_by.id,
        )
        created_ticket = self.repository.create(ticket)
        TicketSimilarityService(self.db).ensure_ticket_embedding(created_ticket)
        self.audit_service.log_action(
            user=created_by,
            action="create_ticket",
            target_type="ticket",
            target_id=created_ticket.id,
            detail_json={
                "title": created_ticket.title,
                "status": created_ticket.status,
                "priority": created_ticket.priority,
                "category": created_ticket.category,
            },
        )
        return created_ticket

    def list_tickets(
        self,
        *,
        status: str | None = None,
        priority: str | None = None,
        category: str | None = None,
    ) -> list[Ticket]:
        return self.repository.list_filtered(status=status, priority=priority, category=category)

    def list_open_tickets(self, *, limit: int = 20) -> list[Ticket]:
        tickets = self.repository.list_all()
        open_statuses = {"open", "ai_processing", "waiting_review", "in_progress"}
        return [ticket for ticket in tickets if ticket.status in open_statuses][:limit]

    def get_ticket(self, ticket_id: int) -> Ticket:
        ticket = self.repository.get_by_id(ticket_id)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )
        return ticket

    def update_ticket(self, ticket_id: int, payload: TicketUpdate, current_user: User) -> Ticket:
        ticket = self.get_ticket(ticket_id)
        update_data = payload.model_dump(exclude_unset=True)

        for field_name, value in update_data.items():
            setattr(ticket, field_name, value)

        if "status" in update_data:
            ticket.closed_at = (
                datetime.now(UTC)
                if ticket.status == "closed"
                else None
            )

        updated_ticket = self.repository.save(ticket)
        if {"title", "content", "status"} & set(update_data):
            TicketSimilarityService(self.db).ensure_ticket_embedding(updated_ticket)
        self.audit_service.log_action(
            user=current_user,
            action="update_ticket",
            target_type="ticket",
            target_id=updated_ticket.id,
            detail_json=update_data,
        )
        return updated_ticket

    def list_ticket_messages(self, ticket_id: int) -> list[TicketMessage]:
        self.get_ticket(ticket_id)
        return self.message_repository.list_by_ticket_id(ticket_id)

    def add_ticket_message(
        self,
        ticket_id: int,
        payload: TicketMessageCreate,
        current_user: User,
    ) -> TicketMessage:
        ticket = self.get_ticket(ticket_id)
        message = TicketMessage(
            ticket_id=ticket.id,
            sender_type=payload.sender_type,
            sender_name=current_user.username,
            content=payload.content,
        )
        created_message = self.message_repository.create(message)
        self.audit_service.log_action(
            user=current_user,
            action="add_ticket_message",
            target_type="ticket",
            target_id=ticket.id,
            detail_json={
                "message_id": created_message.id,
                "sender_type": created_message.sender_type,
            },
        )
        return created_message

    def classify_ticket(self, ticket_id: int, current_user: User) -> TicketClassification:
        # 分类优先尝试 LLM；如果模型不可用或输出不合法，就回退到本地规则，
        # 这样 mock 模式和无密钥环境也能完整演示。
        ticket = self.get_ticket(ticket_id)

        used_fallback = False
        try:
            classification = self._generate_ticket_classification(ticket)
        except (LLMGenerationError, ValidationError):
            classification = self._build_fallback_classification(ticket)
            used_fallback = True

        ticket.category = classification.category
        ticket.priority = classification.priority
        ticket.sentiment = classification.sentiment
        ticket.ai_summary = classification.summary
        ticket.recommended_department = classification.recommended_department

        self.repository.save(ticket)
        self.audit_service.log_action(
            user=current_user,
            action="classify_ticket_ai",
            target_type="ticket",
            target_id=ticket.id,
            detail_json={
                "category": classification.category,
                "priority": classification.priority,
                "sentiment": classification.sentiment,
                "need_human": classification.need_human,
                "recommended_department": classification.recommended_department,
                "used_fallback": used_fallback,
            },
        )
        return classification

    def get_system_user(self) -> User:
        user = self.user_repository.get_by_email("admin@example.com")
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default system user is not available",
            )
        return user

    def get_user_by_id(self, user_id: int) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def apply_workflow_recommendation(
        self,
        *,
        ticket_id: int,
        next_status: str,
        assign_to_department: str,
        next_action: str,
        internal_note: str,
    ) -> Ticket:
        # WorkflowAgent 最终只通过 service 改工单状态，
        # 不让 Agent 自己直接操作数据库，保持分层清晰。
        ticket = self.get_ticket(ticket_id)
        ticket.status = next_status
        ticket.recommended_department = assign_to_department
        if next_status == "closed":
            ticket.closed_at = datetime.now(UTC)
        else:
            ticket.closed_at = None

        updated_ticket = self.repository.save(ticket)
        self.audit_service.log_action(
            user=self.get_system_user(),
            action="apply_workflow_recommendation",
            target_type="ticket",
            target_id=updated_ticket.id,
            detail_json={
                "next_status": next_status,
                "assign_to_department": assign_to_department,
                "next_action": next_action,
                "internal_note": internal_note,
            },
        )
        return updated_ticket

    @staticmethod
    def serialize_ticket(ticket: Ticket) -> dict:
        return TicketRead.model_validate(ticket).model_dump(mode="json")

    def _generate_ticket_classification(self, ticket: Ticket) -> TicketClassification:
        # Prompt 模板放在 prompts 目录，避免把长提示词硬编码进业务逻辑。
        prompt = self._load_classification_prompt().format(
            title=ticket.title,
            content=ticket.content,
            customer_name=ticket.customer_name,
            customer_email=ticket.customer_email,
            category=ticket.category,
            priority=ticket.priority,
        )
        response = self.llm_client.generate_json(prompt)
        return TicketClassification.model_validate(response)

    def _build_fallback_classification(self, ticket: Ticket) -> TicketClassification:
        # 本地规则分类是项目的兜底能力：
        # 即使没有真实模型，也能跑通“分类 -> 审核 -> 工作流”主链路。
        text = f"{ticket.title}\n{ticket.content}".lower()

        category = "other"
        recommended_department = "customer_support"

        if any(keyword in text for keyword in ["退款", "refund", "chargeback", "退费"]):
            category = "refund"
            recommended_department = "billing"
        elif any(keyword in text for keyword in ["发票", "invoice", "税号"]):
            category = "invoice"
            recommended_department = "finance"
        elif any(keyword in text for keyword in ["支付", "payment", "扣款", "未支付", "账单"]):
            category = "payment"
            recommended_department = "billing"
        elif any(keyword in text for keyword in ["账号", "account", "登录", "密码", "验证码"]):
            category = "account"
            recommended_department = "customer_support"
        elif any(keyword in text for keyword in ["bug", "报错", "错误", "异常", "打不开", "故障"]):
            category = "technical"
            recommended_department = "technical_support"
        elif any(keyword in text for keyword in ["hr", "人事", "招聘", "请假", "薪资"]):
            category = "hr"
            recommended_department = "hr"
        elif any(keyword in text for keyword in ["电脑", "网络", "vpn", "邮箱", "系统权限", "it"]):
            category = "it"
            recommended_department = "it"
        elif any(keyword in text for keyword in ["功能", "产品", "需求", "体验"]):
            category = "product"
            recommended_department = "product"

        priority = "medium"
        if any(keyword in text for keyword in ["紧急", "立刻", "马上", "asap", "critical", "严重", "无法使用"]):
            priority = "urgent"
        elif any(keyword in text for keyword in ["尽快", "影响很大", "失败", "投诉", "丢失"]):
            priority = "high"
        elif any(keyword in text for keyword in ["咨询", "建议", "一般", "了解一下"]):
            priority = "low"

        sentiment = "neutral"
        if any(keyword in text for keyword in ["投诉", "愤怒", "生气", "差评", "angry", "terrible", "糟糕"]):
            sentiment = "angry"
        elif any(keyword in text for keyword in ["失败", "问题", "异常", "无法", "负面", "失望"]):
            sentiment = "negative"
        elif any(keyword in text for keyword in ["感谢", "满意", "表扬", "感谢你们"]):
            sentiment = "positive"

        need_human = (
            priority in {"high", "urgent"}
            or sentiment == "angry"
            or category in {"refund", "payment", "invoice"}
        )

        summary = self._build_summary(ticket.content)

        return TicketClassification(
            category=category,
            priority=priority,
            sentiment=sentiment,
            need_human=need_human,
            summary=summary,
            recommended_department=recommended_department,
        )

    @staticmethod
    def _load_classification_prompt() -> str:
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "classify_ticket.txt"
        return prompt_path.read_text(encoding="utf-8")

    @staticmethod
    def _build_summary(content: str, max_length: int = 120) -> str:
        normalized = " ".join(content.split()).strip()
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 3]}..."
