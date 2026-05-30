import re

from backend.agent.fips_rules import BANNED_ALGORITHMS, BANNED_CRYPTO, FIPS_APPROVED
from backend.armoriq_shims import Tool


def _line_number(content: str, pattern: re.Pattern) -> int | None:
    for idx, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith(("#", "//", "/*", "*", "<!--")):
            continue
        if pattern.search(line):
            return idx
    return None


def check_crypto_impl(code_snippet: str, file_path: str | None = None) -> dict:
    found_violations = []
    seen_findings: set[str] = set()

    for _, data in BANNED_CRYPTO.items():
        for pattern in data["patterns"]:
            compiled = re.compile(pattern, re.IGNORECASE)
            if not compiled.search(code_snippet):
                continue

            finding = data["finding"]
            if finding in seen_findings:
                break

            seen_findings.add(finding)
            found_violations.append({
                "algorithm": finding,
                "finding": finding,
                "compliant": False,
                "reason": data["description"],
                "suggested": data["remediation"],
                "remediation": data["remediation"],
                "policy": data["policy"],
                "file_path": file_path,
                "line_number": _line_number(code_snippet, compiled),
            })
            break

    for algo in BANNED_ALGORITHMS:
        if algo.lower() in code_snippet.lower() and algo not in seen_findings:
            found_violations.append({
                "algorithm": algo,
                "finding": algo,
                "compliant": False,
                "reason": f"{algo} is not FIPS 140-3 approved",
                "suggested": "Use SHA-256 or AES-256-GCM",
                "remediation": "Use SHA-256 or AES-256-GCM",
                "policy": "compliance/cryptographic",
                "file_path": file_path,
                "line_number": None,
            })

    return {
        "violations": found_violations,
        "is_compliant": len(found_violations) == 0,
        "fips_approved_algorithms": FIPS_APPROVED,
    }


tool = Tool(
    name="check_crypto",
    description="Check a code snippet for non-FIPS 140-3 compliant cryptographic algorithm usage",
    func=check_crypto_impl,
    parameters={
        "code_snippet": {"type": "string", "description": "Source code to analyze"},
        "file_path": {
            "type": "string",
            "description": "Optional relative file path for reporting",
            "required": False,
        },
    },
)
