import asyncio
from datetime import datetime
from pathlib import Path

from core.exceptions import RAGException
from core.security import hash_file
from core.logging import logger
from core.config import settings
from db.models import DocumentMetadata
from dependencies.sqlite_session import SessionLocalSync
from repositories.collections_repository import CollectionRepository
from repositories.job_repository import get_job
from schemas import CollectionModel
from schemas.job import JobOut
from services import ChunkingService, ConversionService, DbVectorielleService
from services.user_websocket_manager import UserWebSocketManager
from services.job_service import JobService

async def insert_doc(
    file_path: Path,
    filename: str,
    doc_id: str,
    collection: CollectionModel,
    job_id: str,
    user_id: str,
    user_ws_manager: UserWebSocketManager
):
    """Insertion d'un fichier dans la base de connaissance

    Args:
        file_path (Path): chemin vers le fichier à insérer
        filename (str): nom du fichier à insérer
        doc_id (UUID): identifiant du fichier à insérer
        collection (CollectionModel): collection dans laquelle insérer le document 
        job_id (str): identifiant du job d'insertion
        user_id (str): identfiant de l'utilisateur
        user_ws_manager (UserWebSocketManager): magasin de gestion des websockets utilisateurs

    Raises:
        Exception: Erreur levée lors de l'insertion du document
    """

    with SessionLocalSync() as session:
        # Lancement du traitement
        start_time = datetime.now()
        job = get_job(session=session, job_id=job_id)
        if job is None:
            logger.error(f"Job {job_id} inconnu")
            raise Exception("Aucun job avec cet identifiant dans la base")
        
        try:           
            job.progress = "initialisation"
            job.status = "processing"
            session.commit()  
            JobService.add_job_log(session, job_id, f"Démarrage du traitement pour {filename}")
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            )   

            db_vector_service = DbVectorielleService(
                chroma_db=settings.CHROMA_DB,
                embedding_model=settings.LLM_EMBEDDINGS_MODEL,
                ollama_url=settings.OLLAMA_URL
            )

            # Conversion du fichier en markdown
            job.progress = "file conversion"
            JobService.add_job_log(session, job_id, "Lancement conversion en markdown")   
            session.commit()
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            )   

            conversion_result = await asyncio.to_thread(
                ConversionService.convert_to_md,
                file_path=file_path, 
                collection_name=collection.name,
                doc_id=doc_id
            )

            # Enregistrement des informations liées au document inséré
            job.progress = "add metadata"
            session.commit()
            JobService.add_job_log(session, job_id, "Ajout des métadatas dans la base")
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            ) 

            #id=str(uuid.uuid4())
            document = DocumentMetadata(
                id=doc_id,
                filename=filename,
                collection_id=collection.id,
                inserted_by=user_id,
                date_insertion=datetime.now(),
                md5=await asyncio.to_thread(hash_file, file_path=file_path)
            )
            document = CollectionRepository.add_document(
                session=session, 
                document=document
            )

            # chunking du document
            job.progress="chunking"
            session.commit()
            JobService.add_job_log(session, job_id, "Début du découpage (chunking)")
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            )  

            chunking_service = ChunkingService(filename=filename)
            chunking_result = await asyncio.to_thread(
                chunking_service.basic_chunking,
                document=conversion_result.document, 
                document_id=doc_id
            )
            JobService.add_job_log(session, job_id, f"Document découpé en {len(chunking_result.chunks)} morceaux")

            # Enregistrement des chunks dans la base de données vectorielles
            job.progress="embeddings"
            session.commit()
            JobService.add_job_log(session, job_id, f"Lancement des embeddings sur {settings.LLM_EMBEDDINGS_MODEL}...")
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            ) 

            await asyncio.to_thread(
                db_vector_service.insert_chunk,
                collection_name=collection.name,
                chunks=chunking_result.chunks
            )
            document.is_indexed = True
            session.commit()
            JobService.add_job_log(session, job_id, "Indexation vectorielle terminée avec succès")

            # Fin du traitement
            ellapsed_time = datetime.now() - start_time
            job.progress="done" 
            job.status="completed"
            job.finished_at=datetime.now()
            session.commit()
            JobService.add_job_log(session, job_id, f"Traitement terminé en {ellapsed_time} s")
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            ) 

        except RAGException as re:
            session.rollback()
            job.progress="done"
            job.status="failed"
            job.error_message=str(re)
            session.commit()
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            ) 
            logger.error(f"Job {job_id} échoué : {re.message}")
            
        except Exception as e:
            session.rollback()
            job.progress="done"
            job.status="failed"
            job.error_message=str(e)
            session.commit()
            await user_ws_manager.send_to_user(
                user_id=user_id,
                data=JobOut.model_validate(job)
            ) 
            logger.critical(f"Erreur système majeure sur job {job_id}", exc_info=True)
