from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.api import scan, report, violations, audit, ws, policies
from backend.settings import settings
from backend.db.database import engine, Base
from backend.agent.llm_health import LLMHealthError, check_llm_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ComplianceGuard AI", version="2.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with Base.metadata
        from backend.db.models import ScanRun, Violation, AuditEvent, ScanLog
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router,       prefix="/api")
app.include_router(report.router,     prefix="/api")
app.include_router(violations.router, prefix="/api")
app.include_router(audit.router,      prefix="/api")
app.include_router(policies.router,   prefix="/api")
app.include_router(ws.router)

@app.get("/health")
async def health_check():
    result = {"status": "healthy", "llm": {"status": "unknown"}}
    try:
        result["llm"] = await check_llm_health()
    except LLMHealthError as exc:
        result["status"] = "degraded"
        result["llm"] = {"status": "error", "detail": str(exc)}
    return result
