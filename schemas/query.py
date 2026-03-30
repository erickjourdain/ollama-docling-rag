from datetime import datetime

from pydantic import BaseModel, Field

class QueryModel(BaseModel):
    """Modèle query pour stockage des données en base"""
    id: str = Field(..., description="ID de la requête")
    user_id: str = Field(..., description="ID de l'utilisateur")
    collection_id: str = Field(..., description="ID de la collection")
    job_id: str = Field(..., description="ID du job de création de la requête")
    question: str = Field(..., description="question posée")
    answer: str = Field(..., description="réponse de la base de connaissance")
    model: str = Field(..., description="Modèle utilisé pour générer la réponse")
    created_at: datetime = Field(..., description="Date et heure de génération de la réponse")

