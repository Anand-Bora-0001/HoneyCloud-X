"""
Health and status routes with infrastructure diagnostics.
"""
from fastapi import APIRouter
from datetime import datetime
import logging

from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Kubernetes-style health check with infrastructure status"""
    # Database info
    try:
        from ...database import get_engine_info
        db_info = get_engine_info()
    except Exception:
        db_info = {"backend": "unknown"}

    # Cache info
    try:
        from ...core.cache import get_cache_info
        cache_info = get_cache_info()
    except Exception:
        cache_info = {"backend": "none"}

    # Worker info
    try:
        from ...worker import CELERY_AVAILABLE
        worker_status = "connected" if CELERY_AVAILABLE else "disabled"
    except Exception:
        worker_status = "disabled"

    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
        "infrastructure": {
            "database": db_info,
            "cache": cache_info,
            "worker": worker_status,
        },
        "checks": {
            "api": "ok",
            "database": db_info.get("backend", "ok"),
            "cache": cache_info.get("backend", "none"),
            "telegram": "configured" if settings.is_telegram_configured else "not_configured",
            "email": "configured" if settings.is_email_configured else "not_configured"
        }
    }
