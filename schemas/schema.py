from datetime import datetime
from pydantic import BaseModel, Field
from lancedb.embeddings import get_registry
from lancedb.pydantic import LanceModel, Vector
from typing import List, Optional
from pathlib import Path
from docling_core.types.doc.document import DoclingDocument

from core.config import settings

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

class ChunkMetada(LanceModel):
    """Les métadonnéess à stocker dans la base vectorielles"""
    filename: str | None = Field(..., description="Le nom du fichier ont est extrait le chucnk")
    page_numbers: List[int] | None = Field(..., description="La liste des pages concernées par le chunk")
    context: str | None = Field(..., description="Le titre de la section contenant le chunck")

class ChunkWithoutVector(LanceModel):
    """Chunk incluant le contenu et les métadonnées"""
    text: str = Field(..., description="Le contenu texte du chunk")
    metadata: ChunkMetada

class ChunkingResponse(LanceModel):
    """Réponse chunking et embeddings"""
    chunks: List[ChunkWithoutVector]
    embedding_time: float = Field(..., description="Durée de l'embedding")
    
func = get_registry().get("ollama").create(name=settings.llm_embedding_model)

class Chunks(LanceModel):
    """Chunk pour stockage en base de données"""
    text: str = func.SourceField()
    vector: Vector(func.ndims()) = func.VectorField()  # type: ignore
    metadata: ChunkMetada

class Document(LanceModel):
    """Modèle document pour stockage des données"""
    filename: str = Field(..., description="Le nom du fichier")
    collection: str = Field(..., description="Nom de la collection liée au document")
    date: datetime = Field(..., description="Date d'insertion dans la base")
    user: str = Field(..., description="Nom de l'utilisateur ayant inséré le fichier")

class CollectionCreate(BaseModel):
    """Requête pour la création d'une collection"""
    collection_name: str = Field(..., description="Nom de la collection à créer")

class CollectionInfoResponse(BaseModel):
    """Information sur la collection"""
    name: str = Field(..., description="Nom de la collection")
    nb_docs: int = Field(..., description="Nombre de documents dans la collection")

class QueryRequest(BaseModel):
    """Requête pour l'interrogation de la base de données"""
    query: str = Field(..., description="La requête à éxecuter")
    collection_name: str = Field(..., description="La collection à interroger")
    model: Optional[str] = Field(None, description=f"Le modèle à utiliser pour la requête par défaut '{settings.llm_model}'")

class Model(BaseModel):
    """Modèle de gestion des modèles LLM disponibles"""
    nom: str | None = Field(..., description="Le nom du modèle")
    embed: bool = Field(..., description="Modèle de type embedding")

class HealthResponse(BaseModel):
    """État de santé de l'API"""
    api: str = Field(..., description="État de l'API FastAPI")
    llm: str = Field(..., description="État du serveur Ollama")
    db: str = Field(..., description="État Base de données")
    models_available: list[Model] = Field(..., description="Modèles Ollama disponibles")