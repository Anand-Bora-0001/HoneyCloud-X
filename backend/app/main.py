"""
HoneyCloud-X: Production-Grade Honeypot Intelligence Platform
=============================================================
App Factory — Thin orchestrator that mounts routers and middleware.

All business logic lives in:
  - api/routes/   → HTTP endpoint handlers
  - services/     → Business logic
  - core/         → Security, config, caching
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import asyncio
import logging

# Configuration (must be first — sets up logging and directories)
from .config import settings

logger = logging.getLogger(__name__)

# ========================
# APP FACTORY
# ========================

app = FastAPI(
    title=settings.app_name,
    description="Production-Grade Honeypot Intelligence Platform with AI Threat Detection",
    version=settings.app_version,
    debug=settings.debug
)

# ========================
# CORS MIDDLEWARE
# ========================

allowed_origins = ["*"] if not os.getenv("RENDER") else [
    "http://localhost:5173",
    "http://localhost:3000",
    os.getenv("FRONTEND_URL", "https://honeycloud-frontend.onrender.com"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ========================
# MOUNT ROUTERS
# ========================

from .api.routes.auth import router as auth_router
from .api.routes.events import router as events_router
from .api.routes.reports import router as reports_router
from .api.routes.telegram import router as telegram_router
from .api.routes.alerts import router as alerts_router
from .api.routes.ml import router as ml_router
from .api.routes.health import router as health_router
from .api.routes.enhancements import router as enhancements_router
from .api.routes.shadow_nodes import router as shadow_nodes_router

app.include_router(auth_router)
app.include_router(events_router)
app.include_router(reports_router)
app.include_router(telegram_router)
app.include_router(alerts_router)
app.include_router(ml_router)
app.include_router(health_router)
app.include_router(enhancements_router)
app.include_router(shadow_nodes_router)

# SaaS router (optional)
try:
    from .saas_api import router as saas_router
    app.include_router(saas_router)
except ImportError:
    pass

# ========================
# STARTUP / SHUTDOWN
# ========================

@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"🔧 Environment: {'Development' if settings.debug else 'Production'}")

    # Initialize database
    try:
        from .database import init_db
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database init failed: {e}")

    # Start ML training
    try:
        from .ml_trainer import start_background_training
        start_background_training()
        logger.info("🤖 ML training service started")
    except ImportError:
        logger.info("ML trainer not available — basic mode")

    # Load enhancement modules
    _load_enhancements()

    logger.info(f"📊 Dashboard: http://{settings.host}:5173")
    logger.info(f"📚 API Docs: http://{settings.host}:{settings.port}/docs")


def _load_enhancements():
    """Load optional enhancement modules with graceful degradation"""
    from .api.routes.enhancements import set_enhancement_modules

    modules = {"available": False}
    try:
        from .deep_learning_engine import DeepLearningEngine
        from .stream_processor import RealTimeStreamProcessor
        from .threat_intelligence import ThreatIntelligenceEngine
        from .production_optimizer import IntelligentCache, PerformanceMonitor, DatabaseOptimizer
        from .advanced_security import ThreatHunter, AutomatedResponseSystem, SecurityAuditLogger
        from .advanced_analytics import PredictiveAnalytics, BusinessIntelligence, RiskAssessment

        modules = {
            "available": True,
            "deep_learning_engine": DeepLearningEngine(),
            "stream_processor": RealTimeStreamProcessor(),
            "threat_intel_engine": ThreatIntelligenceEngine(),
            "intelligent_cache": IntelligentCache(),
            "performance_monitor": PerformanceMonitor(),
            "database_optimizer": DatabaseOptimizer(),
            "threat_hunter": ThreatHunter(),
            "automated_response": AutomatedResponseSystem(),
            "security_audit_logger": SecurityAuditLogger(),
            "predictive_analytics": PredictiveAnalytics(),
            "business_intelligence": BusinessIntelligence(),
            "risk_assessment": RiskAssessment(),
        }
        logger.info("✅ All enhancement modules loaded")
    except ImportError as e:
        logger.warning(f"⚠️ Enhancement modules not available: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Enhancement init failed: {e}")

    set_enhancement_modules(modules)

# ========================
# FRONTEND STATIC FILES
# ========================

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_PROJECT_DIR = _BACKEND_DIR.parent
_FRONTEND_DIR = _PROJECT_DIR / "frontend"

os.makedirs("reports", exist_ok=True)

if _FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR)), name="frontend_static")

    @app.get("/login.html", response_class=HTMLResponse, include_in_schema=False)
    async def serve_login():
        return FileResponse(str(_FRONTEND_DIR / "login.html"))

    @app.get("/index.html", response_class=HTMLResponse, include_in_schema=False)
    async def serve_index():
        return FileResponse(str(_FRONTEND_DIR / "index.html"))

    @app.get("/dashboard.html", response_class=HTMLResponse, include_in_schema=False)
    async def serve_dashboard():
        return FileResponse(str(_FRONTEND_DIR / "dashboard.html"))

    @app.get("/pricing.html", response_class=HTMLResponse, include_in_schema=False)
    async def serve_pricing():
        return FileResponse(str(_FRONTEND_DIR / "pricing.html"))

    @app.get("/telegram-setup.html", response_class=HTMLResponse, include_in_schema=False)
    async def serve_telegram_setup():
        return FileResponse(str(_FRONTEND_DIR / "telegram-setup.html"))

    @app.get("/config.js", include_in_schema=False)
    async def serve_config_js():
        return FileResponse(str(_FRONTEND_DIR / "config.js"), media_type="application/javascript")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def serve_root():
        return FileResponse(str(_FRONTEND_DIR / "login.html"))

    logger.info(f"Frontend served from: {_FRONTEND_DIR}")
else:
    # API-only mode health check
    @app.get("/")
    def root():
        return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}

    logger.warning(f"Frontend not found at {_FRONTEND_DIR}")

# ========================
# LOCAL RUN
# ========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
