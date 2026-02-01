from pydantic import BaseModel
from typing import List

from schemas.schema import Model


class OllamaHealth(BaseModel):
    """Modèle état du service Ollama"""
    ok: bool
    models: List[Model] | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Modèle état des services"""
    status: str
    sqlite: bool
    chromadb: bool
    ollama: OllamaHealth
