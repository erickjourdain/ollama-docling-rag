from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm  import Session

from db.models import Job

def update_job_progress(
    session: Session, 
    job_id: str, 
    progress: str,
    status: str,
    error: str | None = None
):
    job = session.get(Job, job_id)
    if job:
        job.progress = progress
        job.status = status
        job.error = error
        session.commit()

def finish_job(
    session: Session,
    job_id: str
):
    job = session.get(Job, job_id)
    if job:
        job.finished_at = datetime.now()
        session.commit()

def create_job(
    session: Session,
    job_id: str,
    filename: str | None
):
    new_job=Job(id=job_id, input_data=filename)
    session.add(new_job)
    session.commit()
    session.refresh(new_job)
    return new_job

def get_job(
    session: Session,
    job_id: str
) -> Job | None:
    stmt = select(Job).where(Job.id == job_id)
    result = session.execute(stmt)
    return result.scalar_one_or_none()