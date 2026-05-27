from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api import scan, report, violations, audit, ws
from backend.settings import settings

app = FastAPI(title="ComplianceGuard AI", version="2.0")

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
app.include_router(ws.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
