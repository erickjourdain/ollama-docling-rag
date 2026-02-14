from datetime import datetime

from chromadb import Metadata
from ollama import GenerateResponse


from core.config import settings
from core.logging import logger
from core.exceptions import RAGException
from dependencies.sqlite_session import SessionLocalSync
from repositories.job_repository import get_job
from services import DbVectorielleService, LlmService, JobService

def query_collection(
    job_id: str,
    query: str,
    model: str,
    collection_name: str
):
    """Interrogation de la base de connaissance via une requête utilisateur

    Args:
        job_id (str): identifiant du job
        query (str): requête (prompt) de l'utilisateur
        model (str): modèle à utiliser pour la génération de la réponse
        collection_name (str): nom de la collection à interroger

    Raises:
        Exception: Erreur levée lors de la génération de la réponse
    """    
    
    with SessionLocalSync() as session:
        # Lancement du traitement
        start_time = datetime.now()
        job = get_job(session=session, job_id=job_id)
        if job is None:
            raise Exception("Aucun job avec cet identifiant dans la base")
        
        try:
            job.progress = "initialisation"
            job.status = "processing"
            session.commit()
            JobService.add_job_log(session, job_id, "Démarrage du traitement de la requête")
    
            db_vector_service = DbVectorielleService(
                chroma_db=settings.CHROMA_DB,
                embedding_model=settings.LLM_EMBEDDINGS_MODEL,
                ollama_url=settings.OLLAMA_URL
            )

            # Reformulation de la requête pour interrogation base vectorielle
            job.progress = "query reformulation"
            session.commit()
            JobService.add_job_log(session, job_id, "Reformulation de la requête")   

            llm_service =  LlmService()
            vectordb_query = llm_service.vectordb_query(query=query, model=model)

            # Requête pour interrogation base vectorielle
            job.progress = "query database"
            session.commit()
            JobService.add_job_log(session, job_id, "Interrogation de la base vectorielle")   

            result = db_vector_service.query_collection(
                query=vectordb_query, 
                collection_name=collection_name
            )

            documents = result.get("documents")
            metadatas = result.get("metadatas")
            JobService.add_job_log(session, job_id, "Vérification des documents retournés")   

            # Vérification que la requête à retourner des éléments
            if (
                not documents
                or not documents[0]
                or not metadatas
                or not metadatas[0]
            ):
                job.result = GenerateResponse(
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
                ).model_dump(mode="json")
                job.progress = "done"
                job.status = "completed"
                job.finished_at = datetime.now()
                session.commit()
                JobService.add_job_log(session, job_id, "Fin du traitement: aucun document trouvé")   
                return
            
            # Reranking des documents
            job.progress = "reranking"
            session.commit()
            JobService.add_job_log(session, job_id, "Reranking des documents")   

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
            JobService.add_job_log(session, job_id, "Interrogation du LLM")   

            response = llm_service.create_answer(
                docs=reranked_docs, 
                metadatas=reranked_metas, 
                query=query, 
                model=model
            )

            # Fin de traitement
            ellapsed_time = datetime.now() - start_time
            job.progress = "done"
            job.status = "completed"
            job.finished_at = datetime.now()
            job.result = response.model_dump(mode="json")
            JobService.add_job_log(session, job_id, f"Traitement terminé en {ellapsed_time} s")   
            session.commit()

        except RAGException as re:
            session.rollback()
            job.progress="done"
            job.status="failed"
            job.error=str(re)
            session.commit()
            logger.error(f"Job {job_id} échoué : {re.message}")
            
        except Exception as e:
            session.rollback()
            job.progress="done"
            job.status="failed"
            job.error=str(e)
            session.commit()
            logger.critical(f"Erreur système majeure sur job {job_id}", exc_info=True)