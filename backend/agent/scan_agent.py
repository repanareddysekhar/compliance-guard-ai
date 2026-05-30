import hashlib
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from backend.agent.claw_runner import ArmorClaw
from backend.agent.deterministic_scan import scan_repository
from backend.agent.tools.registry import build_scan_tools, discover_scan_files
from backend.armoriq_client import armoriq
from backend.armoriq_shims import ToolCallPolicy
from backend.db.database import async_session
from backend.db.models import AuditEvent, ScanLog, ScanRun, Violation
from backend.engine.violation_engine import score_violation
from backend.settings import settings

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _scan_log_message(payload: dict) -> str:
    if payload["type"] == "SCAN_STARTED":
        return f"Scan started for {payload.get('service', 'service')}"
    if payload["type"] == "TOOL_CALLED":
        return payload.get("intent") or f"Called {payload.get('tool', 'tool')}"
    if payload["type"] == "VIOLATION_FOUND":
        violation = payload.get("violation") or {}
        return violation.get("description") or "Violation found"
    if payload["type"] == "AGENT_SUMMARY":
        return "LLM agent produced final compliance summary"
    if payload["type"] == "SCAN_COMPLETED":
        summary = payload.get("summary") or {}
        return f"Scan completed with {summary.get('violations_found', 0)} violations"
    if payload["type"] == "SCAN_FAILED":
        return payload.get("error") or "Scan failed"
    return payload["type"]


async def _emit_event(on_event, payload: dict, session=None, scan_uuid: uuid.UUID | None = None):
    if session and scan_uuid:
        session.add(ScanLog(
            scan_run_id=scan_uuid,
            event_type=payload["type"],
            message=_scan_log_message(payload),
            payload=payload,
        ))
    if on_event:
        await on_event(payload)


async def _emit_audit(session, scan_uuid: uuid.UUID, tool_called: str, intent: str, decision: str = "ALLOW"):
    event = AuditEvent(
        scan_run_id=scan_uuid,
        agent="ComplianceGuard-Scanner",
        tool_called=tool_called,
        intent=intent,
        policy_decision=decision,
        input_hash=_hash_text(intent),
        output_hash=_hash_text(f"{tool_called}:{decision}"),
        signature=_hash_text(f"{scan_uuid}:{tool_called}:{decision}:{intent}")[:32],
    )
    session.add(event)


def _build_violation(
    scan_uuid: uuid.UUID,
    service_name: str,
    file_path: str | None,
    category: str,
    finding: str,
    description: str,
    remediation: str,
    policy_ref: str,
    line_number: int | None = None,
    severity: str | None = None,
) -> Violation:
    computed_severity, status = score_violation(category, finding)
    final_severity = severity if severity in {"HIGH", "MED", "LOW"} else computed_severity
    if final_severity == "HIGH":
        status = "BLOCKED"
    elif final_severity == "MED":
        status = "FLAGGED"
    else:
        status = "REPORTED"

    return Violation(
        id=uuid.uuid4(),
        scan_run_id=scan_uuid,
        service=service_name,
        severity=final_severity,
        status=status,
        category=category,
        description=description,
        file_path=file_path,
        line_number=line_number,
        remediation=remediation,
        opa_policy_ref=policy_ref,
    )


def build_scan_prompt(repo_path: str, service_name: str, standards: list[str]) -> str:
    files = discover_scan_files(repo_path)
    preview = "\n".join(f"- {path}" for path in files)

    file_contents = ""
    abs_repo = os.path.abspath(repo_path)
    if len(files) <= 20:
        blocks: list[str] = []
        for rel in files:
            try:
                with open(os.path.join(abs_repo, rel), "r", encoding="utf-8", errors="ignore") as handle:
                    content = handle.read(8000)
                blocks.append(f"### {rel}\n```\n{content}\n```")
            except OSError:
                continue
        if blocks:
            file_contents = "\n\nFile contents to analyze:\n" + "\n\n".join(blocks)

    return f"""Start a compliance scan for '{service_name}' at '{repo_path}'.
Standards: {', '.join(standards)}.

Files to inspect:
{preview}
{file_contents}

You MUST call report_finding for every violation you identify. Do not finish with only a text summary.

For each issue include: file_path, line_number, category, finding, severity (HIGH/MED/LOW), description, remediation.

Start by analyzing the file contents above, then read_file any additional paths if needed, and report_finding for each violation.
"""


async def _record_violation(
    session,
    discovered: list[Violation],
    seen_keys: set[tuple],
    violation: Violation,
    on_event,
    scan_id: str,
    scan_uuid: uuid.UUID,
):
    key = (violation.file_path, violation.category, violation.description)
    if key in seen_keys:
        return

    seen_keys.add(key)
    discovered.append(violation)
    session.add(violation)
    await _emit_event(on_event, {
        "type": "VIOLATION_FOUND",
        "scan_id": scan_id,
        "violation": {
            "id": str(violation.id),
            "service": violation.service,
            "severity": violation.severity,
            "status": violation.status,
            "category": violation.category,
            "description": violation.description,
            "file_path": violation.file_path,
            "line_number": violation.line_number,
            "remediation": violation.remediation,
        },
    }, session, scan_uuid)


async def _merge_deterministic_findings(
    repo_path: str,
    service_name: str,
    scan_id: str,
    scan_uuid: uuid.UUID,
    session,
    discovered: list[Violation],
    seen_keys: set[tuple],
    on_event,
):
    """Rule-based fallback so scans never return 0 when violations exist."""
    for payload in scan_repository(repo_path):
        violation = _build_violation(
            scan_uuid=scan_uuid,
            service_name=service_name,
            file_path=payload.get("file_path"),
            category=payload.get("category", "CRYPTOGRAPHIC"),
            finding=payload.get("finding", "compliance_issue"),
            description=payload.get("description") or "Compliance violation detected",
            remediation=payload.get("remediation") or "Review and fix the identified issue.",
            policy_ref=payload.get("policy", "deterministic/compliance"),
            line_number=payload.get("line_number"),
            severity=payload.get("severity"),
        )
        await _record_violation(session, discovered, seen_keys, violation, on_event, scan_id, scan_uuid)


async def run_scan(
    scan_run_id: str,
    repo_path: str,
    service_name: str,
    standards: list[str],
    on_tool_call=None,
    on_violation=None,
    on_event=None,
):
    scan_uuid = uuid.UUID(scan_run_id)
    discovered: list[Violation] = []
    seen_keys: set[tuple] = set()

    claw = ArmorClaw(
        client=armoriq,
        agent_name="ComplianceGuard-Scanner",
        tool_policy=ToolCallPolicy(
            allowed_tools=["list_files", "read_file", "parse_dependency", "report_finding"],
            blocked_tools=["execute_shell", "write_file", "network_request"],
            require_intent_match=True,
        ),
    )
    tools = build_scan_tools(repo_path)

    async with async_session() as session:
        await session.execute(
            update(ScanRun).where(ScanRun.id == scan_uuid).values(status="RUNNING")
        )
        await session.commit()

        await _emit_event(on_event, {
            "type": "SCAN_STARTED",
            "scan_id": scan_run_id,
            "service": service_name,
            "standards": standards,
            "mode": "llm-only" if not settings.ARMORIQ_ENABLED else "llm+armoriq",
        }, session, scan_uuid)

        async def handle_tool_event(event: dict):
            decision = event.get("decision", "ALLOW")
            await _emit_audit(session, scan_uuid, event["tool"], event["intent"], decision)
            await _emit_event(on_event, event, session, scan_uuid)
            if on_tool_call:
                await on_tool_call(event)

        async def handle_agent_violation(payload: dict):
            finding = payload.get("finding") or "compliance_issue"
            violation = _build_violation(
                scan_uuid=scan_uuid,
                service_name=service_name,
                file_path=payload.get("file_path"),
                category=payload.get("category", "CRYPTOGRAPHIC"),
                finding=finding,
                description=payload.get("description") or "Compliance violation detected",
                remediation=payload.get("remediation") or "Review and fix the identified issue.",
                policy_ref="llm/compliance",
                line_number=payload.get("line_number"),
                severity=payload.get("severity"),
            )
            await _record_violation(session, discovered, seen_keys, violation, on_event, scan_run_id, scan_uuid)
            if on_violation:
                await on_violation(violation)

        try:
            async for event in claw.run_async(
                scan_run_id=scan_run_id,
                prompt=build_scan_prompt(repo_path, service_name, standards),
                tools=tools,
                system=SYSTEM_PROMPT,
                on_tool_call=handle_tool_event,
                on_violation=handle_agent_violation,
            ):
                if event["type"] in {"SCAN_STARTED", "SCAN_COMPLETED"}:
                    continue
                if event["type"] == "TOOL_CALLED":
                    continue
                if event["type"] == "VIOLATION_FOUND":
                    continue
                await _emit_event(on_event, event, session, scan_uuid)

            llm_count = len(discovered)
            await _merge_deterministic_findings(
                repo_path, service_name, scan_run_id, scan_uuid, session, discovered, seen_keys, on_event,
            )
            if len(discovered) > llm_count:
                await _emit_event(on_event, {
                    "type": "AGENT_SUMMARY",
                    "scan_id": scan_run_id,
                    "summary": (
                        f"LLM reported {llm_count} violation(s). "
                        f"Rule-based scan added {len(discovered) - llm_count} more."
                    ),
                }, session, scan_uuid)

            compliance_score = max(0, 100 - (len(discovered) * 10))
            await session.execute(
                update(ScanRun).where(ScanRun.id == scan_uuid).values(
                    status="COMPLETED",
                    completed_at=datetime.now(timezone.utc),
                    services_scanned=1,
                    violations_found=len(discovered),
                    compliance_score=compliance_score,
                )
            )
            await _emit_audit(session, scan_uuid, "run_scan", f"Completed LLM scan for {service_name}")
            await _emit_event(on_event, {
                "type": "SCAN_COMPLETED",
                "scan_id": scan_run_id,
                "summary": {
                    "violations_found": len(discovered),
                    "services_scanned": 1,
                    "compliance_score": compliance_score,
                },
            }, session, scan_uuid)
            await session.commit()
        except Exception as exc:
            await session.execute(
                update(ScanRun).where(ScanRun.id == scan_uuid).values(
                    status="FAILED",
                    completed_at=datetime.now(timezone.utc),
                )
            )
            await _emit_event(on_event, {
                "type": "SCAN_FAILED",
                "scan_id": scan_run_id,
                "error": str(exc),
            }, session, scan_uuid)
            await session.commit()
            raise
