import logging
from pathlib import Path

from db.database import sync_engine
from db.models import Base
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_app():
    """Bootstrap de l'application"""
    # Création des répertoires de stockage si nécéssaire
    md_dir = Path(settings.STATIC_DIR)
    md_dir.mkdir(exist_ok=True)

    # Initialisation de la base de données sqlite
    with sync_engine.begin() as conn:
        Base.metadata.create_all(conn)
        logger.info("initialisation base de données sqlite réalisé")

    