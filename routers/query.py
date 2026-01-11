from ollama import GenerateResponse
from fastapi import APIRouter, HTTPException, status

from schemas import QueryRequest
from services import DbService, LlmService

from core.config import settings

router_query = APIRouter(prefix="/query", tags=["Query"])

@router_query.post(
        "",
        summary="Interroge la base de connaissances",
        description="""
        Excute une requête sur la base de connaissances:
        - interogation de la base de connaissances
        - envoi du contexte au LLM pour création de la réponse
        """
)
async def query(req: QueryRequest) -> GenerateResponse:
    """Exécution d'une requête utilisateur sur le système RAG

    Args:
        req (QueryRequest): Information sur la requête à effectuer
            query: requête de l'utilisateur
            collection_name: nom de la collection à interroger
            model: nom du modèle à utiliser (optionel)

    Raises:
        HTTPException: Erreur lors de l'éxecution de la fonction

    Returns:
        GenerateResponse | None: Réponse 
    """
    try:
        db_service = DbService()
        llm_service =  LlmService()
        model = req.model if req.model is not None else settings.llm_model
        # Tester si la collecion / table existe
        tables = db_service.list_tables()
        if req.collection_name not in tables:
            raise Exception(f"La collection '{req.collection_name}' n'existe pas")
        # Tester si le modèle existe
        models = llm_service.list_models()
        noms_models = [model.nom for model in models if not model.embed]
        if model not in noms_models:
            raise Exception(f"Le modèle '{req.model}' n'est pas disponible")
        vectordb_query = llm_service.vectordb_query(req.query, model=model)
        chunks = db_service.query_db(vectordb_query, req.collection_name)
        if len(chunks):
            chunks = llm_service.rerank_chunks_llm(query=req.query,chunks=chunks)
        reponse = llm_service.create_answer(chunks=chunks, query=req.query, model=model)
        return reponse
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de l'éxcution de la demande: {str(e)}"
        ) 

