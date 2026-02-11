from typing import List, Optional

from ollama import GenerateResponse
from pydantic import BaseModel, Field
from datetime import datetime

class JobInput(BaseModel):
    """Schéma Input Data du Job"""
    query: Optional[str] = Field(None, description="Requête utilisateur")
    model: Optional[str] = Field(None, description="LLM modèle")
    collection: Optional[str] = Field(None, description="Collection interrogée")
    filename: Optional[str] = Field(None, description="Nom du fichier à traiter")
    doc_id: Optional[str] = Field(None, description="Identifiant du document à traiter")
    user: Optional[str] = Field(None, description="Nom de l'utilisateur")

class JobLogOut(BaseModel):
    """Schéma pour une entrée individuelle dans les logs"""
    timestamp: str = Field(..., description="ISO timestamp de l'événement")
    level: str = Field(..., description="Niveau de log (INFO, ERROR, etc.)")
    message: str = Field(..., description="Message descriptif")

class JobOut(BaseModel):
    """Modèle Job pour réponse API"""
    id: str = Field(..., description="ID du job")
    type: str = Field(..., description="Type de job (insertion ou query)")
    status: str  = Field(..., description="Statut d'avancement")
    progress: str  = Field(..., description="Etat de traitement courant")
    logs: List[JobLogOut] = Field(default_factory=list, description="Historique détaillé")
    input_data: JobInput | None  = Field(..., description="Données d'entrée du job")
    result: GenerateResponse | None = Field(..., description="Résultat du traitement")
    error: str  | None= Field(..., description="Description de l'erreur de traitement")
    created_at: datetime = Field(..., description="Date de début du traitement")
    finished_at: datetime | None = Field(..., description="Date de fin du traitement")

    class Config:
        from_attributes = True
