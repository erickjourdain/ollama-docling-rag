from core.config import settings
from services.db_service import DbService

def init_app():
    """Bootstrap de l'application
    """
    # Vérification de l'existance de le table / collection pour gestion des documents
    db_service = DbService()
    tables = db_service.list_tables()
    # Création des tables / collections de stockage des informations collections et documents
    if settings.db_collections not in tables and settings.db_documents not in tables:
        db_service.create_info_tables()
    