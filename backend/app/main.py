"""
HoneyCloud: Production-Grade Honeypot Intelligence Platform
=============================================================
App Factory — Thin orchestrator that mounts routers and middleware.

All business logic lives in:
  - api/routes/   → HTTP endpoint handlers
  - services/     → Business logic
  - core/         → Security, config, caching
"""
from fastapi import FastAPI, HTTPException
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
from .api.routes import auth, events, investigation, recycle_bin

app.include_router(auth_router)
app.include_router(events.router)
app.include_router(reports_router)
app.include_router(telegram_router)
app.include_router(alerts_router)
app.include_router(ml_router)
app.include_router(health_router)
app.include_router(enhancements_router)
app.include_router(shadow_nodes_router)
app.include_router(investigation.router)
app.include_router(recycle_bin.router)

from .deception_env.router import router as deception_router
app.include_router(deception_router)

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

    # Start Background Reporting Scheduler
    try:
        from .services.scheduler import start_reporting_scheduler
        start_reporting_scheduler()
    except Exception as sched_err:
        logger.error(f"Failed to start reporting scheduler: {sched_err}")

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
from .config import settings
os.makedirs(settings.reports_dir, exist_ok=True)


_DIST_DIR = _FRONTEND_DIR / "dist"
_VANILLA_DIR = _PROJECT_DIR / "frontend-vanilla"

if _DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(_DIST_DIR / "assets")), name="frontend_assets")
    
    @app.get("/")
    async def root():
        """Serve index.html at root."""
        return FileResponse(str(_DIST_DIR / "index.html"))

    @app.get("/{catchall:path}")
    async def catch_all(catchall: str):
        """Catch-all redirecting to index.html for SPA router (ignoring api/auth/docs endpoints)."""
        if catchall.startswith(("api", "auth", "docs", "redoc", "openapi.json", "health")):
            raise HTTPException(status_code=404, detail="Not found")
        return FileResponse(str(_DIST_DIR / "index.html"))

    logger.info(f"React Frontend served from: {_DIST_DIR}")

elif _VANILLA_DIR.exists():
    if (_VANILLA_DIR / "css").exists():
        app.mount("/css", StaticFiles(directory=str(_VANILLA_DIR / "css")), name="frontend_css")
    if (_VANILLA_DIR / "js").exists():
        app.mount("/js", StaticFiles(directory=str(_VANILLA_DIR / "js")), name="frontend_js")
    if (_VANILLA_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(_VANILLA_DIR / "assets")), name="frontend_assets")
    
    app.mount("/static", StaticFiles(directory=str(_VANILLA_DIR)), name="frontend_static")
    
    @app.get("/")
    async def root():
        return FileResponse(str(_VANILLA_DIR / "index.html"))

    @app.get("/login.html")
    async def serve_login():
        return FileResponse(str(_VANILLA_DIR / "login.html"))

    @app.get("/dashboard.html")
    async def serve_dashboard():
        return FileResponse(str(_VANILLA_DIR / "dashboard.html"))

    @app.get("/attack-details.html")
    async def serve_attack_details():
        return FileResponse(str(_VANILLA_DIR / "attack-details.html"))

    @app.get("/reports.html")
    async def serve_reports():
        return FileResponse(str(_VANILLA_DIR / "reports.html"))

    @app.get("/recycle-bin.html")
    async def serve_recycle_bin():
        return FileResponse(str(_VANILLA_DIR / "recycle-bin.html"))

    @app.get("/settings.html")
    async def serve_settings():
        return FileResponse(str(_VANILLA_DIR / "settings.html"))

    @app.get("/{filename}.html")
    async def serve_html(filename: str):
        file_path = _VANILLA_DIR / f"{filename}.html"
        if file_path.exists():
            return FileResponse(str(file_path))
        raise HTTPException(status_code=404, detail="Page not found")

    @app.get("/config.js", include_in_schema=False)
    async def serve_config_js():
        api_base = os.getenv("VITE_API_URL", "")
        content = f"""
const CONFIG = {{
    API_BASE: "{api_base}",
    VERSION: "{settings.app_version}"
}};
console.log('[HoneyCloud] Dynamic Configuration Loaded: ' + (CONFIG.API_BASE || 'Relative'));
"""
        return HTMLResponse(content=content, media_type="application/javascript")

    logger.info(f"Legacy Vanilla Frontend served from: {_VANILLA_DIR}")

else:
    @app.get("/")
    def root():
        return {"status": "healthy", "service": settings.app_name, "version": settings.app_version}

    logger.warning(f"Frontend static directories not found.")

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
