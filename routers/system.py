from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from dependencies.vector_db import get_vector_db_service
from dependencies.role_checker import allow_any_user
from services import DbVectorielleService, LlmService, HealthService
from schemas import HealthResponse, Model

router_system = APIRouter(prefix="/system")

@router_system.get(
    "/health",
    response_model=HealthResponse,
    summary="Vérifier l'état de santé de l'API",
    description="""
    Vérifie l'état de fonctionnement de tous les composants du système:
    - API FastAPI
    - Serveur Ollama
    - Base de données ChromaDB
    - Modèles Ollama disponibles
    """,
    tags=["Système"]
)
def health_check(
    user: User = Depends(allow_any_user),
    session: Session = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
    ) -> HealthResponse:
    """Vérification de l'état de l'application

    Args:
        user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session de connection à la base de données. Defaults to Depends(get_db).
        vector_db (DbVectorielleService, optional): service de base de données vectorielle. Defaults to Depends(get_vector_db_service).

    Raises:
        HTTPException: Erreur lors de la vérification de l'état du système

    Returns:
        HealthResponse: état de santé de l'application
    """
    try:
        return HealthService.check(session=session, vector_db=vector_db)
    except Exception as e:
        logger.error(f"Crash inattendu lors de la vérification de l'état du système: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de la vérification des services"
        )
    
@router_system.get(
    "/models",
    response_model=list[Model],
    summary="Liste des modèles LLM disponibles",
    description="Récupère la liste des modèles disponibles pour interrogation",
    tags=["Système"]
)
def list_models(
    user: User = Depends(allow_any_user)
) -> list[Model]:
    """Récupération de la liste des modèles disponibles sur le serveur LLM

    Args:
        user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).

    Raises:
        HTTPException: Erreur lors de la récupération de la liste des modèles

    Returns:
        list[Model]: liste des modèles disponibles sur le serveur LLM
    """
    try:
        llm_service = LlmService()
        return llm_service.list_models()
    except Exception as e:
        logger.error(f"Crash inattendu lors du chargement des modèles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors du chargement des modèles"
        )
