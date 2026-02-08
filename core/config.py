import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Nombre maximum de worker de l'application
    max_worker: int = 1

    # Struture de stockage des documents
    temp_dir: str = "./temp" # répertoire temportaire de stockage des fichiers à insérer

    # Static files
    static_url: str= "/data"
    static_dir: Path = Path("data/files")
    image_resolution_scale: float = 2.0

    # Sqlite Database
    sqlite_db_dir: str = "./data/metadata.db" # chemin de la base

    # Chromadb Databse
    chroma_db_dir: str = "./chromadb" # répertoire de stockage de la base de données

    # LLM
    OLLAMA_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL: str = "gemma3:4b" # nom du modèle llm utilisé par défaut
    LLM_EMBEDDINGS_MODEL: str = "mxbai-embed-large:latest" # nom du modèle d'embeddings utilisé par défaut

    # API
    api_title: str = "Ollama Docling RAG API" # nom de l'application
    api_version: str = "1.0.0" # version de l'application
    api_description: str = "API de gestion d'un système de recherche d'information basée sur Docling et Ollamo."

    # Premier utilisateur
    FIRST_USER_USERNAME: str = os.environ.get("ADMIN_LOG", "admin")
    FIRST_USER_PWD: str = os.environ.get("ADMON_PWD", "admin")
    FIRST_USER_EMAIL: str = os.environ.get("ADMIN_EMAIL", "test@test.com")

settings = Settings()