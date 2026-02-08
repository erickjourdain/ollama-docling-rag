from sqlalchemy.orm import Session

from schemas import HealthResponse

from .collection_service import CollectionService
from .db_vectorielle_service import DbVectorielleService
from .llm_service import LlmService


class HealthService:

    @staticmethod
    def check(
        session: Session,
        vector_db: DbVectorielleService
    ) -> HealthResponse:
        sqlite_ok = CollectionService.check_db(session=session)
        chroma_ok = vector_db.check_db()
        ollama_status = LlmService().check_ollama()

        status = "ok" if (
            sqlite_ok and chroma_ok and ollama_status.ok
        ) else "degraded"

        return HealthResponse(
            status=status,
            sqlite=sqlite_ok,
            chromadb=chroma_ok,
            ollama=ollama_status
        )