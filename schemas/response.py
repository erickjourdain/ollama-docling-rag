from pydantic import BaseModel, Field

from .document import DocumentModel
from .collection import CollectionModel

class ProcessingResponse(BaseModel):
    """Réponse après le traitement d'un PDF"""
    detail: str = Field(..., description="Détail du résultat du traitement")
    success: bool = Field(..., description="Indique si le traitement a réussi") 
    conversion_time: float = Field(..., description="Durée de la conversion pdf to md")
    embedding_time: float = Field(..., description="Durée de l'embedding")

class InsertResponse(BaseModel):
    """Réponse insertion d'un nouveau document"""
    job_id: str = Field(..., description="Identifiant du job d'insertion")

class JobCleaningResponse(BaseModel):
    """Réponse après nettoyage des anciens jobs"""
    message: str = Field(..., description="Message de confirmation du nettoyage")
    deleted: int = Field(..., description="Nombre de jobs supprimés")

class CollectionListResponse(BaseModel):
    """Réponse pour la liste des collections"""
    collections: list[CollectionModel] = Field(..., description="Liste des collections")
    count: int = Field(..., description="Nombre total de collections")

class DocumentListResponse(BaseModel):
    """Réponse pour la liste des documents d'une collection"""
    documents: list[DocumentModel] = Field(..., description="Liste des documents de la collection")
    count: int = Field(..., description="Nombre total de documents dans la collection")