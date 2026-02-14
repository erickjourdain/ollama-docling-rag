from fastapi import Request

from services import DbVectorielleService


def get_vector_db_service(request: Request) -> DbVectorielleService:
    return request.app.state.vector_db_service