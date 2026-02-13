import re

from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from .user import UserOut

class CollectionCreate(BaseModel):
    """Modèle collection pour la création dans la base de données"""
    name: str = Field(
        ...,
        min_length=5, 
        max_length=25,
        description="Nom de la collection (caractères spéciaux et espaces interdits hors _ et -)",
    )
    description: str | None = Field(..., description="Description du contenu de la collection")

    @field_validator('name')
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        # Regex : ^[a-zA-Z0-9]+$ 
        # Signifie : commence par début de ligne (^), 
        # contient uniquement des lettres ou chiffres ([a-zA-Z0-9]+), 
        # se termine ($).
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                "Le nom de la collection ne doit contenir que des lettres et des chiffres (pas d'espaces ni de caractères spéciaux)."
            )
        return v

class CollectionModel(BaseModel):
    """Modèle collection pour stockage des données en base"""
    id: str = Field(..., description="ID de la collection")
    name: str = Field(..., description="Nom de la collection")
    description: str | None = Field(..., description="Description du contenu de la collection")
    creator: UserOut = Field(..., description="Créateur de la collection")
    date_creation: datetime = Field(..., description="Date de création de la collection")

    class Config:
        from_attributes = True

