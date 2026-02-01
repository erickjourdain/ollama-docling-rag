from datetime import datetime
from chromadb import Metadata
from ollama import GenerateResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from depencies.sqlite_session import get_db
from depencies.vector_db import get_vector_db_service
from schemas import QueryRequest
from services import CollectionService, DbVectorielleService, LlmService

from core.config import settings

router_query = APIRouter(prefix="/query", tags=["Query"])

@router_query.post(
        "",
        response_model=GenerateResponse,
        summary="Interroge la base de connaissances",
        description="""
        Excute une requête sur la base de connaissances:
        - interogation de la base de connaissances
        - envoi du contexte au LLM pour création de la réponse
        """
)
async def query(
    payload: QueryRequest, 
    db: AsyncSession = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
    ) -> GenerateResponse:
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
        collection_service = CollectionService()
        llm_service =  LlmService()
        model = payload.model if payload.model is not None else settings.llm_model
        # Tester si la collecion / table existe
        collection = collection_service.get_by_name(db=db, name=payload.collection_name)
        if collection is None:
            raise Exception(f"La collection '{payload.collection_name}' n'existe pas")
        # Tester si le modèle existe
        models = llm_service.list_models()
        noms_models = [model.nom for model in models if not model.embed]
        if model not in noms_models:
            raise Exception(f"Le modèle '{payload.model}' n'est pas disponible")
        vectordb_query = llm_service.vectordb_query(payload.query, model=model)
        result = vector_db.query_collection(query=vectordb_query, collection_name=payload.collection_name)
        
        documents = result.get("documents")
        metadatas = result.get("metadatas")

        # Vérification que la requête à retourner des éléments
        if (
            not documents
            or not documents[0]
            or not metadatas
            or not metadatas[0]
        ):
            return GenerateResponse(
                model=payload.model,
                created_at=datetime.now().isoformat(),
                done=False,
                done_reason="Aucun document trouvé",
                total_duration=0,
                load_duration=0,
                prompt_eval_count=0,
                prompt_eval_duration=0,
                eval_count=0,
                eval_duration=0,
                response="""
                    '''json
                        {
                            "answer": "Aucune donnée trouvée permettant de répondre à la question posée",
                            "sources": []
                        }
                    '''
                """
            )

        # Reranking des documents
        documents = documents[0]
        metadatas = metadatas[0]
        ranking = llm_service.rerank_chunks_llm(query=payload.query,chunks=documents)

        reranked_docs: list[str] = []
        reranked_metas: list[Metadata] = []
        for idx in ranking:
            if idx < len(documents):
                reranked_docs.append(documents[idx])
                reranked_metas.append(metadatas[idx])

        # Création de la réponse
        reponse = llm_service.create_answer(
            docs=reranked_docs, 
            metadatas=reranked_metas, 
            query=payload.query, 
            model=model
        )

        return reponse
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de l'éxcution de la demande: {str(e)}"
        ) 

