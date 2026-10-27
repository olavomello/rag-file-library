"""Application configuration using Pydantic Settings.

Configuration is loaded from environment variables and an optional ``.env`` file.
All settings are validated at startup; invalid configuration raises a clear error.
"""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed, validated application settings.

    Field names map to environment variables case-insensitively (e.g. ``API_PORT``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_name: str = "Private RAG"
    app_env: str = "development"

    # --- API / HTTP ---
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # --- Storage paths ---
    chroma_path: str = "./data/chroma"
    upload_dir: str = "./data/uploads"
    jobs_dir: str = "./data/jobs"
    config_dir: str = "./data/config"
    temp_dir: str = "./data/temp"

    # --- Ollama (local AI) ---
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_generation_model: str = "qwen3:0.6b"
    ollama_embedding_model: str = "embeddinggemma"
    ollama_temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    ollama_max_output_tokens: int = Field(default=1024, ge=1)
    ollama_context_window: int = Field(default=4096, ge=256)
    ollama_request_timeout_seconds: float = Field(default=120.0, gt=0.0)

    # --- Uploads ---
    max_upload_size_mb: int = Field(default=25, ge=1)

    # --- Chunking ---
    chunk_size: int = Field(default=500, ge=1)
    chunk_overlap: int = Field(default=75, ge=0)

    # --- Search ---
    search_top_k: int = Field(default=5, ge=1)

    # --- Concurrency ---
    indexing_concurrency: int = Field(default=1, ge=1)
    generation_concurrency: int = Field(default=1, ge=1)

    # --- Logging ---
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Allow CORS origins to be supplied as a comma-separated string."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, value: str) -> str:
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return upper

    @model_validator(mode="after")
    def _validate_chunk_relationship(self) -> Settings:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                "chunk_overlap must be strictly smaller than chunk_size "
                f"(got overlap={self.chunk_overlap}, size={self.chunk_size})"
            )
        return self

    @property
    def max_upload_size_bytes(self) -> int:
        """Maximum upload size expressed in bytes."""
        return self.max_upload_size_mb * 1024 * 1024
