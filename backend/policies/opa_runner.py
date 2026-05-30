from backend.armoriq_shims import OPARunner
from backend.armoriq_client import armoriq
from backend.settings import settings

CRYPTOGRAPHIC_BANNED = {"MD5", "SHA1", "DES", "3DES", "RC4", "TLSV1.0", "TLSV1.1", "DISABLED_CERT_VALIDATION"}


class PolicyEvaluationResult:
    def __init__(self, allowed: bool, violations: list[str]):
        self.allowed = allowed
        self.violations = violations


def _normalize_algorithm(value: str) -> str:
    return value.upper().replace("-", "").replace("_", "").replace(" ", "")


def _evaluate_cryptographic_policy(input_data: dict) -> PolicyEvaluationResult:
    algorithm = _normalize_algorithm(str(input_data.get("algorithm", "")))
    normalized_banned = {_normalize_algorithm(item) for item in CRYPTOGRAPHIC_BANNED}

    if algorithm in normalized_banned:
        raw = input_data.get("algorithm", "unknown")
        return PolicyEvaluationResult(
            allowed=False,
            violations=[
                f"Non-FIPS algorithm detected: {raw}. Use SHA-256 or AES-256-GCM instead."
            ],
        )

    return PolicyEvaluationResult(allowed=True, violations=[])


opa = OPARunner(
    client=armoriq,
    policy_bundle_path=settings.OPA_POLICY_PATH,
    decision_log=True,
)


async def evaluate_policy(policy: str, input_data: dict):
    if policy.endswith("cryptographic") or policy == "compliance/cryptographic":
        return _evaluate_cryptographic_policy(input_data)
    return await opa.evaluate(policy=policy, input=input_data)
