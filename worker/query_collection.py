from datetime import datetime
import json

from chromadb import Metadata
from ollama import GenerateResponse
from core.config import settings
from depencies.sqlite_session import SessionLocalSync
from repositories.job_repository import get_job, update_job_progress
from services import DbVectorielleService, LlmService

def query_collection(
    job_id: str,
    query: str,
    model: str,
    collection_name: str
):
    
    with SessionLocalSync() as session:
        try:
            # Lancement du traitement
            job = get_job(session=session, job_id=job_id)
            if job is None:
                raise Exception("Aucun job avec cet identifiant dans la base")
            
            job.progress = "initialisation"
            job.status = "processing"
            session.commit()
    
            db_vector_service = DbVectorielleService(
                chroma_db_dir=settings.chroma_db_dir,
                embedding_model=settings.LLM_EMBEDDINGS_MODEL,
                ollama_url=settings.OLLAMA_URL
            )

            # Reformulation de la requête pour interrogation base vectorielle
            job.progress = "query reformulation"
            session.commit()

            llm_service =  LlmService()
            vectordb_query = llm_service.vectordb_query(query=query, model=model)

            # Requête pour interrogation base vectorielle
            job.progress = "query database"
            session.commit()

            result = db_vector_service.query_collection(
                query=vectordb_query, 
                collection_name=collection_name
            )

            documents = result.get("documents")
            metadatas = result.get("metadatas")

            # Vérification que la requête à retourner des éléments
            if (
                not documents
                or not documents[0]
                or not metadatas
                or not metadatas[0]
            ):
                job.result = json.dumps(GenerateResponse(
                    model=model,
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
                ))
                job.progress = "done"
                job.status = "completed"
                job.finished_at = datetime.now()
                session.commit()
                return
            
            # Reranking des documents
            job.progress = "reranking"
            session.commit()

            documents = documents[0]
            metadatas = metadatas[0]
            ranking = llm_service.rerank_chunks_llm(query=query,chunks=documents)

            reranked_docs: list[str] = []
            reranked_metas: list[Metadata] = []
            for idx in ranking:
                if idx < len(documents):
                    reranked_docs.append(documents[idx])
                    reranked_metas.append(metadatas[idx])

            # Génération de la réponse
            job.progress = "generation answer"
            session.commit()

            response = llm_service.create_answer(
                docs=reranked_docs, 
                metadatas=reranked_metas, 
                query=query, 
                model=model
            )

            job.progress = "done"
            job.status = "completed"
            job.finished_at = datetime.now()
            job.result = json.dumps(response.model_dump_json(), ensure_ascii=False)
            session.commit()

        except Exception as e:
            session.rollback()
            update_job_progress(
                session=session, 
                job_id=job_id, 
                progress="done", 
                status="failed",
                error=str(e)
            )