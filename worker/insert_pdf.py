from datetime import datetime
from pathlib import Path
import uuid

from core.security import hash_file
from core.config import settings
from db.models import DocumentMetadata
from depencies.sqlite_session import SessionLocalSync
from repositories.collections_repository import CollectionRepository
from repositories.job_repository import get_job, update_job_progress
from schemas import CollectionModel
from services import ChunkingService, ConversionService, DbVectorielleService
        

def insert_pdf(
    file_path: Path,
    filename: str,
    collection: CollectionModel,
    job_id: str,
    user_id: str,
):
    """Insertion d'un fichier pdf dans la base de connaissance

    Args:
        file_path (Path): chemin vers le fichier à insérer
        filename (str): nom du fichier
        collection (CollectionModel): collection dans laquelle insérer le document 
        job_id (str): identifiant du job d'insertion
        user_id (str): identfiant de l'utilisateur
    """
    # Session principale pour l'insertion du fichier
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

            # Conversion du fichier pdf
            job.progress = "file conversion"
            session.commit()

            conversion_result = ConversionService.convert_pdf_to_md(
                file_path=file_path, 
                collection_name=collection.name
            )

            # Enregistrement des informations liées au document inséré
            job.progress = "add metadata"
            session.commit()

            id=str(uuid.uuid4())
            document = DocumentMetadata(
                id=id,
                filename=filename,
                collection_id=collection.id,
                inserted_by=user_id,
                date_insertion=datetime.now(),
                md5=hash_file(file_path=file_path)
            )
            document = CollectionRepository.add_document(
                session=session, 
                document=document
            )

            # chunking du document
            job.progress="chunking"
            session.commit()

            chunking_service = ChunkingService(filename=filename)
            chunking_result = chunking_service.basic_chunking(
                document=conversion_result.document, 
                document_id=id
            )

            # Enregistrement des chunks dans la base de données vectorielles
            job.progress="embeddings"
            session.commit()

            db_vector_service.insert_chunk(
                collection_name=collection.name,
                chunks=chunking_result.chunks
            )
            document.is_indexed = True

            # fin du traitement
            job.progress="done" 
            job.status="completed"
            job.finished_at=datetime.now()
            session.commit()

        except Exception as e:
            session.rollback()
            with SessionLocalSync() as progress_session:
                update_job_progress(
                    session=progress_session, 
                    job_id=job_id, 
                    progress="done", 
                    status="failed",
                    error=str(e)
                )
