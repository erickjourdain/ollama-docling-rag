from fastapi import APIRouter, HTTPException, status

from services import LlmService, DbService
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
async def health_check() -> HealthResponse:
    try:
        llm_service = LlmService()
        models_list = llm_service.list_models()
        llm_status = "ok"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="serveur ollama injoignable"
        )
    
    try:
        db_service = DbService()
        db_service.list_tables()
        db_service = "ok"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="erreur connexion ChromaDB"
        )
    
    return HealthResponse(
        api="ok",
        llm=llm_status,
        db=db_service,
        models_available=models_list
    )

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
