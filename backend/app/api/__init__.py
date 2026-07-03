from fastapi import APIRouter

from app.api.ai import router as ai_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.reviews import router as reviews_router
from app.api.tickets import router as tickets_router
from app.api.audit_logs import router as audit_logs_router

router = APIRouter()
router.include_router(ai_router)
router.include_router(analytics_router)
router.include_router(auth_router)
router.include_router(health_router)
router.include_router(knowledge_router)
router.include_router(reviews_router)
router.include_router(tickets_router)
router.include_router(audit_logs_router)
