from pydantic import BaseModel, Field

class CollectionFilters(BaseModel):
    name: str | None = Field(None, description="Filtre par nom de collection")
    user: str | None = Field(None, description="Filtre par utilisateur ayant créé la collection")
    limit: int = Field(50, description="Nombre de collections à retourner (max 50)")
    offset: int = Field(0, description="Offset pour la pagination")

class DocumentFilters(BaseModel):
    collection_name: str = Field(..., description="Nom de la collection à laquelle appartiennent les documents")
    limit: int = Field(50, description="Nombre de documents à retourner (max 50)")
    offset: int = Field(0, description="Offset pour la pagination")

class UserFilters(BaseModel):
    search: str | None = Field(None, description="Filtre par nom ou email des utilisateurs")
    is_active: bool| None = Field(None, description="Filtre sur le statut de l'utilisateur")
    limit: int = Field(50, description="Nombre de collections à retourner (max 50)")
    offset: int = Field(0, description="Offset pour la pagination")