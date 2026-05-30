from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
from backend.db.database import get_db
from backend.db.models import ScanLog, ScanRun
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.agent.scan_agent import run_scan
from backend.api.ws import manager

router = APIRouter()

class ScanRequest(BaseModel):
    service_name: str
    repo_path: str
    scan_depth: str = "full"
    standards: List[str] = ["FIPS-140-3", "CIS-Docker", "OWASP-Dependency"]

class ScanResponse(BaseModel):
    scan_id: uuid.UUID
    status: str
    message: str

@router.post("/scan", response_model=ScanResponse, status_code=202)
async def trigger_scan(
    request: ScanRequest, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    scan_id = uuid.uuid4()
    
    # Create scan run in DB
    new_scan = ScanRun(
        id=scan_id,
        service_name=request.service_name,
        repo_path=request.repo_path,
        status="PENDING",
        standards=request.standards
    )
    db.add(new_scan)
    await db.commit()

    # Define event handler for websocket
    async def on_event(event):
        await manager.broadcast_to_scan(str(scan_id), event)

    # Start scan in background
    background_tasks.add_task(
        run_scan, 
        str(scan_id), 
        request.repo_path, 
        request.service_name, 
        request.standards,
        on_event=on_event
    )

    return ScanResponse(
        scan_id=scan_id,
        status="PENDING",
        message="Scan queued. Connect to /ws/scan-status for live updates."
    )

@router.get("/scan/{scan_id}")
async def get_scan_status(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    scan_run = await db.get(ScanRun, scan_id)
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan_run

@router.get("/scans")
async def list_scans(limit: int = 25, db: AsyncSession = Depends(get_db)):
    query = select(ScanRun).order_by(ScanRun.started_at.desc()).limit(min(limit, 100))
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/scan/{scan_id}/logs")
async def get_scan_logs(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    scan_run = await db.get(ScanRun, scan_id)
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan not found")

    query = select(ScanLog).where(ScanLog.scan_run_id == scan_id).order_by(ScanLog.timestamp.asc())
    result = await db.execute(query)
    return result.scalars().all()
