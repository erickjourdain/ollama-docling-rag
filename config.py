from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Struture de stockage des documents
    temp_directory: str = "./temp"
    md_dir : str = "./data/files"
    image_resolution_scale: float = 2.0

    # lancedb
    lancedb_dir : str = "./lancedb"

    # Chromadb
    chromadb_persist_directory: str = "./chroma_db"

    # Ollama
    ollama_model: str = "qwen2.5:7b"
    ollama_embedding_model: str = "mxbai-embed-large:latest"

    # API
    api_title: str = "Ollama Docling RAG"
    api_version: str = "1.0.0"
    api_description: str = "API de gestion d'un système de recherche d'information basé sur Docling, Ollama et Chromadb."

settings = Settings()