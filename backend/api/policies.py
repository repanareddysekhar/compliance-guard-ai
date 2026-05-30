from fastapi import APIRouter
import os
from backend.settings import settings

router = APIRouter()

POLICY_METADATA = {
    "access_control": {
        "description": "Enforces service level authorization requirements and restricts wildcard CORS settings to prevent unauthenticated access and data leaks.",
        "category": "ACCESS_CONTROL",
        "severity": "HIGH",
        "standards": ["SOC 2 CC6.3", "OWASP A01:2021-Broken Access Control"],
        "rules_count": 2,
        "rules_list": [
            "Verify authentication middleware is active on all endpoints.",
            "Verify CORS policies do not use insecure wildcard origin declarations."
        ],
        "remediation": "Configure authentication routing filters and define explicit trusted origin domains in backend middlewares."
    },
    "container": {
        "description": "Validates Dockerfile and Kubernetes definitions to block root-user executions, verify container health checks, and enforce precise image tags.",
        "category": "CONTAINER",
        "severity": "HIGH",
        "standards": ["CIS Docker Benchmark 4.1", "NIST SP 800-190"],
        "rules_count": 3,
        "rules_list": [
            "Block privileged container execution (must run as non-root user).",
            "Verify Dockerfile contains a valid HEALTHCHECK parameter.",
            "Block usage of the 'latest' image tag (must pin to a version/hash)."
        ],
        "remediation": "Add 'USER nonroot' in Dockerfiles, declare HEALTHCHECK instruction, and pin base image tags to specific semantic versions."
    },
    "cryptographic": {
        "description": "Reviews codebase and algorithms to ban deprecated hashes and encryptions (MD5, SHA1, DES, RC4) and ensure FIPS 140-3 approved standards.",
        "category": "CRYPTOGRAPHIC",
        "severity": "HIGH",
        "standards": ["FIPS 140-3", "PCI-DSS v4.0 Requirement 4.2"],
        "rules_count": 5,
        "rules_list": [
            "Ban MD5 usage for cryptographic hash algorithms.",
            "Ban SHA-1 usage for signatures and hashes.",
            "Ban DES/3DES symmetric encryption.",
            "Ban RC4 stream cipher algorithms.",
            "Ban hardcoded cryptographic secrets and keys."
        ],
        "remediation": "Replace weak ciphers with AES-256-GCM, use SHA-256 for integrity verification, and fetch secret keys from environment variables."
    },
    "dependency": {
        "description": "Inspects project manifest files (requirements.txt, package.json) to prevent integration of packages containing critical or high severity vulnerabilities.",
        "category": "DEPENDENCY",
        "severity": "HIGH",
        "standards": ["OWASP A06:2021-Vulnerable and Outdated Components", "NIST SSDF"],
        "rules_count": 2,
        "rules_list": [
            "Block packages with active Critical CVE warnings.",
            "Flag packages with active High CVE warnings."
        ],
        "remediation": "Run 'npm audit fix' or 'pip-audit' to upgrade packages to safe versions that resolve known vulnerabilities."
    }
}

@router.get("/policies")
async def list_policies():
    policy_dir = settings.OPA_POLICY_PATH
    policies = []
    
    if os.path.exists(policy_dir):
        for file in os.listdir(policy_dir):
            if file.endswith(".rego"):
                key = file.replace(".rego", "")
                name = key.replace("_", " ").title()
                meta = POLICY_METADATA.get(key, {
                    "description": "Custom OPA Rego compliance validation rules.",
                    "category": "CUSTOM",
                    "severity": "MED",
                    "standards": ["Compliance Standard"],
                    "rules_count": 1,
                    "rules_list": ["Custom OPA policy evaluations."],
                    "remediation": "Review rego logic."
                })
                policies.append({
                    "id": len(policies) + 1,
                    "name": name,
                    "path": f"compliance/{key}",
                    "status": "ACTIVE",
                    "rules": meta["rules_count"],
                    "description": meta["description"],
                    "category": meta["category"],
                    "severity": meta["severity"],
                    "standards": meta["standards"],
                    "rules_list": meta["rules_list"],
                    "remediation": meta["remediation"]
                })
    
    return policies
