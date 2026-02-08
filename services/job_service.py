from sqlalchemy.orm  import Session

from db.models import Job
from repositories import job_repository


def get_job(
    session: Session,
    job_id: str
) -> Job| None:
    job = job_repository.get_job(session=session, job_id=job_id)
    return job