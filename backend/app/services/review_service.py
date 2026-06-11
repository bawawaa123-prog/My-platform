from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion
from app.models.user import User
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.review import (
    SuggestionApproveRequest,
    SuggestionEditRequest,
    SuggestionRejectRequest,
)
from app.services.audit_service import AuditService


class ReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SuggestionRepository(db)
        self.audit_service = AuditService(db)

    def approve_suggestion(
        self,
        suggestion_id: int,
        payload: SuggestionApproveRequest,
        current_user: User,
    ) -> AISuggestion:
        suggestion = self._get_reviewable_suggestion(suggestion_id)
        final_content = payload.final_content or suggestion.suggested_content

        suggestion.status = "approved"
        suggestion.reviewed_by = current_user.id
        suggestion.reviewed_at = datetime.now(UTC)
        suggestion.final_content = final_content
        suggestion.reject_reason = None

        updated = self.repository.save(suggestion)
        self.audit_service.log_action(
            user=current_user,
            action="approve_ai_suggestion",
            target_type="ai_suggestion",
            target_id=updated.id,
            detail_json={
                "ticket_id": updated.ticket_id,
                "suggestion_type": updated.suggestion_type,
                "status": updated.status,
                "used_custom_final_content": payload.final_content is not None,
            },
        )
        return updated

    def edit_suggestion(
        self,
        suggestion_id: int,
        payload: SuggestionEditRequest,
        current_user: User,
    ) -> AISuggestion:
        suggestion = self._get_reviewable_suggestion(suggestion_id)

        suggestion.status = "edited"
        suggestion.reviewed_by = current_user.id
        suggestion.reviewed_at = datetime.now(UTC)
        suggestion.final_content = payload.final_content
        suggestion.reject_reason = None

        updated = self.repository.save(suggestion)
        self.audit_service.log_action(
            user=current_user,
            action="edit_ai_suggestion",
            target_type="ai_suggestion",
            target_id=updated.id,
            detail_json={
                "ticket_id": updated.ticket_id,
                "suggestion_type": updated.suggestion_type,
                "status": updated.status,
            },
        )
        return updated

    def reject_suggestion(
        self,
        suggestion_id: int,
        payload: SuggestionRejectRequest,
        current_user: User,
    ) -> AISuggestion:
        suggestion = self._get_reviewable_suggestion(suggestion_id)

        suggestion.status = "rejected"
        suggestion.reviewed_by = current_user.id
        suggestion.reviewed_at = datetime.now(UTC)
        suggestion.final_content = None
        suggestion.reject_reason = payload.reject_reason

        updated = self.repository.save(suggestion)
        self.audit_service.log_action(
            user=current_user,
            action="reject_ai_suggestion",
            target_type="ai_suggestion",
            target_id=updated.id,
            detail_json={
                "ticket_id": updated.ticket_id,
                "suggestion_type": updated.suggestion_type,
                "status": updated.status,
                "reject_reason": updated.reject_reason,
            },
        )
        return updated

    def apply_review_action(
        self,
        *,
        suggestion_id: int,
        action: str,
        current_user: User,
        final_content: str | None = None,
        reject_reason: str | None = None,
    ) -> AISuggestion:
        if action == "approve":
            return self.approve_suggestion(
                suggestion_id,
                SuggestionApproveRequest(final_content=final_content),
                current_user,
            )
        if action == "edit":
            return self.edit_suggestion(
                suggestion_id,
                SuggestionEditRequest(final_content=final_content or ""),
                current_user,
            )
        if action == "reject":
            return self.reject_suggestion(
                suggestion_id,
                SuggestionRejectRequest(reject_reason=reject_reason or ""),
                current_user,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported review action: {action}",
        )

    def _get_reviewable_suggestion(self, suggestion_id: int) -> AISuggestion:
        suggestion = self.repository.get_by_id(suggestion_id)
        if suggestion is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI suggestion not found",
            )
        if suggestion.status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="AI suggestion has already been reviewed",
            )
        return suggestion
