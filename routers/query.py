from concurrent.futures import ThreadPoolExecutor
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.exceptions import RAGException
from core.config import settings
from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from dependencies.worker import get_workers
from dependencies.role_checker import allow_any_user
from repositories import job_repository
from schemas import QueryRequest, CollectionModel
from schemas.response import InsertResponse
from services import CollectionService, LlmService
from worker.query_collection import query_collection

router_query = APIRouter(prefix="/query", tags=["Query"])

@router_query.post(
        "",
        response_model=InsertResponse,
        summary="Interroge la base de connaissances",
        description="""
        Excute une requête sur la base de connaissances:
        - interogation de la base de connaissances
        - envoi du contexte au LLM pour création de la réponse
        """
)
def query(
    payload: QueryRequest,
    user: User = Depends(allow_any_user),
    session: Session = Depends(get_db),
    executor: ThreadPoolExecutor = Depends(get_workers)
    ) -> InsertResponse:
    """Exécution d'une requête utilisateur sur le système RAG

    Args:
        payload (QueryRequest): Information sur la requête à effectuer
            query: requête de l'utilisateur
            collection_name: nom de la collection à interroger
            model: nom du modèle à utiliser (optionel)
        user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session de connection à la base de données. Defaults to Depends(get_db).
        executor (ThreadPoolExecutor, optional): pool de threads pour l'exécution des tâches en arrière-plan. Defaults to Depends(get_workers).

    Raises:
        HTTPException: Erreur lors de l'éxecution de la fonction

    Returns:
        InsertResponse | None: identifiant du job 
    """
    try:
        # 1. Vérification de la présence de la collection
        collection = CollectionService.get_by_name(
            session=session, 
            name=payload.collection_name
        )
        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"La collection {payload.collection_name} n'existe pas"
            )
        collection = CollectionModel.model_validate(collection)

        # 2. Vérification de l'existence du modèle
        model = payload.model if payload.model is not None else settings.LLM_MODEL
        llm_service =  LlmService()
        models = llm_service.list_models()
        noms_models = [model.nom for model in models if not model.embed]
        if model not in noms_models:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Le modèle '{payload.model}' n'est pas disponible"
            )

        # 3. Création du job dans la base de données
        job_id = str(uuid.uuid4())
        job_repository.create_job(
            session=session, 
            job_id=job_id, 
            input_data={
                "query": payload.query,
                "model": payload.model,
                "collection": payload.collection_name,
                "user": user.username
            },
            type="query"
        )

        # 4. Mise en attente de la requête dans la pile de traitement
        executor.submit(query_collection,
            job_id=job_id,
            query=payload.query,
            model=model,
            collection_name=payload.collection_name
        )

        return InsertResponse(job_id=job_id)

    except HTTPException as he:
        raise he
    except RAGException as re:
        logger.error(f"Erreur lors de l'exécution de la requête {payload.query}: {re.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de l'éxécution de la requête"
        )
    except Exception as e:
        logger.error(f"Crash inattendu lors de l'exécution d'une requête: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors de l'éxécution de la requête"
        )

