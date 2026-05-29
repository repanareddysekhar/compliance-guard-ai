import hashlib
import os
import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from backend.db.database import async_session
from backend.db.models import AuditEvent, ScanRun, Violation
from backend.engine.violation_engine import score_violation

# Load system prompt
SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt")
with open(SYSTEM_PROMPT_PATH, "r") as f:
    SYSTEM_PROMPT = f.read()

BANNED_CRYPTO = {
    "md5": {
        "finding": "MD5",
        "description": "Non-FIPS algorithm MD5 detected.",
        "remediation": "Replace MD5 with SHA-256 or SHA-512 for hashing operations.",
        "policy": "compliance/cryptographic",
    },
    "sha1": {
        "finding": "SHA1",
        "description": "Non-FIPS algorithm SHA1 detected.",
        "remediation": "Replace SHA1 with SHA-256 or stronger approved hashing.",
        "policy": "compliance/cryptographic",
    },
    "des": {
        "finding": "DES",
        "description": "Weak DES encryption detected.",
        "remediation": "Use AES-256-GCM for symmetric encryption.",
        "policy": "compliance/cryptographic",
    },
    "rc4": {
        "finding": "RC4",
        "description": "Weak RC4 cipher detected.",
        "remediation": "Use AES-256-GCM or ChaCha20-Poly1305 instead.",
        "policy": "compliance/cryptographic",
    },
}

OUTDATED_DEPENDENCIES = {
    "flask": "Upgrade to Flask 3.x or latest maintained version.",
    "requests": "Upgrade to the latest patched Requests release.",
    "cryptography": "Upgrade to the latest supported cryptography package.",
    "pyyaml": "Upgrade to the latest patched PyYAML release.",
}


def _line_number(content: str, needle: str) -> int | None:
    for idx, line in enumerate(content.splitlines(), start=1):
        if needle.lower() in line.lower():
            return idx
    return None


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def _emit_event(on_event, payload: dict):
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


def _build_violation(scan_uuid: uuid.UUID, service_name: str, file_path: str, category: str, finding: str,
                     description: str, remediation: str, policy_ref: str, line_number: int | None = None) -> Violation:
    severity, status = score_violation(category, finding)
    return Violation(
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
    return f"""
    Start a compliance scan for the service '{service_name}' located at '{repo_path}'.
    Check against the following standards: {', '.join(standards)}.
    
    1. List the files in the directory.
    2. Scan each file for security and compliance issues.
    3. Check dependencies for known vulnerabilities or banned packages.
    4. Check for insecure cryptographic practices.
    5. Evaluate all findings against the relevant OPA policies.
    """

async def run_scan(scan_run_id: str, repo_path: str, service_name: str, standards: list[str],
                   on_tool_call=None, on_violation=None, on_event=None):
    scan_uuid = uuid.UUID(scan_run_id)
    discovered: list[Violation] = []
    files_scanned = 0

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
        })

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}]
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, repo_path)
                files_scanned += 1

                await _emit_audit(session, scan_uuid, "read_file", f"Inspecting {rel_path}")
                await _emit_event(on_event, {
                    "type": "TOOL_CALLED",
                    "scan_id": scan_run_id,
                    "tool": "read_file",
                    "intent": f"Inspecting {rel_path}",
                    "decision": "ALLOW",
                })

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                        content = handle.read()
                except OSError:
                    continue

                lower_content = content.lower()

                for token, data in BANNED_CRYPTO.items():
                    if token in lower_content:
                        violation = _build_violation(
                            scan_uuid=scan_uuid,
                            service_name=service_name,
                            file_path=rel_path,
                            category="CRYPTOGRAPHIC",
                            finding=data["finding"],
                            description=data["description"],
                            remediation=data["remediation"],
                            policy_ref=data["policy"],
                            line_number=_line_number(content, token),
                        )
                        discovered.append(violation)
                        session.add(violation)
                        await _emit_event(on_event, {
                            "type": "VIOLATION_FOUND",
                            "scan_id": scan_run_id,
                            "violation": {
                                "id": str(violation.id),
                                "service": service_name,
                                "severity": violation.severity,
                                "status": violation.status,
                                "category": violation.category,
                                "description": violation.description,
                                "file_path": rel_path,
                                "line_number": violation.line_number,
                                "remediation": violation.remediation,
                            },
                        })

                if filename == "Dockerfile":
                    if ":latest" in content:
                        violation = _build_violation(
                            scan_uuid, service_name, rel_path, "CONTAINER", "latest_tag",
                            "Docker image uses the mutable 'latest' tag.", "Pin the image to a specific version tag.",
                            "compliance/container", _line_number(content, ":latest")
                        )
                        discovered.append(violation)
                        session.add(violation)
                    if "healthcheck" not in lower_content:
                        violation = _build_violation(
                            scan_uuid, service_name, rel_path, "CONTAINER", "no_healthcheck",
                            "Dockerfile does not define a HEALTHCHECK.", "Add a HEALTHCHECK instruction to verify container health.",
                            "compliance/container"
                        )
                        discovered.append(violation)
                        session.add(violation)
                    if "user " not in lower_content or "user root" in lower_content:
                        violation = _build_violation(
                            scan_uuid, service_name, rel_path, "CONTAINER", "root_user",
                            "Container appears to run as root.", "Create and switch to a non-root user with USER appuser.",
                            "compliance/container", _line_number(content, "USER")
                        )
                        discovered.append(violation)
                        session.add(violation)

                if filename == "requirements.txt":
                    await _emit_audit(session, scan_uuid, "parse_dependency", f"Parsing dependency manifest {rel_path}")
                    await _emit_event(on_event, {
                        "type": "TOOL_CALLED",
                        "scan_id": scan_run_id,
                        "tool": "parse_dependency",
                        "intent": f"Parsing dependency manifest {rel_path}",
                        "decision": "ALLOW",
                    })
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
                            discovered.append(violation)
                            session.add(violation)

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
        await _emit_audit(session, scan_uuid, "run_scan", f"Completed scan for {service_name}")
        await session.commit()

    await _emit_event(on_event, {
        "type": "SCAN_COMPLETED",
        "scan_id": scan_run_id,
        "summary": {
            "violations_found": len(discovered),
            "services_scanned": 1,
            "compliance_score": compliance_score,
        },
    })
