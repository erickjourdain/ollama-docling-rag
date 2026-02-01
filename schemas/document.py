from pydantic import BaseModel, Field
from datetime import datetime

from .user import UserOut

class DocumentCreate(BaseModel):
    """Modèle document pour la création dans la base de données"""
    filename: str = Field(..., description="Nom du fichier")
    collection_id: int = Field(..., description="id de collection liée au document")

class DocumentOut(BaseModel):
    """Modèle document pour stockage des données en base"""
    id: str = Field(..., description="ID du document")
    filename: str = Field(..., description="Nom du fichier")
    collection_id: str = Field(..., description="ID de la collection de rattachement du document")
    date_insertion: datetime = Field(..., description="Date d'insertion dans la base")
    creator: UserOut = Field(..., description="Utilisateur ayant inséré le fichier")
    
    class Config:
        from_attributes = True 