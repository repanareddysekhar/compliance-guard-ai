from armoriq.opa import OPARunner
from backend.armoriq_client import armoriq
from backend.settings import settings

opa = OPARunner(
    client=armoriq,
    policy_bundle_path=settings.OPA_POLICY_PATH,
    decision_log=True
)

async def evaluate_policy(policy: str, input_data: dict):
    result = await opa.evaluate(
        policy=policy,
        input=input_data
    )
    return result
