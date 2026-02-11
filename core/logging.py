import logging
import sys

def setup_logging():
    # Configuration du format : Heure | Niveau | Nom du logger | Message
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s : %(message)s"
    
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),  # Console
            logging.FileHandler("app.log")      # Fichier pour historique
        ]
    )

    # On réduit le bruit des bibliothèques tierces
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("RAG-App")