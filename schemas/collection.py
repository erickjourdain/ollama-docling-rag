from pydantic import BaseModel, Field
from datetime import datetime

from .user import UserOut

class CollectionCreate(BaseModel):
    """Modèle collection pour la création dans la base de données"""
    name: str = Field(..., description="Nom de la collection")
    description: str | None = Field(..., description="Description du contenu de la collection")

class CollectionModel(BaseModel):
    """Modèle collection pour stockage des données en base"""
    id: str = Field(..., description="ID de la collection")
    name: str = Field(..., description="Nom de la collection")
    description: str | None = Field(..., description="Description du contenu de la collection")
    creator: UserOut = Field(..., description="Créateur de la collection")
    date_creation: datetime = Field(..., description="Date de création de la collection")

    class Config:
        from_attributes = True

