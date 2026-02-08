from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from concurrent.futures import ThreadPoolExecutor
import uuid

from core.utility import delete_file
from core.config import settings
from depencies.sqlite_session import get_db
from depencies.worker import get_workers
from repositories import job_repository
from schemas.collection import CollectionModel
from services import job_service
from schemas import InsertResponse, JobOut
from services import ConversionService, CollectionService
from services.user_service import UserService
from worker.insert_pdf import insert_pdf

router_insert = APIRouter(prefix="/insert", tags=["Insertion fichier"])

@router_insert.post(
    "/pdf",
    response_model=InsertResponse,
    summary="Lancer le traitement d'un PDF pour stockage dans la base de connaissances",
    description="""
    Insertion d'un fichier PDF complet et stockage dans une collection / table.
    """
)
async def process_pdf(
    file: UploadFile = File(..., description="Fichier PDF à traiter"),
    collection_name: str = "",
    session: Session = Depends(get_db),
    executor: ThreadPoolExecutor = Depends(get_workers)
) -> InsertResponse:
    """
    Mise en attente d'un fichier PDF dans la file d'attente de traitement 
    pour intégration dans la base de connaissances
    """
    try:
        # 1. Vérification des différents élements avant de lancer le job de conversion
        collection = CollectionService.get_by_name(
            session=session, 
            name=collection_name
        )
        if collection is None:
            raise Exception("La collection doit être créée avant d'y insérer un document")
        collection = CollectionModel.model_validate(collection)

        is_pdf = ConversionService.check_pdf(
            file=file
        )
        if not is_pdf:
            raise Exception("Le fichier fourni n'est pas un fichier pdf")

        # 2. Sauvegarde du fichier
        job_id = str(uuid.uuid4())
        doc_id = str(uuid.uuid4())
        filename=f"{doc_id}.pdf"
        file_path = await ConversionService.save_pdf(
            file=file, 
            collection_name=collection_name, 
            filename=filename
        )

        # 3. Vérification de la présence du fichier dans la collection
        file_exist = ConversionService.check_md5(
            file_path=file_path, 
            collection_id=collection.id, 
            session=session
        )
        if file_exist:
            delete_file(file_path=file_path)
            raise Exception("Le fichier est déjà présent dans la collection")

        # 4. Création du job dans la base de données
        job_repository.create_job(
            session=session, 
            job_id=job_id, 
            filename=filename
        )

        # 5. Récupération de l'utilisateur
        user = UserService.get_user_by_name(
            session=session, 
            username=settings.FIRST_USER_USERNAME
        )
        if user is None:
            raise Exception("L'utilisateur n'existe pas")
        
        executor.submit(insert_pdf,
            file_path=file_path,
            filename=filename, 
            collection=collection,
            job_id=job_id,
            user_id=user.id
        )

        return InsertResponse(job_id=job_id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors du traitement du PDF: {str(e)}"
        )
    
@router_insert.get(
        "/{job_id}",
        response_model=JobOut,
        summary="Statut d'un job d'insertion",
        description="Fourniture de l'état d'avancement de l'insertion d'un fichier dans la base de connaissances",
)
def job_status(
    job_id: str,
    session: Session = Depends(get_db),
) -> JobOut:
    """Status d'avancement de l'insertion d'un fichier dans la base de connaissances

    Args:
        job_id (str): id du job d'insertion
        session (Session, optional): Session de connection à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: 404 job not found
        HTTPException: 500 internal server error

    Returns:
        Job: Etat du job d'insertion
    """
    try:
        job = job_service.get_job(sesssion=session, job_id=job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Aucun job portant cet identifiant"
            )
        return JobOut.model_validate(job)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la lectrure d'un job: {str(e)}"
        )
    