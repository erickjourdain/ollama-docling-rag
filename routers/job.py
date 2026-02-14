from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.logging import logger
from db.models import User
from dependencies.sqlite_session import get_db
from dependencies.role_checker import allow_admin, allow_any_user
from schemas.response import JobCleaningResponse
from services import JobService
from schemas import JobOut


router_job = APIRouter(prefix="/jobs", tags=["Jobs"])

@router_job.get(
        "/{job_id}",
        response_model=JobOut,
        summary="Statut d'un job",
        description="Fourniture de l'état d'avancement d'un job",
)
def job_status(
    job_id: str,
    admin_user: User = Depends(allow_any_user), 
    session: Session = Depends(get_db),
) -> JobOut:
    """Status d'avancement de l'insertion d'un fichier dans la base de connaissances

    Args:
        job_id (str): id du job d'insertion
        user (User, optional): utilisateur courant. Defaults to Depends(allow_any_user).
        session (Session, optional): session de connection à la base de données. Defaults to Depends(get_db).

    Raises:
        HTTPException: 404 job not found
        HTTPException: 500 internal server error

    Returns:
        Job: Etat du job d'insertion
    """
    try:
        job = JobService.get_job(session=session, job_id=job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Aucun job portant cet identifiant"
            )
        return JobOut.model_validate(job)
    except Exception as e:
        logger.error(f"Crash inattendu : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la lectrure d'un job: {str(e)}"
        )
    
@router_job.delete("/jobs/cleanup")
async def cleanup_old_jobs(
    days: int = 7,
    admin_user: User = Depends(allow_admin), 
    session: Session = Depends(get_db)
)-> JobCleaningResponse:
    """Nettoyage des anciens jobs de la base de données

    Args:
        days (int, optional): nombre de jours avant suppression des jobs. Defaults to 7.
        admin_user (User, optional): utilisateur courant. Defaults to Depends(allow_admin).
        session (Session, optional): session de connection à la base de données. Defaults to Depends(get_db).

    Returns:
        _type_: _description_
    """
    try:
        count = JobService.cleanup_old_jobs(session, days)
        return JobCleaningResponse(
            message=f"Nettoyage effectué par {admin_user.username}", 
            deleted=count
        )
    except Exception as e:
        logger.error(f"Crash inattendu lors du nettoyage des anciens jobs : {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Erreur lors du nettoyage des anciens jobs"
        )