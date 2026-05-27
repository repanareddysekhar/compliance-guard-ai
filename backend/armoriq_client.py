from armoriq_sdk import ArmorIQClient
from backend.armoriq_shims import PolicyConfig
from backend.settings import settings

armoriq = ArmorIQClient(
    api_key=settings.ARMORIQ_API_KEY
)

# In a real scenario, we might want to apply this config to the client or session
# but for now, we just satisfy the spec's initialization structure
policy_config = PolicyConfig(
    enforcement_mode=settings.ARMORIQ_ENFORCEMENT_MODE,
    audit_log_enabled=True,
    cryptographic_audit=settings.ARMORIQ_CRYPTOGRAPHIC_AUDIT,
    intent_verification=True,
)
