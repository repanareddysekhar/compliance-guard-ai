from armoriq_sdk import ArmorIQClient

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

class OPARunner:
    def __init__(self, client: ArmorIQClient, policy_bundle_path: str, decision_log: bool = True):
        self.client = client
        self.policy_bundle_path = policy_bundle_path
        self.decision_log = decision_log

    async def evaluate(self, policy: str, input: dict):
        return type("obj", (object,), {"allowed": True, "violations": []})
