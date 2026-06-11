from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsOverviewRead
from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewRead)
def get_analytics_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalyticsOverviewRead:
    overview = AnalyticsService(db).get_overview()
    return AnalyticsOverviewRead.model_validate(overview)
