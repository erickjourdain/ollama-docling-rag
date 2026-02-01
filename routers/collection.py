from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from depencies.sqlite_session import get_db
from depencies.vector_db import get_vector_db_service
from schemas.document import DocumentOut
from services import CollectionService, DbVectorielleService
from schemas import CollectionOut, CollectionCreate

router_collection = APIRouter(prefix="/collections", tags=["Collections"])

@router_collection.get(
        "",
        summary="Liste des collections / tables",
        description="Récupère l'ensemble des collections / tables de la base de données",
        response_model=list[CollectionOut]
)
async def get_collections(
    limit: int = 50, 
    offset: int = 0, 
    db: AsyncSession = Depends(get_db)
 ) -> list[CollectionOut]:
    try:
        limit = (limit if limit < 50 and limit > 0 else 50)
        offset = (offset if offset > 0 else 0) 
        collections = await CollectionService.list_collections(
            db,
            limit=limit,
            offset=offset
        )
        return [CollectionOut.model_validate(collection) for collection in collections]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la récupération des tables: {str(e)}"
        )
    
@router_collection.post(
        "",
        summary="Créer une collection / table",
        description="Création d'une nouvelle collection / table dans la base de données vectorielle",
        response_model=CollectionOut
)
async def create(
    payload: CollectionCreate,
    db: AsyncSession = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
) -> CollectionOut:
    try:
        await CollectionService.create_collection(
            db=db, 
            vector_db=vector_db,
            name=payload.name,
            description=payload.description,
            user_id="a12b8b9d-e0b0-4e84-a7c0-36da6ec16907"
        )
        collection = await CollectionService.get_by_name(db=db, name=payload.name)
        return CollectionOut.model_validate(collection)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la création de la collection / table: {str(e)}"
        )
    
@router_collection.get(
        "/{collection_name}",
        summary="Information sur une collection",
        description="Retourne les information sur la collection",
        response_model=CollectionOut
)
async def get_collection(
    collection_name: str,
    db: AsyncSession = Depends(get_db)
    ) -> CollectionOut:
    try:
        collection = await CollectionService.get_by_name(db=db, name=collection_name)
        return CollectionOut.model_validate(collection)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la lecture des information sur de la collection / table: {str(e)}"
        )

@router_collection.get(
        "/{collection_name}/documents",
        summary="Liste des documents indexés dans la collection",
        response_model=list[DocumentOut]
)
async def get_collection_documents(
    collection_name: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
) -> list[DocumentOut]:
    try:
        limit = (limit if limit < 50 and limit > 0 else 50)
        offset = (offset if offset > 0 else 0) 
        documents = await CollectionService.documents_collection(
            db=db, 
            collection_name=collection_name,
            limit=limit,
            offset=offset
        )
        return [DocumentOut.model_validate(doc) for doc in documents]
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la lecture des documents de la collection / table: {str(e)}"
        )
        
@router_collection.delete(
        "",
        summary="Supprime une collection / table",
        description="""Supression d'une collection / table de la base de données""",
        response_model=bool
)
async def delete_collection(
    collection_name: str,
    db: AsyncSession = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
    ) -> bool:
    try:
        await CollectionService.delete_collection(
            db=db,
            vector_db=vector_db,
            name=collection_name
        )
        return True
    except ValueError:
        raise HTTPException(status_code=404, detail="Collection not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
