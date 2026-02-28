from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.exceptions import RAGException
from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from schemas import UsersListResponse, UserOut, UserFilters, UserCreate, UserUpdate
from dependencies.role_checker import allow_any_user, allow_admin
from services.user_service import UserService


router_user = APIRouter(prefix="/users", tags=["users"])

@router_user.get(
    "/me",
    summary="Information sur l'utilisateur courant",
    description="Récupère les informations de l'utilisateur authentifié par le token JWT.",
    response_model=UserOut
)
async def read_current_user(
    current_user: User = Depends(allow_any_user)
) -> UserOut:
    """Récupération des informations sur l'utilisateur courant via le token JWT fourni

    Args:
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).

    Returns:
        UserOut: informations de l'utilisateur courant
    """
    return UserOut.model_validate(current_user)


@router_user.get(
    "",
    summary="Liste des utilisateurs",
    description="Récupération de la liste des utilisateurs. Accès limité aux administrateurs",
    response_model=UsersListResponse
) 
async def get_users(
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(allow_admin),
    session: Session = Depends(get_db)
)-> UsersListResponse:
    """Liste des utilisateurs enregistrés

    Args:
        limit (int, optional): nombre d'utilisateurs à retourner. Defaults to 50.
        offset (int, optional): offset pour la pagination. Defaults to 0.
        search (Optional[str], optional): filtre de recherche. Defaults to None.
        is_active (Optional[bool], optional): filtre sur l'état des utilisateurs recherchés. Defaults to None.
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_admin).

    Raises:
        HTTPException: Erreur lors de la récupération des utilisateurs
        HTTPException: L'utilisateur n'a pas les droits nécessaires pour accéder aux utilisateurs        

    Returns:
        UsersListResponse: liste des utilisateurs et leur nombre total
    """
    try:
        filters = UserFilters(
            search=search,
            is_active=is_active,
            limit=(limit if limit < 50 and limit > 0 else 50),
            offset=(offset if offset > 0 else 0)
        )
        return UserService.list_users(
            session=session,
            filters=filters
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la récupération des utilisateurs"
        )
    
@router_user.post(
    "",
    summary="Création d'un utilisateur",
    description="Créer un nouvel utilisateur dans la base de données. Action réservée aux administrateurs de l'application",
    response_model=UserOut
)
async def create_user(
    payload: UserCreate,
    session: Session = Depends(get_db),
    current_user: User = Depends(allow_admin)
) -> UserOut:
    """Création d'un nouvel utilisateur dans la base de données

    Args:
        payload (UserCreate): données de création de l'utilisateur
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_admin).

    Returns:
        UserOut: le nouvel utilisateur créé
    """

    try:
        new_user = UserService.create_user(
            user=payload,
            is_active=False,
            session=session
        )
        if new_user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible de créer l'utilisateur"
            )
        return UserOut(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            created_at=new_user.created_at,
            role=new_user.role
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne disposez pas des droits pour effectuer cette opération"
        )
    except Exception as e:
        logger.error(f"Crash inattendu lors de la création de l'utilisateur : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la création de la collection"
        )
    
@router_user.patch(
    "/{user_id}/activate",
    summary="Activation d'un compte utilisateur",
    description="Activer le compte d'un utilisateur, action réservée à un administrateur",
    response_model=UserOut
)
async def activate_user(
    user_id: str,
    current_user: User = Depends(allow_admin),
    session: Session = Depends(get_db)
) -> UserOut:
    """Activation du compte d'un utilisateur

    Args:
        id (str): identifiant de l'utilisateur
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_admin).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).

    Returns:
        bool: l'utilisateur mis à jour
    """
    try:
        user =  UserService.activate_user(
            session=session,
            user_id=user_id
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible de créer l'utilisateur"
            )
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            role=user.role
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne disposez pas des droits pour effectuer cette opération"
        )
    except Exception as e:
        logger.error(f"Crash inattendu lors de la création de l'utilisateur : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la création de la collection"
        )

@router_user.patch(
    "/{user_id}",
    summary="Mise à jour d'un utilisateur",
    description="Mettre à jour les données d'un utilisateur. Action réservée à l'utilisateur ou administrateur"
)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    session: Session = Depends(get_db),
    current_user: User = Depends(allow_any_user)
) -> UserOut:
    """Mise à jour d'un utilisateur

    Args:
        user_id (str): identifiant de l'utilisateur à mettre à jour
        payload (UserUpdate): données de l'utilisateur
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).
        current_user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).

    Returns:
        UserOut: utilisateur mis à jour
    """
    try:
        user = UserService.update_user(
            session=session,
            user_id=user_id,
            user=payload,
            current_user=current_user
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Impossible de créer l'utilisateur"
            )
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            role=user.role
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne disposez pas des droits pour effectuer cette opération"
        )
    except RAGException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )
    except Exception as e:
        logger.error(f"Crash inattendu lors de la création de l'utilisateur : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la création de la collection"
        )