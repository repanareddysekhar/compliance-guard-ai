import logging

from armoriq_sdk import ArmorIQClient
from armoriq_sdk.session import SessionOptions

from backend.armoriq_shims import PolicyConfig
from backend.settings import settings

logger = logging.getLogger(__name__)

policy_config = PolicyConfig(
    enforcement_mode=settings.ARMORIQ_ENFORCEMENT_MODE,
    audit_log_enabled=True,
    cryptographic_audit=settings.ARMORIQ_CRYPTOGRAPHIC_AUDIT,
    intent_verification=True,
)

_armoriq: ArmorIQClient | None = None


def get_armoriq_client() -> ArmorIQClient:
    global _armoriq
    if _armoriq is None:
        _armoriq = ArmorIQClient(
            api_key=settings.ARMORIQ_API_KEY,
            agent_id=settings.ARMORIQ_AGENT_ID,
            user_id=settings.ARMORIQ_USER_ID,
        )
    return _armoriq


# Backwards-compatible module export used by scan_agent
armoriq = get_armoriq_client() if settings.ARMORIQ_ENABLED else None


def get_armoriq_scope():
    """User-scoped client — required for ArmorIQ dashboard attribution."""
    return get_armoriq_client().for_user(settings.ARMORIQ_USER_EMAIL)


def get_armoriq_session():
    """Open an ArmorIQ session that sends token/enforce/audit events to the cloud."""
    scope = get_armoriq_scope()
    return scope.start_session(
        SessionOptions(
            llm=settings.LLM_MODEL,
            default_mcp_name=settings.ARMORIQ_MCP_NAME,
            mode=settings.ARMORIQ_MODE,
            validity_seconds=settings.ARMORIQ_TOKEN_VALIDITY_SECONDS,
        )
    )


async def check_armoriq_health() -> dict:
    if not settings.ARMORIQ_ENABLED:
        return {"status": "disabled", "detail": "ARMORIQ_ENABLED=false — using local LLM-only mode"}

    scope = get_armoriq_scope()
    bootstrap = scope._client.bootstrap()
    return {
        "status": "ok",
        "mode": settings.ARMORIQ_MODE,
        "user_email": settings.ARMORIQ_USER_EMAIL,
        "agent_id": settings.ARMORIQ_AGENT_ID,
        "mcp_name": settings.ARMORIQ_MCP_NAME,
        "registered_mcps": len(bootstrap.get("mcps", []) or bootstrap.get("mcpList", []) or []),
    }
