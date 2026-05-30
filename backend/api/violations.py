from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid
from pathlib import Path
from backend.db.database import get_db
from backend.db.models import ScanRun, Violation

router = APIRouter()


def _read_code_snippet(repo_path: str, file_path: Optional[str], line_number: Optional[int], context: int = 2) -> dict:
    if not repo_path or not file_path:
        return {"code_snippet": None, "snippet_start_line": None}

    try:
        repo_root = Path(repo_path).resolve()
        target_path = (repo_root / file_path).resolve()
        target_path.relative_to(repo_root)
    except (OSError, ValueError):
        return {"code_snippet": None, "snippet_start_line": None}

    try:
        lines = target_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return {"code_snippet": None, "snippet_start_line": None}

    if not lines:
        return {"code_snippet": None, "snippet_start_line": None}

    focus_line = line_number if line_number and line_number > 0 else 1
    start = max(1, focus_line - context)
    end = min(len(lines), focus_line + context)

    return {
        "code_snippet": "\n".join(lines[start - 1:end]),
        "snippet_start_line": start,
    }


def _serialize_violation(violation: Violation, repo_path: str) -> dict:
    return {
        "id": str(violation.id),
        "scan_run_id": str(violation.scan_run_id),
        "service": violation.service,
        "severity": violation.severity,
        "status": violation.status,
        "category": violation.category,
        "description": violation.description,
        "file_path": violation.file_path,
        "line_number": violation.line_number,
        "remediation": violation.remediation,
        "opa_policy_ref": violation.opa_policy_ref,
        "detected_at": violation.detected_at.isoformat() if violation.detected_at else None,
        **_read_code_snippet(repo_path, violation.file_path, violation.line_number),
    }


@router.get("/violations")
async def list_violations(
    scan_id: Optional[uuid.UUID] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Violation, ScanRun.repo_path).join(ScanRun, Violation.scan_run_id == ScanRun.id)
    if scan_id:
        query = query.where(Violation.scan_run_id == scan_id)
    if severity:
        query = query.where(Violation.severity == severity)
    if status:
        query = query.where(Violation.status == status)
    
    result = await db.execute(query)
    return [_serialize_violation(violation, repo_path) for violation, repo_path in result.all()]
