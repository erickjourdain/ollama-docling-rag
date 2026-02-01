from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Struture de stockage des documents
    temp_dir: str = "./temp" # répertoire temportaire de stockage des fichiers à insérer

    # Static files
    static_url: str= "/data"
    static_dir: Path = Path("data/files")
    static_temp_dir: Path = static_dir / "temp"
    image_resolution_scale: float = 2.0

    # Sqlite Database
    sqlite_db_dir: str = "./data/metadata.db" # chemin de la base

    # Chromadb Databse
    chroma_db_dir: str = "./chromadb" # répertoire de stockage de la base de données

    # Lance Database
    db_dir: str = "./lancedb" # répertoire de stockage de la base de données
    db_documents: str = "documents" # nom de la collections pour le stockage des documents
    db_collections: str = "collections" # nom de la collections pour le stockage des collections

    # Modèle LLM
    llm_model: str = "gemma3:4b" # nom du modèle llm utilisé par défaut
    llm_embedding_model: str = "mxbai-embed-large:latest" # nom du modèle d'embeddings utilisé par défaut

    # API
    api_title: str = "Ollama Docling RAG" # nom de l'application
    api_version: str = "1.0.0" # version de l'application
    api_description: str = "API de gestion d'un système de recherche d'information basé sur Docling, Ollama et Lancedb."

settings = Settings()