from pydantic import BaseModel, Field
from datetime import datetime

class JobOut(BaseModel):
    "Modèle Job pour réponse API"
    id: str = Field(..., description="ID du job")
    status: str  = Field(..., description="Statut d'avancement")
    progress: str  = Field(..., description="Etat de traitement courant")
    input_data: str  = Field(..., description="Nom du fichier")
    result: str | None = Field(..., description="Résultat du ttraitement")
    error: str  | None= Field(..., description="Description de l'erreur de traitement")
    created_at: datetime = Field(..., description="Date de début du traitement")
    finished_at: datetime | None = Field(..., description="Date de fin du traitement")

    class Config:
        from_attributes = True
