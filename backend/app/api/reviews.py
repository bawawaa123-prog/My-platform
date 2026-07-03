'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-06-01 16:51:24
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 17:25:48
FilePath: \My-platform\backend\app\api\reviews.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user, require_reviewer
from app.db.session import get_db
from app.models.user import User
from app.schemas.review import (
    PendingSuggestionPage,
    PendingSuggestionRead,
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
    current_user: User = Depends(require_reviewer),
) -> SuggestionReviewResponse:
    suggestion = ReviewService(db).approve_suggestion(suggestion_id, payload, current_user)
    return SuggestionReviewResponse.model_validate(suggestion)


@router.post("/{suggestion_id}/edit", response_model=SuggestionReviewResponse)
def edit_suggestion(
    suggestion_id: int,
    payload: SuggestionEditRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> SuggestionReviewResponse:
    suggestion = ReviewService(db).edit_suggestion(suggestion_id, payload, current_user)
    return SuggestionReviewResponse.model_validate(suggestion)


@router.post("/{suggestion_id}/reject", response_model=SuggestionReviewResponse)
def reject_suggestion(
    suggestion_id: int,
    payload: SuggestionRejectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> SuggestionReviewResponse:
    suggestion = ReviewService(db).reject_suggestion(suggestion_id, payload, current_user)
    return SuggestionReviewResponse.model_validate(suggestion)

@router.get("/pending-suggestions", response_model=PendingSuggestionPage)
def list_pending_suggestions(
    ticket_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PendingSuggestionPage:
    page=ReviewService(db).list_pending_suggestions(
        ticket_id=ticket_id,
        limit=limit,
        offset=offset
    )
    return PendingSuggestionPage(
        items=[PendingSuggestionRead.model_validate(s) for s in page["items"]],
        total=page["total"],
        limit=page["limit"],
        offset=page["offset"],
    )