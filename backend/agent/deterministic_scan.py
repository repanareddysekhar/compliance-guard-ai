"""Rule-based compliance scan used as fallback and to validate LLM findings."""

import os
import re

from backend.agent.fips_rules import BANNED_CRYPTO, CODE_EXTENSIONS

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}

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


def _find_banned_crypto(content: str, patterns: list[str]) -> tuple[int | None, str] | None:
    for pattern in patterns:
        compiled = re.compile(pattern, re.IGNORECASE)
        line_number = _line_number(content, compiled)
        if line_number:
            return line_number, pattern
    return None


def scan_repository(repo_path: str) -> list[dict]:
    """Return normalized finding dicts for all rule-based violations in a repo."""
    findings: list[dict] = []
    abs_repo = os.path.abspath(repo_path)

    for root, dirs, files in os.walk(abs_repo):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in files:
            file_path = os.path.join(root, filename)
            rel_path = os.path.relpath(file_path, abs_repo).replace(os.sep, "/")

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                    content = handle.read()
            except OSError:
                continue

            lower_content = content.lower()
            ext = os.path.splitext(filename)[1].lower()

            if ext in CODE_EXTENSIONS:
                for _, data in BANNED_CRYPTO.items():
                    match = _find_banned_crypto(content, data["patterns"])
                    if not match:
                        continue
                    line_number, _ = match
                    findings.append({
                        "file_path": rel_path,
                        "category": "CRYPTOGRAPHIC",
                        "finding": data["finding"],
                        "description": data["description"],
                        "remediation": data["remediation"],
                        "policy": data["policy"],
                        "line_number": line_number,
                        "severity": "HIGH",
                        "source": "deterministic",
                    })

            if filename == "Dockerfile":
                if ":latest" in content:
                    findings.append({
                        "file_path": rel_path,
                        "category": "CONTAINER",
                        "finding": "latest_tag",
                        "description": "Docker image uses the mutable 'latest' tag.",
                        "remediation": "Pin the image to a specific version tag.",
                        "policy": "compliance/container",
                        "line_number": _line_number(content, ":latest"),
                        "severity": "LOW",
                        "source": "deterministic",
                    })
                if "healthcheck" not in lower_content:
                    findings.append({
                        "file_path": rel_path,
                        "category": "CONTAINER",
                        "finding": "no_healthcheck",
                        "description": "Dockerfile does not define a HEALTHCHECK.",
                        "remediation": "Add a HEALTHCHECK instruction to verify container health.",
                        "policy": "compliance/container",
                        "line_number": None,
                        "severity": "MED",
                        "source": "deterministic",
                    })
                if "user " not in lower_content or "user root" in lower_content:
                    findings.append({
                        "file_path": rel_path,
                        "category": "CONTAINER",
                        "finding": "root_user",
                        "description": "Container appears to run as root.",
                        "remediation": "Create and switch to a non-root user with USER appuser.",
                        "policy": "compliance/container",
                        "line_number": _line_number(content, "USER"),
                        "severity": "HIGH",
                        "source": "deterministic",
                    })

            if filename == "requirements.txt":
                for line in content.splitlines():
                    dep = line.strip()
                    if not dep or dep.startswith("#") or "==" not in dep:
                        continue
                    pkg = dep.split("==", 1)[0].lower()
                    if pkg in OUTDATED_DEPENDENCIES:
                        findings.append({
                            "file_path": rel_path,
                            "category": "DEPENDENCY",
                            "finding": "outdated",
                            "description": f"Dependency '{dep}' is outdated or known to be risky.",
                            "remediation": OUTDATED_DEPENDENCIES[pkg],
                            "policy": "compliance/dependency",
                            "line_number": _line_number(content, dep),
                            "severity": "LOW",
                            "source": "deterministic",
                        })

    return findings
