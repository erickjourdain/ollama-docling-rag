from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class UserCreate(BaseModel):
    """Modèle utilisateur pour création dans la base de données"""
    username: str = Field(..., description="Nom d'utilisateur")
    email: str = Field(..., description="Adresse e-mail de l'utilisateur")
    password: str =Field(..., description="Mot de passe de l'utilisateur")
    role: Optional[str] = Field(..., description="Role de l'utilisateur")

class UserOut(BaseModel):
    """Modèle utilisateur pour réponse API"""
    id: str = Field(..., description="ID de l'utilisateur")
    username: str = Field(..., description="Nom d'utilisateur")
    email: str = Field(..., description="Adresse e-mail de l'utilisateur")
    created_at: datetime = Field(..., description="Date de création de l'utilisateur")
    role: str = Field(..., description="Role de l'utilisateur")

    class Config:
        from_attributes = True 
