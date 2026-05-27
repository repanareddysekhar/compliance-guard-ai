from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from backend.db.database import get_db
from backend.db.models import Violation, AuditEvent, ScanRun
from backend.engine.report_generator import generate_report as build_report

router = APIRouter()

@router.get("/report/{scan_id}")
async def get_report(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Fetch scan run
    scan_run = await db.get(ScanRun, scan_id)
    if not scan_run:
        raise HTTPException(status_code=404, detail="Scan run not found")

    # Fetch violations
    v_query = select(Violation).where(Violation.scan_run_id == scan_id)
    v_result = await db.execute(v_query)
    violations = v_result.scalars().all()

    # Fetch audit events
    a_query = select(AuditEvent).where(AuditEvent.scan_run_id == scan_id)
    a_result = await db.execute(a_query)
    audit_events = a_result.scalars().all()

    # Generate structured report
    report = build_report(str(scan_id), violations, audit_events)
    return report
