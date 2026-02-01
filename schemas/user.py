from pydantic import BaseModel, Field
from datetime import datetime

class UserCreate(BaseModel):
    """Modèle utilisateur pour création dans la base de données"""
    username: str = Field(..., description="Nom d'utilisateur")
    email: str = Field(..., description="Adresse e-mail de l'utilisateur")

class UserOut(BaseModel):
    """Modèle utilisateur pour gestion des utilisateurs"""
    id: str = Field(..., description="ID de l'utilisateur")
    username: str = Field(..., description="Nom d'utilisateur")
    email: str = Field(..., description="Adresse e-mail de l'utilisateur")
    created_at: datetime = Field(..., description="Date de création de l'utilisateur")
    class Config:
        from_attributes = True 
