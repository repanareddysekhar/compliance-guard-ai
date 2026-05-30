from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator

class Settings(BaseSettings):
    # ArmorIQ SDK
    ARMORIQ_API_KEY: str
    ARMORIQ_ENFORCEMENT_MODE: str = "blocking"
    ARMORIQ_CRYPTOGRAPHIC_AUDIT: bool = True

    # LLM Provider (defaults to local Ollama for POC)
    LLM_PROVIDER: str = "ollama"                 # ollama | openai | anthropic
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "llama3.2:3b"
    LLM_MAX_TOKENS: int = 4096
    LLM_MAX_TURNS: int = 60
    LLM_TIMEOUT_SECONDS: float = 120.0
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ARMORIQ_MODE: str = "local"
    ARMORIQ_USER_ID: str = "complianceguard-system"

    # Database
    DATABASE_URL: str

    # API
    COMPLIANCEGUARD_API_KEY: str
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except:
                    pass
            return [i.strip() for i in v.split(",")]
        return v

    # OPA
    OPA_POLICY_PATH: str = "./backend/policies/"

    # Feature Flags
    ENABLE_AUTO_FIX: bool = False
    ENABLE_MULTI_TENANT: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
