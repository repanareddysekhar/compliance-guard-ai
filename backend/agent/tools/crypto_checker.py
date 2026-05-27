from armoriq.armorclaw import Tool

BANNED_ALGORITHMS = ["MD5", "SHA1", "DES", "3DES", "RC4"]
FIPS_APPROVED = ["SHA-256", "SHA-384", "SHA-512", "AES-256", "RSA-2048+", "ECDSA-P256+"]

def check_crypto_impl(code_snippet: str) -> dict:
    found_violations = []
    for algo in BANNED_ALGORITHMS:
        if algo.lower() in code_snippet.lower():
            found_violations.append({
                "algorithm": algo,
                "compliant": False,
                "reason": f"{algo} is not FIPS 140-3 approved",
                "suggested": "Use SHA-256 or AES-256-GCM"
            })
    return {"violations": found_violations, "is_compliant": len(found_violations) == 0}

tool = Tool(
    name="check_crypto",
    description="Check a code snippet for non-compliant cryptographic algorithm usage",
    func=check_crypto_impl,
    parameters={
        "code_snippet": {"type": "string", "description": "Source code to analyze"}
    }
)
