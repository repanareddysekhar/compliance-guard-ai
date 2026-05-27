from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
from backend.db.database import get_db
from backend.db.models import AuditEvent

router = APIRouter()

@router.get("/audit/{scan_id}")
async def get_audit_log(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    query = select(AuditEvent).where(AuditEvent.scan_run_id == scan_id)
    result = await db.execute(query)
    audit_events = result.scalars().all()
    return audit_events
