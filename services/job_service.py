from datetime import datetime

from sqlalchemy.orm  import Session

from db.models import Job
from repositories import job_repository

class JobService:

    @staticmethod
    def get_job(
        session: Session,
        job_id: str
    ) -> Job| None:
        job = job_repository.get_job(session=session, job_id=job_id)
        return job

    @staticmethod
    def add_job_log(session: Session, job_id: str, message: str, level: str = "INFO"):
        """
        Ajoute une entrée horodatée dans la colonne JSON logs du job.
        """
        job = JobService.get_job(session=session, job_id=job_id)
        if job:
            # Création de l'entrée
            new_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message
            }
            
            # /!\ Astuce SQLAlchemy : Pour que l'ORM détecte le changement dans une liste JSON
            # il est souvent plus sûr de réassigner la liste entière.
            current_logs = list(job.logs) # Copie de la liste
            current_logs.append(new_entry)
            job.logs = current_logs