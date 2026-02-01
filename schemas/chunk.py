from typing import List
from pydantic import BaseModel, Field

class ChunkMetada(BaseModel):
    """Modèle description des metadata d'un chunk"""
    document_id: str = Field(..., description="ID du document")
    filename: str = Field(..., description="nom du fichier dont est issu le chiunk")
    pages: str | None = Field(..., description="La liste des pages concernées par le chunk")
    section: str | None = Field(..., description="Le titre de la section contenant le chunck")

class Chunk(BaseModel):
    text: str = Field(..., description="Chunk au format texte")
    metadata: ChunkMetada = Field(..., description="Les metada du chunk")

class ChunkingResponse(BaseModel):
    chunks: List[Chunk] = Field(..., description="Liste des chunks")
    elapsed_time: float = Field(..., description="Durée de l'opération du chunking")