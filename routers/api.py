from ollama import Client
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile

from models import HealthResponse, ProcessingResponse, QueryRequest
from services import (
    ChromaDBService,
    ConversionService,
    ChunkingService,
    QueryService
)
from config import settings

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
        conversion_result = ConversionService().convert_pdf_to_md(temp_dir / file.filename, collection_name)
        # Suppression du fichier temporaire
        (temp_dir / file.filename).unlink()
        # Chunk du document
        chunknig_result = ChunkingService().basic_chunking(
            document=conversion_result.document, 
            collection_name=collection_name, 
            file_name=file.filename
        )

        return ProcessingResponse(
            success=True, 
            detail="PDF traité et stocké avec succès.",
            conversion_time=conversion_result.conversion_time,
            embedding_time=chunknig_result.embedding_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF: {str(e)}")
    
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
async def query(req: QueryRequest):
    try:
        chunks = QueryService().query_db(req.query, req.collection_name)
        chunks = QueryService().rerank_chunks_llm(query=req.query,chunks=chunks)
        context = QueryService().define_context(chunks)
        response = QueryService().create_answer(context=context, query=req.query)
        return response.response
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
    tags=["Système"])
async def health_check() -> HealthResponse:
    try:
        client = Client(host=settings.ollama_base_url)
        models_list = client.list()
        ollama_status = "ok"
        models = [model['model'] for model in models_list.get('models', [])]
    except Exception:
        raise HTTPException(status_code=503, detail="serveur ollama injoignable")
    
    try:
        ChromaDBService().list_collections()
        chromadb_status = "ok"
    except Exception:
        raise HTTPException(status_code=503, detail="erreur connexion ChromaDB")
    
    return HealthResponse(
        api="ok",
        ollama=ollama_status,
        chromadb=chromadb_status,
        models_available=models
    )