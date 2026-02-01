from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

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
async def health_check(
    db: AsyncSession = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
    ) -> HealthResponse:
    return await HealthService.check(db=db, vector_db=vector_db)

@router_system.get(
    "/models",
    response_model=list[Model],
    summary="Liste des modèles LLM disponibles",
    description="Récupère la liste des modèles disponibles pour interrogation",
    tags=["Système"]
)
async def list_models() -> list[Model]:
    try:
        llm_service = LlmService()
        return llm_service.list_models()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors du chargement des modèles: {str(e)}"
        )
