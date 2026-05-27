from typing import Tuple

SEVERITY_RULES = {
    "CRYPTOGRAPHIC": {
        "MD5":        "HIGH",    # Direct FIPS violation
        "SHA1":       "HIGH",
        "DES":        "HIGH",
        "RC4":        "HIGH",
        "hardcoded_key": "HIGH",
    },
    "DEPENDENCY": {
        "critical_cve": "HIGH",
        "high_cve":     "MED",
        "medium_cve":   "LOW",
        "outdated":     "LOW",
    },
    "CONTAINER": {
        "root_user":        "HIGH",   # Privileged container
        "no_healthcheck":   "MED",
        "latest_tag":       "LOW",
        "expose_all_ports": "MED",
    },
    "ACCESS_CONTROL": {
        "no_auth_middleware": "HIGH",
        "wildcard_cors":      "MED",
        "debug_mode_on":      "MED",
    },
    "HEADER": {
        "missing_hsts":     "MED",
        "missing_csp":      "MED",
        "missing_x_frame":  "LOW",
    }
}

def score_violation(category: str, finding: str) -> Tuple[str, str]:
    severity = SEVERITY_RULES.get(category, {}).get(finding, "LOW")
    status = "BLOCKED" if severity == "HIGH" else "FLAGGED" if severity == "MED" else "REPORTED"
    return severity, status
