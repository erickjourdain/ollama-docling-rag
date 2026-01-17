from pathlib import Path

from core.config import settings
from services.db_service import DbService

def init_app():
    """Bootstrap de l'application
    """
    # Création des répertoires de stockage si nécéssaire
    md_dir = Path(settings.static_dir) / "temp"
    md_dir.mkdir(exist_ok=True)
    tmp_dir = Path(settings.temp_dir)
    tmp_dir.mkdir(exist_ok=True)
    # Vérification de l'existence de la table / collection pour gestion des documents
    db_service = DbService()
    tables = db_service.list_tables()
    # Création des tables / collections de stockage des informations collections et documents
    if settings.db_collections not in tables and settings.db_documents not in tables:
        db_service.create_info_tables()
    