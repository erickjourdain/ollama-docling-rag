from fastapi import Request

from services import JobRunner

def get_job_runner(request: Request) -> JobRunner:
    return request.app.state.job_runner