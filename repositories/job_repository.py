from datetime import datetime, timedelta

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


def cleanup_old_jobs(session: Session, days: int = 7) -> int:
    """Suppression des vieux jobs

    Args:
        session (Session): session d'accès à la base de données
        days (int, optional): nombre de jours au-delà duquel les jobs sont supprimés. Defaults to 7.

    Returns:
        int: nombre de jobs supprimés
    """
    # Calcul de la date limite
    threshold_date = datetime.now() - timedelta(days=days)
    
    # 1. Identifier les IDs à supprimer
    query = session.query(Job.id).filter(
        Job.status.in_(["completed", "failed"]),
        Job.created_at < threshold_date
    )
    job_ids = [r.id for r in query.all()]
    
    if not job_ids:
        return 0

    # 2. Supprimer
    session.query(Job).filter(Job.id.in_(job_ids)).delete(synchronize_session=False)
    session.commit()

    return len(job_ids) # Retourne le nombre de lignes supprimées