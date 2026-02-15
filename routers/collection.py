from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from dependencies.vector_db import get_vector_db_service
from dependencies.role_checker import allow_admin, allow_any_user
from services import CollectionService, DbVectorielleService
from schemas import (
    CollectionCreate, 
    CollectionModel, 
    CollectionFilters, 
    CollectionListResponse,
    DocumentFilters,
    DocumentListResponse
)

router_collection = APIRouter(prefix="/collections", tags=["Collections"])

@router_collection.get(
        "",
        summary="Liste des collections",
        description="Récupère l'ensemble des collections de la base de données",
        response_model=CollectionListResponse
)
def get_collections(
    limit: int = 50, 
    offset: int = 0,
    collection_name: Optional[str] = None,
    user: Optional[str] = None,
    current_user: User = Depends(allow_any_user),
    session: Session = Depends(get_db)
 ) -> CollectionListResponse:
    """Liste des collections indéxées dans la base de données

    Args:
        limit (int, optional): nombre de collections à retourner. Defaults to 50.
        offset (int, optional): offset pour la pagination. Defaults to 0.
        collection_name (Optional[str], optional): nom de la collection à filtrer. Defaults to None.
        user (Optional[str], optional): utilisateur à filtrer. Defaults to None.
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: Erreur lors de la récupération des collections
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour accéder aux collections

    Returns:
        CollectionListResponse: liste des collections et leur nombre total
    """
    try:
        filters = CollectionFilters(
            name = collection_name,
            user = user,
            limit = (limit if limit < 50 and limit > 0 else 50),
            offset =(offset if offset > 0 else 0)
        ) 
        return CollectionService.list_collections(
            session=session,
            filters=filters
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la récupération des collections"
        )
    
@router_collection.post(
        "",
        summary="Créer une collection",
        description="Création d'une nouvelle collection dans la base de données vectorielle",
        response_model=CollectionModel
)
async def create(
    payload: CollectionCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(allow_admin),
    vector_session: DbVectorielleService = Depends(get_vector_db_service)
) -> CollectionModel:
    """Création d'un nouvelle collection

    Args:
        payload (CollectionCreate): données de création de la collection
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_admin).
        vector_session (DbVectorielleService, optional): service de base de données vectorielle. Defaults to Depends(get_vector_db_service).

    Raises:
        HTTPException: Erreur lors de la création de la collection
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour supprimer la collection

    Returns:
        CollectionModel: la collection créée
    """
    try:
        CollectionService.create_collection(
            session=session, 
            vector_session=vector_session,
            name=payload.name,
            description=payload.description,
            user_id=current_user.id
        )
        collection = CollectionService.get_by_name(session=session, name=payload.name)
        return CollectionModel.model_validate(collection)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except HTTPException as e:
        logger.error(f"Crash inattendu lors de la création de la collection : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la création de la collection"
        )
    
@router_collection.get(
        "/{collection_name}",
        summary="Information sur une collection",
        description="Retourne les information sur la collection",
        response_model=CollectionModel
)
async def get_collection(
    collection_name: str,
    current_user: User = Depends(allow_any_user),
    session: Session = Depends(get_db)
    ) -> CollectionModel:
    """Information sur une collection

    Args:
        collection_name (str): nom de la collection
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour supprimer la collection
        HTTPException: La collection n'existe pas

    Returns:
        CollectionModel: information sur la collection
    """
    try:
        collection = CollectionService.get_by_name(session=session, name=collection_name)
        return CollectionModel.model_validate(collection)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la lecture des information de la collection"
        )

@router_collection.get(
        "/{collection_name}/documents",
        summary="Liste des documents indexés dans la collection",
        response_model=DocumentListResponse
)
async def get_collection_documents(
    collection_name: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(allow_any_user),
    session: Session = Depends(get_db)
) -> DocumentListResponse:
    """Liste des documents indexés dans une collection

    Args:
        collection_name (str): nom de la collection
        limit (int, optional): nombre de documents à retourner. Defaults to 50.
        offset (int, optional): offset. Defaults to 0.
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: La collection n'existe pas
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour supprimer la collection
        HTTPException: Erreur lors de la lecture des documents de la collection

    Returns:
        DocumentListResponse: liste des documents indexés dans la collection et leur nombre total
    """
    try:
        limit = (limit if limit < 50 and limit > 0 else 50)
        offset = (offset if offset > 0 else 0) 
        return CollectionService.documents_collection(
            session=session,
            filters=DocumentFilters(
            collection_name=collection_name,
                limit=limit,
                offset=offset
            )
        )
    except ValueError as e:
        logger.error(f"Collection introuvable : {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection introuvable")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except Exception as e:
        logger.error(f"Crash inattendu lors de la lecture des documents de la collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la lecture des documents de la collection"
        )
    
@router_collection.get(
        "/{collection_name}/documents/count",
        summary="Nombre de documents indexés dans la collection",
        description="Retourne le nombre de documents indexés dans la collection",
        response_model=int
)
async def count_collection_documents(
    collection_name: str,
    current_user: User = Depends(allow_any_user),
    session: Session = Depends(get_db)
) -> int:
    """Nombre de documents indexés dans une collection

    Args:
        collection_name (str): nom de la collection
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: La collection n'existe pas
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour supprimer la collection
        HTTPException: Erreur lors de la lecture du nombre de documents de la collection

    Returns:
        int: nombre de documents indexés dans la collection
    """
    try:
        return CollectionService.count_documents_collection(
            session=session,
            collection_name=collection_name
        )
    except ValueError as e:
        logger.error(f"Collection introuvable : {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection introuvable")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except Exception as e:
        logger.error(f"Crash inattendu lors de la lecture du nombre de documents de la collection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la lecture du nombre de documents de la collection"
        )
        
@router_collection.delete(
        "",
        summary="Supprime une collection / table",
        description="""Supression d'une collection de la base de données""",
        response_model=bool
)
async def delete_collection(
    collection_name: str,
    current_user: User = Depends(allow_admin),
    session: Session = Depends(get_db),
    vector_session: DbVectorielleService = Depends(get_vector_db_service)
    ) -> bool:
    """Suppression d'une collection et tous les documents indexé dans la collection

    Args:
        collection_name (str): nom de la collection à supprimer
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_admin).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).
        vector_session (DbVectorielleService, optional): session d'accès à la base vectorielle. Defaults to Depends(get_vector_db_service).

    Raises:
        HTTPException: La collection n'existe pas
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour supprimer la collection
        HTTPException: Erreur lors de la suppression de la collection

    Returns:
        bool: True si la collection a été supprimée avec succès
    """
    try:
        CollectionService.delete_collection(
            session=session,
            vector_session=vector_session,
            name=collection_name
        )
        return True
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La collection n'existe pas'")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la suppression de la collection"
        )
