from armoriq.armorclaw import Tool
from backend.policies.opa_runner import evaluate_policy

async def run_opa_query_impl(policy: str, input_data: dict) -> dict:
    try:
        result = await evaluate_policy(policy, input_data)
        return {
            "allowed": result.allowed,
            "violations": result.violations,
            "policy": policy
        }
    except Exception as e:
        return {"error": str(e)}

tool = Tool(
    name="run_opa_query",
    description="Evaluate a specific OPA policy against a given input data",
    func=run_opa_query_impl,
    parameters={
        "policy": {"type": "string", "description": "The OPA policy to evaluate (e.g., 'compliance/cryptographic')"},
        "input_data": {"type": "object", "description": "The data to evaluate against the policy"}
    }
)
