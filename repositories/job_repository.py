from sqlalchemy import select
from sqlalchemy.orm  import Session

from db.models import Job

def create_job(
    session: Session,
    job_id: str,
    input_data: dict[str, str | None] | None,
    type: str
) -> Job:
    """Création d'un nouveau job pour les workers

    Args:
        session (Session): session d'accès à la base de données
        job_id (str): identifiant du job
        input_data (dict[str, str  |  None] | None): dictionnaire des données d'entrée du worker
        type (str): type de job "insert" ou "query"

    Returns:
        Job: le job nouvellement créé
    """
    new_job=Job(id=job_id, input_data=input_data, type=type)
    session.add(new_job)
    session.commit()
    session.refresh(new_job)
    return new_job

def get_job(
    session: Session,
    job_id: str
) -> Job | None:
    """Récupération d'un job

    Args:
        session (Session): session d'accès à la base de données
        job_id (str): identifiant du job

    Returns:
        Job | None: job récupéré
    """
    stmt = select(Job).where(Job.id == job_id)
    result = session.execute(stmt)
    return result.scalar_one_or_none()