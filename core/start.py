from core.config import settings
from services.db_service import DbService


def init_app():
    """Bootstrap de l'application
    """
    # Vérification de l'existance de le table / collection pour gestion des documents
    doc_table = settings.db_documents
    db_service = DbService()
    tables = db_service.list_tables()
    # Création de la table / collection
    if doc_table not in tables:
        db_service.create_table(settings.db_documents, True)
    