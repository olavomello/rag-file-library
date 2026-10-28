"""Response schemas for model info endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelPullRequest(BaseModel):
    """Request to download (pull) a model into the local Ollama instance."""

    model: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:/-]+$")


class ModelsStatusResponse(BaseModel):
    generation_model: str
    embedding_model: str
    ollama_available: bool
    generation_available: bool
    embedding_available: bool


class ModelsResponse(ModelsStatusResponse):
    available_models: list[str]
