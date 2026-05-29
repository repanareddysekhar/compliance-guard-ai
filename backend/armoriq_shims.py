from armoriq_sdk import ArmorIQClient
import asyncio

class ToolCallPolicy:
    def __init__(self, allowed_tools=None, blocked_tools=None, require_intent_match=True):
        self.allowed_tools = allowed_tools or []
        self.blocked_tools = blocked_tools or []
        self.require_intent_match = require_intent_match

class Tool:
    def __init__(self, name, description, func, parameters=None):
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters or {}

class PolicyConfig:
    def __init__(self, enforcement_mode="blocking", audit_log_enabled=True, cryptographic_audit=True, intent_verification=True):
        self.enforcement_mode = enforcement_mode
        self.audit_log_enabled = audit_log_enabled
        self.cryptographic_audit = cryptographic_audit
        self.intent_verification = intent_verification

class ArmorClaw:
    def __init__(self, client: ArmorIQClient, agent_name: str, tool_policy: ToolCallPolicy):
        self.client = client
        self.agent_name = agent_name
        self.tool_policy = tool_policy

    async def run_async(self, scan_run_id, prompt, tools, system, on_tool_call=None, on_violation=None):
        from backend.db.database import async_session
        from backend.db.models import ScanRun
        from sqlalchemy import update
        import uuid
        from datetime import datetime

        # Small delay to allow WebSocket to connect
        await asyncio.sleep(1)

        yield {"type": "SCAN_STARTED", "service": "ComplianceGuard-Scanner", "scan_id": scan_run_id}
        
        # Update DB status to RUNNING
        async with async_session() as session:
            await session.execute(
                update(ScanRun).where(ScanRun.id == uuid.UUID(scan_run_id)).values(status="RUNNING")
            )
            await session.commit()

        # Mimic autonomous loop
        for tool in tools:
            if on_tool_call:
                event = {"tool": tool.name, "intent": f"Scanning using {tool.name}"}
                await on_tool_call(event)
                yield {"type": "TOOL_CALLED", "tool": tool.name, "intent": event["intent"], "decision": "ALLOW", "scan_id": scan_run_id}
            
            await asyncio.sleep(0.5) # Simulate work
            
        # Update DB status to COMPLETED
        async with async_session() as session:
            await session.execute(
                update(ScanRun).where(ScanRun.id == uuid.UUID(scan_run_id)).values(
                    status="COMPLETED", 
                    completed_at=datetime.now()
                )
            )
            await session.commit()

        yield {"type": "SCAN_COMPLETED", "scan_id": scan_run_id}

class OPARunner:
    def __init__(self, client: ArmorIQClient, policy_bundle_path: str, decision_log: bool = True):
        self.client = client
        self.policy_bundle_path = policy_bundle_path
        self.decision_log = decision_log

    async def evaluate(self, policy: str, input: dict):
        # Shim for OPA evaluation using ArmorIQ policies
        # In reality, this would call the ArmorIQ OPA endpoint
        return type('obj', (object,), {'allowed': True, 'violations': []})
