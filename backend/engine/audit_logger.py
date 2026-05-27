from backend.db.database import async_session
from backend.db.models import AuditEvent
from sqlalchemy import insert
import uuid

async def log_audit_event(scan_run_id: str, event_data: dict):
    async with async_session() as session:
        stmt = insert(AuditEvent).values(
            scan_run_id=uuid.UUID(scan_run_id),
            agent=event_data.get("agent", "ComplianceGuard-Scanner"),
            tool_called=event_data.get("tool_called"),
            intent=event_data.get("intent"),
            policy_decision=event_data.get("policy_decision", "ALLOW"),
            input_hash=event_data.get("input_hash"),
            output_hash=event_data.get("output_hash"),
            signature=event_data.get("signature")
        )
        await session.execute(stmt)
        await session.commit()
