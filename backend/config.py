from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Any


class Settings(BaseSettings):
    azure_openai_endpoint: str = "https://placeholder.openai.azure.com/"
    azure_openai_api_key: str = "placeholder"
    azure_openai_api_version: str = "2025-03-01-preview"
    database_url: str = "sqlite+aiosqlite:///./ccm_hub.db"
    storage_path: str = "./uploads"
    cors_origins: str | list[str] = "http://localhost:5173"
    context_window_messages: int = 20

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"


settings = Settings()
