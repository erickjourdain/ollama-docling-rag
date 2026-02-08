from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from depencies.sqlite_session import get_db
from depencies.vector_db import get_vector_db_service
from services import CollectionService, DbVectorielleService
from schemas import DocumentModel, CollectionCreate, CollectionModel
from services.user_service import UserService

router_collection = APIRouter(prefix="/collections", tags=["Collections"])

@router_collection.get(
        "",
        summary="Liste des collections / tables",
        description="Récupère l'ensemble des collections / tables de la base de données",
        response_model=list[CollectionModel]
)
def get_collections(
    limit: int = 50, 
    offset: int = 0, 
    session: Session = Depends(get_db)
 ) -> list[CollectionModel]:
    try:
        limit = (limit if limit < 50 and limit > 0 else 50)
        offset = (offset if offset > 0 else 0) 
        collections = CollectionService.list_collections(
            session=session,
            limit=limit,
            offset=offset
        )
        return [CollectionModel.model_validate(collection) for collection in collections]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la récupération des tables: {str(e)}"
        )
    
@router_collection.post(
        "",
        summary="Créer une collection / table",
        description="Création d'une nouvelle collection / table dans la base de données vectorielle",
        response_model=CollectionModel
)
async def create(
    payload: CollectionCreate,
    session: Session = Depends(get_db),
    vector_session: DbVectorielleService = Depends(get_vector_db_service)
) -> CollectionModel:
    try:
        user = UserService().get_user_by_name(session=session, username=settings.FIRST_USER_USERNAME)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")
        CollectionService.create_collection(
            session=session, 
            vector_session=vector_session,
            name=payload.name,
            description=payload.description,
            user_id=user.id
        )
        collection = CollectionService.get_by_name(session=session, name=payload.name)
        return CollectionModel.model_validate(collection)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la création de la collection / table: {str(e)}"
        )
    
@router_collection.get(
        "/{collection_name}",
        summary="Information sur une collection",
        description="Retourne les information sur la collection",
        response_model=CollectionModel
)
async def get_collection(
    collection_name: str,
    session: Session = Depends(get_db)
    ) -> CollectionModel:
    try:
        collection = CollectionService.get_by_name(session=session, name=collection_name)
        return CollectionModel.model_validate(collection)
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la lecture des information sur de la collection / table: {str(e)}"
        )

@router_collection.get(
        "/{collection_name}/documents",
        summary="Liste des documents indexés dans la collection",
        response_model=list[DocumentModel]
)
async def get_collection_documents(
    collection_name: str,
    limit: int = 50,
    offset: int = 0,
    session: Session = Depends(get_db)
) -> list[DocumentModel]:
    try:
        limit = (limit if limit < 50 and limit > 0 else 50)
        offset = (offset if offset > 0 else 0) 
        documents = CollectionService.documents_collection(
            session=session, 
            collection_name=collection_name,
            limit=limit,
            offset=offset
        )
        return [DocumentModel.model_validate(doc) for doc in documents]
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
    session: Session = Depends(get_db),
    vector_session: DbVectorielleService = Depends(get_vector_db_service)
    ) -> bool:
    try:
        CollectionService.delete_collection(
            session=session,
            vector_session=vector_session,
            name=collection_name
        )
        return True
    except ValueError:
        raise HTTPException(status_code=404, detail="Collection not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Forbidden")
