from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from backend.db.database import get_db
from backend.db.models import AuditEvent

router = APIRouter()

@router.get("/audit/{scan_id}")
async def get_audit_log(scan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    query = select(AuditEvent).where(AuditEvent.scan_run_id == scan_id).order_by(AuditEvent.timestamp.asc())
    result = await db.execute(query)
    audit_events = result.scalars().all()
    return [{
        "event_id": str(event.event_id),
        "scan_run_id": str(event.scan_run_id),
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "agent": event.agent,
        "tool_called": event.tool_called,
        "intent": event.intent,
        "policy_decision": event.policy_decision,
        "input_hash": event.input_hash,
        "output_hash": event.output_hash,
        "signature": event.signature,
    } for event in audit_events]
