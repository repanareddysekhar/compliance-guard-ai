from armoriq import ArmorIQClient, PolicyConfig
from backend.settings import settings

armoriq = ArmorIQClient(
    api_key=settings.ARMORIQ_API_KEY,
    policy_config=PolicyConfig(
        enforcement_mode=settings.ARMORIQ_ENFORCEMENT_MODE,
        audit_log_enabled=True,
        cryptographic_audit=settings.ARMORIQ_CRYPTOGRAPHIC_AUDIT,
        intent_verification=True,
    )
)
