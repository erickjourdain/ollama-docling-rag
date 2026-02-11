from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.logging import logger
from depencies.sqlite_session import get_db
from depencies.vector_db import get_vector_db_service
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
    session: Session = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
    ) -> HealthResponse:
    try:
        return HealthService.check(session=session, vector_db=vector_db)
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
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
def list_models() -> list[Model]:
    try:
        llm_service = LlmService()
        return llm_service.list_models()
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors du chargement des modèles"
        )
