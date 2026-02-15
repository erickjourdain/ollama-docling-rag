from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
import uuid

from core import security
from core.exceptions import RAGException
from core.utility import delete_file
from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from dependencies.worker import get_workers
from dependencies.role_checker import allow_admin
from repositories import job_repository
from schemas.collection import CollectionModel
from schemas import InsertResponse
from services import ConversionService, CollectionService
from worker.insert_doc import insert_doc

router_insert = APIRouter(prefix="/insert", tags=["Insertion fichier"])

@router_insert.post(
    "/pdf",
    response_model=InsertResponse,
    summary="Lancer le traitement d'un document pour stockage dans la base de connaissances",
    description="""
    Conversion d'un document en markdown via Docling, stockage du fichier converti sur le serveur,
    chunk du document et stockage dans la base de données vectorielle.
    """
)
async def process_file(
    file: UploadFile = File(..., description="Fichier à traiter"),
    collection_name: str = "",
    user_admin: User = Depends(allow_admin),
    session: Session = Depends(get_db),
    executor: ThreadPoolExecutor = Depends(get_workers)
) -> InsertResponse:
    """
    Mise en attente d'un fichier dans la file d'attente de traitement 
    pour intégration dans la base de connaissances
    """
    try:
        # 1. Vérification des différents élements avant de lancer le job de conversion
        collection = CollectionService.get_by_name(
            session=session, 
            name=collection_name
        )
        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"La collection {collection_name} n'existe pas"
            )
        collection = CollectionModel.model_validate(collection)

        await security.validate_file_type(file=file)

        # 2. Sauvegarde du fichier
        job_id = str(uuid.uuid4())
        doc_id = uuid.uuid4()
        file_path = await ConversionService.save_imported_file(
            file=file, 
            collection_name=collection_name, 
            doc_id=str(doc_id)
        )

        # 3. Vérification de la présence du fichier dans la collection
        file_exist = ConversionService.check_md5(
            file_path=file_path, 
            collection_id=collection.id, 
            session=session
        )
        if file_exist:
            delete_file(file_path=file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Le fichier est déjà présent dans la collection"
            )
        
        # 4. Création du job dans la base de données
        job_repository.create_job(
            session=session, 
            job_id=job_id, 
            input_data={
                'filename': file.filename,
                'doc_id': str(doc_id),
                'collection': collection.name,
                'user': user_admin.username
            },
            type="insertion"
        )
        
        # 5. Mise en attente du document dans la pile de traitement
        executor.submit(insert_doc,
            file_path=file_path,
            filename=file.filename or 'unknown',
            doc_id=str(doc_id),
            collection=collection,
            job_id=job_id,
            user_id=user_admin.id
        )

        return InsertResponse(job_id=job_id)

    except HTTPException as he:
        raise he
    except RAGException as re:
        logger.error(f"Erreur lors de l'insertion du fichier {file.filename} dans la collection {collection_name}: {re.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors du traitement du PDF"
        )
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors du traitement du PDF"
        )
    