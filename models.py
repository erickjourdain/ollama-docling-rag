from pydantic import BaseModel, Field
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from typing import List
from pathlib import Path
from docling_core.types.doc.document import DoclingDocument

from config import settings

class HealthResponse(BaseModel):
    """État de santé de l'API"""
    api: str = Field(..., description="État de l'API FastAPI")
    ollama: str = Field(..., description="État du serveur Ollama")
    chromadb: str = Field(..., description="État de ChromaDB")
    models_available: List[str] = Field(
        default=[],
        description="Modèles Ollama disponibles"
    )

class ProcessingResponse(BaseModel):
    """Réponse après le traitement d'un PDF"""
    detail: str = Field(..., description="Détail du résultat du traitement")
    success: bool = Field(..., description="Indique si le traitement a réussi") 
    conversion_time: float = Field(..., description="Durée de la conversion pdf to md")
    embedding_time: float = Field(..., description="Durée de l'embedding")

class ConvertPdfResponse(BaseModel):
    """Réponse conversion d'un PDF en Markdown"""
    document: DoclingDocument = Field(..., description="Document docling")
    markdown: Path | str = Field(..., description="Contenu Markdown converti à partir du PDF")
    conversion_time: float = Field(..., description="Durée pour la conversion en secondes")

class ChunkingResponse(BaseModel):
    """Réponse chunking et embeddings"""
    embedding_time: float = Field(..., description="Durée de l'embedding")

class ChunkMetada(LanceModel):
    """Les métadonnéess à stocker dans la base vectorielles"""
    filename: str | None = Field(..., description="Le nom du fichier ont est extrait le chucnk")
    page_numbers: List[int] | None = Field(..., description="La liste des pages concernées par le chunk")
    context: str | None = Field(..., description="Le titre de la section contenant le chunck")

func = get_registry().get("ollama").create(name=settings.ollama_embedding_model)

class Chunks(LanceModel):
    text: str = func.SourceField()
    vector: Vector(func.ndims()) = func.VectorField()  # type: ignore
    metadata: ChunkMetada

class QueryRequest(BaseModel):
    """Requête pour l'interrogation de la base de données"""
    query: str = Field(..., description="La requête à éxecuter")
    collection_name: str = Field(..., description="La collection à interroger")