from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import uuid

from core import security
from core.exceptions import RAGException
from core.utility import delete_file
from core.logging import logger
from db.models import User
from dependencies.job_runner import get_job_runner
from dependencies.user_websocket import get_user_ws_manager
from dependencies.sqlite_session import get_db
from dependencies.role_checker import allow_admin
from repositories import job_repository
from schemas import CollectionModel, JobResponse, JobOut
from services import ConversionService, CollectionService, JobRunner, UserWebSocketManager, InsertionService

router_insert = APIRouter(prefix="/insert", tags=["Insertion fichier"])

@router_insert.post(
    "/pdf",
    response_model=JobResponse,
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
    user_ws_manager: UserWebSocketManager = Depends(get_user_ws_manager),
    job_runner: JobRunner = Depends(get_job_runner)
) -> JobResponse:
    """Processus d'insertion d'un fichier dans la base de connaissances

    Args:
        file (UploadFile, optional): fichier à insérer.
        collection_name (str, optional): nom de la collection pour insertion du fichier. Defaults to "".
        user_admin (User, optional): utilisateur courant. Defaults to Depends(allow_admin).
        session (Session, optional): session d'accès à la base de données. Defaults to Depends(get_db).
        user_ws_manager (UserWebSocketManager, optional): magasin de gestion des sockets utilisateurs. Defaults to Depends(get_user_ws_manager).
        job_runner (JobRunner, optional): service de gestion des tâches. Defaults to Depends(get_job_runner).

    Raises:
        HTTPException: collection inexistante
        HTTPException: Fichier déjà existant dans la collection
        he: Erreur lors de l'éxecution de la fonction
        HTTPException: Erreur lors de l'insertion du fichier
        HTTPException: Erreur lors de l'éxécution de la fonction

    Returns:
        JobResponse: identifiant de la nouvelle tâche
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
        new_job = job_repository.create_job(
            session=session, 
            job_id=job_id,
            user_id=user_admin.id,
            type="insertion"
        )
        await user_ws_manager.send_to_user(
            user_id=user_admin.id,
            data=JobOut.model_validate(new_job)
        )
        
        print("Vérification fichier terminée")
        # 5. Mise en attente du document dans la pile de traitement
        await job_runner.submit(InsertionService.run_insert_doc,
            file_path=file_path,
            filename=file.filename or 'unknown',
            doc_id=str(doc_id),
            collection=collection,
            job_id=job_id,
            user_id=user_admin.id,
            user_ws_manager=user_ws_manager
        )

        return JobResponse(job_id=job_id)

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
    