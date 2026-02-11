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
        """_summary_

        Args:
            session (Session): session d'accès à la base de données
            vector_db (DbVectorielleService): service d'accès à la base de données vectorielle

        Raises:
            Exception: erreur lors de la vérification des services

        Returns:
            HealthResponse: état de l'application
        """
        try:
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
        except Exception as e:
            raise Exception(e)