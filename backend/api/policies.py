from fastapi import APIRouter
import os
from backend.settings import settings

router = APIRouter()

@router.get("/policies")
async def list_policies():
    policy_dir = settings.OPA_POLICY_PATH
    policies = []
    
    if os.path.exists(policy_dir):
        for file in os.listdir(policy_dir):
            if file.endswith(".rego"):
                name = file.replace(".rego", "").replace("_", " ").title()
                policies.append({
                    "id": len(policies) + 1,
                    "name": name,
                    "path": f"compliance/{file.replace('.rego', '')}",
                    "status": "ACTIVE",
                    "rules": "Dynamic"
                })
    
    return policies
