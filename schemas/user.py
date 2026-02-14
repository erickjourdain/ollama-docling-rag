import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

class UserCreate(BaseModel):
    """Modèle utilisateur pour création dans la base de données"""
    username: str = Field(
        ..., 
        description="Nom d'utilisateur",
        min_length=3,
        max_length=50
    )
    email: str = Field(
        ..., 
        description="Adresse e-mail de l'utilisateur",
        min_length=8,
        max_length=128,
    )
    password: str =Field(..., description="Mot de passe de l'utilisateur")
    role: Optional[str] = Field(..., description="Role de l'utilisateur")
    
    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        # 1. Au moins une majuscule
        if not re.search(r'[A-Z]', v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule.")
        
        # 2. Au moins une minuscule
        if not re.search(r'[a-z]', v):
            raise ValueError("Le mot de passe doit contenir au moins une minuscule.")
        
        # 3. Au moins un chiffre
        if not re.search(r'\d', v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre.")
        
        # 4. Au moins un caractère spécial
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Le mot de passe doit contenir au moins un caractère spécial.")
            
        return v

class UserOut(BaseModel):
    """Modèle utilisateur pour réponse API"""
    id: str = Field(..., description="ID de l'utilisateur")
    username: str = Field(..., description="Nom d'utilisateur")
    email: str = Field(..., description="Adresse e-mail de l'utilisateur")
    created_at: datetime = Field(..., description="Date de création de l'utilisateur")
    role: str = Field(..., description="Role de l'utilisateur")

    class Config:
        from_attributes = True

class UserToken(BaseModel):
    """Modèle de token utilisateur pour réponse API"""
    access_token: str = Field(..., description="Token d'accès de l'utilisateur")
    token_type: str = Field(..., description="Type de token (ex: Bearer)")
