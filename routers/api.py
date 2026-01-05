from pathlib import Path

from ollama import GenerateResponse
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile

from models import HealthResponse, Model, ProcessingResponse, QueryRequest
from services import (
    ConversionService,
    ChunkingService,
    LanceDBService,
    OllamaService
)
from config import settings

load_dotenv()

router = APIRouter()

@router.post(
    "/save-pdf",
    response_model=ProcessingResponse,
    summary="Traiter un PDF et le stocker dans ChromaDB",
    description="""
    Traite un fichier PDF complet et le stocke dans une collection ChromaDB.
    """,
    tags=["Traitement PDF"]
)
async def process_pdf(
    file: UploadFile = File(..., description="Fichier PDF à traiter"),
    collection_name: str = "Nom de la collection ChromaDB à utiliser pour le stockage"
) -> ProcessingResponse:
    """Traitement d'un fichier PDF et stockage dans ChromaDB"""
    # Vérification que le fichier fouri est bien un fichier pdf
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")
    
    try:
        # Enregistrement du fichier dans le répertoire temporaire
        pdf_bytes = await file.read()
        temp_dir = Path(settings.temp_directory)
        temp_dir.mkdir(parents=True, exist_ok=True)
        with open(temp_dir / file.filename, "wb") as f:
            f.write(pdf_bytes)

        # Conversion du fichier pdf
        conversion_service = ConversionService()
        conversion_result = conversion_service.convert_pdf_to_md(temp_dir / file.filename, collection_name)
        # Suppression du fichier temporaire
        (temp_dir / file.filename).unlink()

        # Vérifie l'existance de la collection / table
        lancedb_service = LanceDBService()
        liste_collections = lancedb_service.list_tables()
        if collection_name not in liste_collections:
            lancedb_service.create_table(collection_name)

        # Chunk du document
        chunking_service = ChunkingService(filename=file.filename)
        chunking_result = chunking_service.basic_chunking(document=conversion_result.document)

        # Enregistrement des chunks dans la base de données
        lancedb_service.insert_data(chunks=chunking_result.chunks, collection_name=collection_name)

        return ProcessingResponse(
            success=True, 
            detail="PDF traité et stocké avec succès.",
            conversion_time=conversion_result.conversion_time,
            embedding_time=chunking_result.embedding_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF: {str(e)}")
    
@router.delete(
        "/collection",
        summary="Supprime une collection / table",
        description="""Supression d'une collection / table de la base de données""",
        tags=["Base de données"]
)
async def delete_collection(collection_name: str) -> bool:
    try:
        lancedb_service = LanceDBService()
        lancedb_service.delete_table(collection_name=collection_name)
        return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression de la table: {str(e)}")
    
@router.post(
        "/query",
        summary="Interroge la base de connaissances",
        description="""
        Excute une requête sur la base de connaissances:
        - interogation de la base de connaissances
        - envoi du contexte au LLM pour création de la réponse
        """,
        tags=["Query base connaissances"]
)
async def query(req: QueryRequest) -> GenerateResponse:
    """Exécution d'une requête utilisateur sur le système RAG

    Args:
        req (QueryRequest): Information sur la requête à effectuer
            query: requête de l'utilisateur
            collection_name: nom de la collection à interroger
            model: nom du modèle à utiliser (optionel)

    Raises:
        HTTPException: Erreur lors de l'éxecution de la fonction

    Returns:
        GenerateResponse | None: Réponse 
    """
    try:
        lancedb_service = LanceDBService()
        ollama_service =  OllamaService()
        model = req.model if req.model is not None else settings.ollama_model
        # Tester présence du modèle
        models = ollama_service.list_models()
        vectordb_query = ollama_service.vectordb_query(req.query, model=model)
        chunks = lancedb_service.query_db(vectordb_query, req.collection_name)
        if len(chunks):
            chunks = ollama_service.rerank_chunks_llm(query=req.query,chunks=chunks)
        reponse = ollama_service.create_answer(chunks=chunks, query=req.query, model=model)
        return reponse
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF: {str(e)}") 

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Vérifier l'état de santé de l'API",
    description="""
    Vérifie l'état de fonctionnement de tous les composants du système:
    - API FastAPI
    - Serveur Ollama
    - Base de données ChromaDB
    - Modèles Ollama disponibles
    """,
    tags=["Système"]
)
async def health_check() -> HealthResponse:
    try:
        ollama_service = OllamaService()
        models_list = ollama_service.list_models()
        ollama_status = "ok"
    except Exception:
        raise HTTPException(status_code=503, detail="serveur ollama injoignable")
    
    try:
        lancedb_service = LanceDBService()
        lancedb_service.list_tables()
        lancedb_service = "ok"
    except Exception:
        raise HTTPException(status_code=503, detail="erreur connexion ChromaDB")
    
    return HealthResponse(
        api="ok",
        ollama=ollama_status,
        lancedb=lancedb_service,
        models_available=models_list
    )

@router.get(
    "/models",
    response_model=list[Model],
    summary="Liste des modèles LLM disponibles",
    description="Récupère la liste des modèles disponibles pour interrogation",
    tags=["Système"]
)
async def list_models() -> list[Model]:
    try:
        ollama_service = OllamaService()
        return ollama_service.list_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du chargement des modèles: {str(e)}")
