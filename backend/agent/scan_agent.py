import hashlib
import os
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from backend.agent.claw_runner import ArmorClaw
from backend.agent.tools.registry import build_scan_tools, discover_scan_files
from backend.armoriq_client import armoriq
from backend.armoriq_shims import ToolCallPolicy
from backend.db.database import async_session
from backend.db.models import AuditEvent, ScanLog, ScanRun, Violation
from backend.engine.violation_engine import score_violation

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()

OUTDATED_DEPENDENCIES = {
    "flask": "Upgrade to Flask 3.x or latest maintained version.",
    "requests": "Upgrade to the latest patched Requests release.",
    "cryptography": "Upgrade to the latest supported cryptography package.",
    "pyyaml": "Upgrade to the latest patched PyYAML release.",
}


def _line_number(content: str, needle: str | re.Pattern) -> int | None:
    for idx, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "//", "/*", "*", "<!--")):
            continue
        if isinstance(needle, re.Pattern) and needle.search(line):
            return idx
        if isinstance(needle, str) and needle.lower() in line.lower():
            return idx
    return None


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
) -> Violation:
    severity, status = score_violation(category, finding)
    return Violation(
        id=uuid.uuid4(),
        scan_run_id=scan_uuid,
        service=service_name,
        severity=severity,
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
    preview = "\n".join(f"- {path}" for path in files[:100])
    extra = f"\n... and {len(files) - 100} more files" if len(files) > 100 else ""

    return f"""Start a compliance scan for the service '{service_name}' located at '{repo_path}'.
Check against these standards: {', '.join(standards)}.

Primary objective: FIPS-140-3 cryptographic compliance.

Repository files to inspect:
{preview}{extra}

Required workflow:
1. Use list_files if you need to explore the repository structure.
2. Use read_file on each relevant source, config, Dockerfile, and dependency manifest.
3. Use check_crypto on code that may contain cryptography, TLS settings, or hashing.
4. For every non-compliant algorithm found, call run_opa_query with policy "compliance/cryptographic".
5. Continue until all relevant files are reviewed, then provide a concise final compliance summary.

Approved examples: SHA-256, SHA-384, SHA-512, AES-256-GCM, RSA-2048+, ECDSA-P256+.
Banned examples: MD5, SHA1, DES, 3DES, RC4, TLS 1.0, TLS 1.1, disabled certificate validation.
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


async def _run_supplemental_scan(
    repo_path: str,
    service_name: str,
    scan_id: str,
    scan_uuid: uuid.UUID,
    session,
    discovered: list[Violation],
    seen_keys: set[tuple],
    on_event,
):
    """Deterministic checks for container and dependency issues after the LLM FIPS pass."""
    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}]
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, repo_path)

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                    content = handle.read()
            except OSError:
                continue

            lower_content = content.lower()

            if filename == "Dockerfile":
                if ":latest" in content:
                    violation = _build_violation(
                        scan_uuid, service_name, rel_path, "CONTAINER", "latest_tag",
                        "Docker image uses the mutable 'latest' tag.", "Pin the image to a specific version tag.",
                        "compliance/container", _line_number(content, ":latest"),
                    )
                    await _record_violation(session, discovered, seen_keys, violation, on_event, scan_id, scan_uuid)
                if "healthcheck" not in lower_content:
                    violation = _build_violation(
                        scan_uuid, service_name, rel_path, "CONTAINER", "no_healthcheck",
                        "Dockerfile does not define a HEALTHCHECK.", "Add a HEALTHCHECK instruction to verify container health.",
                        "compliance/container",
                    )
                    await _record_violation(session, discovered, seen_keys, violation, on_event, scan_id, scan_uuid)
                if "user " not in lower_content or "user root" in lower_content:
                    violation = _build_violation(
                        scan_uuid, service_name, rel_path, "CONTAINER", "root_user",
                        "Container appears to run as root.", "Create and switch to a non-root user with USER appuser.",
                        "compliance/container", _line_number(content, "USER"),
                    )
                    await _record_violation(session, discovered, seen_keys, violation, on_event, scan_id, scan_uuid)

            if filename == "requirements.txt":
                for line in content.splitlines():
                    dep = line.strip()
                    if not dep or dep.startswith("#") or "==" not in dep:
                        continue
                    pkg = dep.split("==", 1)[0].lower()
                    if pkg in OUTDATED_DEPENDENCIES:
                        violation = _build_violation(
                            scan_uuid=scan_uuid,
                            service_name=service_name,
                            file_path=rel_path,
                            category="DEPENDENCY",
                            finding="outdated",
                            description=f"Dependency '{dep}' is outdated or known to be risky.",
                            remediation=OUTDATED_DEPENDENCIES[pkg],
                            policy_ref="compliance/dependency",
                            line_number=_line_number(content, dep),
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
            allowed_tools=["list_files", "read_file", "parse_dependency", "check_crypto", "run_opa_query"],
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
        }, session, scan_uuid)

        async def handle_tool_event(event: dict):
            decision = event.get("decision", "ALLOW")
            await _emit_audit(session, scan_uuid, event["tool"], event["intent"], decision)
            await _emit_event(on_event, event, session, scan_uuid)
            if on_tool_call:
                await on_tool_call(event)

        async def handle_agent_violation(payload: dict):
            finding = payload.get("finding") or payload.get("algorithm") or "policy_violation"
            violation = _build_violation(
                scan_uuid=scan_uuid,
                service_name=service_name,
                file_path=payload.get("file_path"),
                category=payload.get("category", "CRYPTOGRAPHIC"),
                finding=finding,
                description=payload.get("description") or payload.get("reason") or "FIPS violation detected",
                remediation=payload.get("remediation") or payload.get("suggested") or "Use FIPS-approved algorithms.",
                policy_ref=payload.get("policy", "compliance/cryptographic"),
                line_number=payload.get("line_number"),
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

            await _run_supplemental_scan(
                repo_path, service_name, scan_run_id, scan_uuid, session, discovered, seen_keys, on_event,
            )

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
