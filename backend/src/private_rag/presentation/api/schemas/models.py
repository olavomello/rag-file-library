"""Response schemas for model info endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class ModelsStatusResponse(BaseModel):
    generation_model: str
    embedding_model: str
    ollama_available: bool
    generation_available: bool
    embedding_available: bool


class ModelsResponse(ModelsStatusResponse):
    available_models: list[str]
