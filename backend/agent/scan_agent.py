import hashlib
import os
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from backend.db.database import async_session
from backend.db.models import AuditEvent, ScanLog, ScanRun, Violation
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
        "patterns": [
            r"\bhashlib\.md5\s*\(",
            r"\bmd5\s*\(",
            r"\bcreateHash\s*\(\s*['\"]md5['\"]",
            r"\bMessageDigest\.getInstance\s*\(\s*['\"]MD5['\"]",
            r"\bCryptoJS\.MD5\s*\(",
            r"\bMD5\.Create\s*\(",
        ],
    },
    "sha1": {
        "finding": "SHA1",
        "description": "Non-FIPS algorithm SHA1 detected.",
        "remediation": "Replace SHA1 with SHA-256 or stronger approved hashing.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bhashlib\.sha1\s*\(",
            r"\bsha1\s*\(",
            r"\bcreateHash\s*\(\s*['\"]sha1['\"]",
            r"\bMessageDigest\.getInstance\s*\(\s*['\"]SHA-?1['\"]",
            r"\bCryptoJS\.SHA1\s*\(",
            r"\bSHA1\.Create\s*\(",
        ],
    },
    "des": {
        "finding": "DES",
        "description": "Weak DES encryption detected.",
        "remediation": "Use AES-256-GCM for symmetric encryption.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bcreateCipher(?:iv)?\s*\(\s*['\"]des(?:-|['\"])",
            r"\bCipher\.getInstance\s*\(\s*['\"]DES(?:/|['\"])",
            r"\bDES\.Create\s*\(",
            r"\bCryptoJS\.DES\.",
            r"\balgorithms\.DES\b",
        ],
    },
    "rc4": {
        "finding": "RC4",
        "description": "Weak RC4 cipher detected.",
        "remediation": "Use AES-256-GCM or ChaCha20-Poly1305 instead.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bARC4\.new\s*\(",
            r"\bcreateCipher(?:iv)?\s*\(\s*['\"]rc4['\"]",
            r"\bCipher\.getInstance\s*\(\s*['\"]RC4['\"]",
            r"\bCryptoJS\.RC4\.",
        ],
    },
    "tls10": {
        "finding": "TLSv1.0",
        "description": "Deprecated TLS 1.0 protocol detected.",
        "remediation": "Disable TLS 1.0 and require TLS 1.2 or TLS 1.3 with approved cipher suites.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bssl\.PROTOCOL_TLSv1\b",
            r"\bTLSVersion\.TLSv1\b",
            r"\bminimum_version\s*=\s*ssl\.TLSVersion\.TLSv1\b",
            r"\bsecureProtocol\s*:\s*['\"]TLSv1_method['\"]",
        ],
    },
    "tls11": {
        "finding": "TLSv1.1",
        "description": "Deprecated TLS 1.1 protocol detected.",
        "remediation": "Disable TLS 1.1 and require TLS 1.2 or TLS 1.3 with approved cipher suites.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bssl\.PROTOCOL_TLSv1_1\b",
            r"\bTLSVersion\.TLSv1_1\b",
            r"\bminimum_version\s*=\s*ssl\.TLSVersion\.TLSv1_1\b",
            r"\bsecureProtocol\s*:\s*['\"]TLSv1_1_method['\"]",
        ],
    },
    "disabled_cert_validation": {
        "finding": "disabled_cert_validation",
        "description": "TLS certificate validation is disabled.",
        "remediation": "Enable certificate validation, require hostname verification, and trust only approved CA bundles.",
        "policy": "compliance/cryptographic",
        "patterns": [
            r"\bverify\s*=\s*False\b",
            r"\bcheck_hostname\s*=\s*False\b",
            r"\bCERT_NONE\b",
            r"\brejectUnauthorized\s*:\s*false\b",
            r"\bNODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]?0['\"]?",
        ],
    },
}

CODE_EXTENSIONS = {
    ".c", ".cc", ".cpp", ".cs", ".go", ".java", ".js", ".jsx", ".kt", ".mjs", ".php",
    ".py", ".rb", ".rs", ".scala", ".swift", ".ts", ".tsx",
}

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


def _is_code_file(filename: str) -> bool:
    return os.path.splitext(filename)[1].lower() in CODE_EXTENSIONS


def _find_banned_crypto_usage(content: str, patterns: list[str]) -> tuple[int | None, re.Pattern] | None:
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    for pattern in compiled_patterns:
        line_number = _line_number(content, pattern)
        if line_number:
            return line_number, pattern
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


async def _record_violation(session, discovered: list[Violation], violation: Violation, on_event, scan_id: str, scan_uuid: uuid.UUID):
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


def _build_violation(scan_uuid: uuid.UUID, service_name: str, file_path: str, category: str, finding: str,
                     description: str, remediation: str, policy_ref: str, line_number: int | None = None) -> Violation:
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
        }, session, scan_uuid)

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
                }, session, scan_uuid)

                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                        content = handle.read()
                except OSError:
                    continue

                lower_content = content.lower()

                if _is_code_file(filename):
                    for _, data in BANNED_CRYPTO.items():
                        match = _find_banned_crypto_usage(content, data["patterns"])
                        if not match:
                            continue

                        line_number, _ = match
                        violation = _build_violation(
                            scan_uuid=scan_uuid,
                            service_name=service_name,
                            file_path=rel_path,
                            category="CRYPTOGRAPHIC",
                            finding=data["finding"],
                            description=data["description"],
                            remediation=data["remediation"],
                            policy_ref=data["policy"],
                            line_number=line_number,
                        )
                        await _record_violation(session, discovered, violation, on_event, scan_run_id, scan_uuid)

                if filename == "Dockerfile":
                    if ":latest" in content:
                        violation = _build_violation(
                            scan_uuid, service_name, rel_path, "CONTAINER", "latest_tag",
                            "Docker image uses the mutable 'latest' tag.", "Pin the image to a specific version tag.",
                            "compliance/container", _line_number(content, ":latest")
                        )
                        await _record_violation(session, discovered, violation, on_event, scan_run_id, scan_uuid)
                    if "healthcheck" not in lower_content:
                        violation = _build_violation(
                            scan_uuid, service_name, rel_path, "CONTAINER", "no_healthcheck",
                            "Dockerfile does not define a HEALTHCHECK.", "Add a HEALTHCHECK instruction to verify container health.",
                            "compliance/container"
                        )
                        await _record_violation(session, discovered, violation, on_event, scan_run_id, scan_uuid)
                    if "user " not in lower_content or "user root" in lower_content:
                        violation = _build_violation(
                            scan_uuid, service_name, rel_path, "CONTAINER", "root_user",
                            "Container appears to run as root.", "Create and switch to a non-root user with USER appuser.",
                            "compliance/container", _line_number(content, "USER")
                        )
                        await _record_violation(session, discovered, violation, on_event, scan_run_id, scan_uuid)

                if filename == "requirements.txt":
                    await _emit_audit(session, scan_uuid, "parse_dependency", f"Parsing dependency manifest {rel_path}")
                    await _emit_event(on_event, {
                        "type": "TOOL_CALLED",
                        "scan_id": scan_run_id,
                        "tool": "parse_dependency",
                        "intent": f"Parsing dependency manifest {rel_path}",
                        "decision": "ALLOW",
                    }, session, scan_uuid)
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
                            await _record_violation(session, discovered, violation, on_event, scan_run_id, scan_uuid)

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
