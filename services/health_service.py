from sqlalchemy.ext.asyncio import AsyncSession

from schemas import HealthResponse

from .collection_service import CollectionService
from .db_vectorielle_service import DbVectorielleService
from .llm_service import LlmService


class HealthService:

    @staticmethod
    async def check(
        db: AsyncSession,
        vector_db: DbVectorielleService
    ) -> HealthResponse:
        sqlite_ok = await CollectionService.check_db(db)
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