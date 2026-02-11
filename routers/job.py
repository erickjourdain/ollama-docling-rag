from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from depencies.sqlite_session import get_db
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
        job = JobService.get_job(session=session, job_id=job_id)
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