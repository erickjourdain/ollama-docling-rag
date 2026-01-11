from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Struture de stockage des documents
    temp_directory: str = "./temp" # répertoire temportaire de stockage des fichiers à insérer
    md_dir: str = "./data/files" # répertoire de stockage des fichiers markdown
    image_resolution_scale: float = 2.0

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