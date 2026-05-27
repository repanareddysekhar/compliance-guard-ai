from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # ArmorIQ SDK
    ARMORIQ_API_KEY: str
    ARMORIQ_ENFORCEMENT_MODE: str = "blocking"
    ARMORIQ_CRYPTOGRAPHIC_AUDIT: bool = True

    # LLM Provider
    LLM_MODEL: str = "claude-3-5-sonnet-20240620"
    LLM_MAX_TOKENS: int = 4096

    # Database
    DATABASE_URL: str

    # API
    COMPLIANCEGUARD_API_KEY: str
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    # OPA
    OPA_POLICY_PATH: str = "./backend/policies/"

    # Feature Flags
    ENABLE_AUTO_FIX: bool = False
    ENABLE_MULTI_TENANT: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
