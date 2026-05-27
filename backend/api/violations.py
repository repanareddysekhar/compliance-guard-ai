from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from backend.db.database import get_db
from backend.db.models import Violation

router = APIRouter()

@router.get("/violations")
async def list_violations(
    scan_id: Optional[uuid.UUID] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Violation)
    if scan_id:
        query = query.where(Violation.scan_run_id == scan_id)
    if severity:
        query = query.where(Violation.severity == severity)
    if status:
        query = query.where(Violation.status == status)
    
    result = await db.execute(query)
    violations = result.scalars().all()
    return violations
