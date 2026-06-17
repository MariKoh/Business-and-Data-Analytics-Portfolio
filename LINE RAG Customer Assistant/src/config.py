"""Centralised, validated configuration loaded from environment / .env.

One typed settings object (instead of scattered os.getenv calls) keeps config
testable, documented, and fast-failing at startup.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenRouter (LLM)
    openrouter_api_key: str = "changeme"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Pinecone (vector DB)
    pinecone_api_key: str = "changeme"
    pinecone_index: str = "moomhom-rag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_namespace: str = "moomhom"

    # Embeddings
    embedding_model: str = "intfloat/multilingual-e5-base"
    embedding_dim: int = 768

    # Retrieval
    top_k: int = 4
    chunk_size: int = 600
    chunk_overlap: int = 80
    score_threshold: float = 0.80

    # LINE
    line_channel_access_token: str = ""
    line_channel_secret: str = ""

    # Human handoff
    handoff_hours: float = 3.0
    handoff_triggers: str = (
        "talk to human,talk to a human,talk to agent,speak to a human,"
        "คุยกับแอดมิน,ขอคุยกับแอดมิน,คุยกับคน,ขอคุยกับคน,ติดต่อแอดมิน,ขอแอดมิน,คุยกับเจ้าหน้าที่"
    )
    resume_triggers: str = "talk to bot,คุยกับบอท,เปิดบอท,กลับมาคุยกับบอท,คุยกับน้องหอม"
    handoff_notify_on_resume: bool = True

    # App
    app_env: str = "local"
    log_level: str = "INFO"
    assistant_language: str = "th"

    @property
    def handoff_trigger_list(self) -> list[str]:
        return [t.strip().lower() for t in self.handoff_triggers.split(",") if t.strip()]

    @property
    def resume_trigger_list(self) -> list[str]:
        return [t.strip().lower() for t in self.resume_triggers.split(",") if t.strip()]


_settings: Settings | None = None


def get_settings() -> Settings:
    """Singleton accessor so config is parsed once per process."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
