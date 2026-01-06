from typing import Iterable
from fastapi import APIRouter, HTTPException, status

from models import CollectionCreate
from services import DbService

router_collection = APIRouter(prefix="/collections", tags=["Collections"])

@router_collection.get(
        "",
        summary="Liste des collections / tables",
        description="Récupère l'ensemble des collections / tables de la base de données"
)
async def get_collections() -> Iterable[str]:
    try:
        db_service = DbService()
        return db_service.list_tables()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la récupération des tables: {str(e)}"
        )
    
@router_collection.post(
        "",
        summary="Créer une collection / table",
        description="Création d'une nouvelle collection / table dans la base de données vectorielle"
)
async def new_collection(req: CollectionCreate) -> bool:
    try:
        db_service = DbService()
        tables = db_service.list_tables()
        if req.collection_name in tables:
            raise Exception
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La collection existe déjà dans la base de données"
        )
    
    try:
        db_service.create_table(req.collection_name)
        return True
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la création de la collection / table: {str(e)}"
        )

@router_collection.delete(
        "",
        summary="Supprime une collection / table",
        description="""Supression d'une collection / table de la base de données""",
)
async def delete_collection(collection_name: str) -> bool:
    try:
        db_service = DbService()
        db_service.delete_table(collection_name=collection_name)
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la suppression de la table: {str(e)}"
        )
