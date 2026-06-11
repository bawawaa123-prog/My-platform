from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import (
    SuggestionApproveRequest,
    SuggestionEditRequest,
    SuggestionRejectRequest,
    SuggestionReviewResponse,
)
from app.services.review_service import ReviewService


router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("/{suggestion_id}/approve", response_model=SuggestionReviewResponse)
def approve_suggestion(
    suggestion_id: int,
    payload: SuggestionApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuggestionReviewResponse:
    suggestion = ReviewService(db).approve_suggestion(suggestion_id, payload, current_user)
    return SuggestionReviewResponse.model_validate(suggestion)


@router.post("/{suggestion_id}/edit", response_model=SuggestionReviewResponse)
def edit_suggestion(
    suggestion_id: int,
    payload: SuggestionEditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuggestionReviewResponse:
    suggestion = ReviewService(db).edit_suggestion(suggestion_id, payload, current_user)
    return SuggestionReviewResponse.model_validate(suggestion)


@router.post("/{suggestion_id}/reject", response_model=SuggestionReviewResponse)
def reject_suggestion(
    suggestion_id: int,
    payload: SuggestionRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuggestionReviewResponse:
    suggestion = ReviewService(db).reject_suggestion(suggestion_id, payload, current_user)
    return SuggestionReviewResponse.model_validate(suggestion)
