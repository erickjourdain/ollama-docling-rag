from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from services import ConversionService, ChunkingService, DbService
from schemas import ProcessingResponse, DocumentInfo
from core.config import settings

router_insert = APIRouter(prefix="/insert", tags=["Insertion fichier"])

@router_insert.post(
    "/pdf",
    response_model=ProcessingResponse,
    summary="Traiter un PDF et le stocker dans ChromaDB",
    description="""
    Insertion d'un fichier PDF complet et stockage dans une collection / table.
    """
)
async def process_pdf(
    file: UploadFile = File(..., description="Fichier PDF à traiter"),
    collection_name: str = "Nom de la collection / table à utiliser pour le stockage",
) -> ProcessingResponse:
    """Traitement d'un fichier PDF et stockage dans la base de données"""
    # Vérification que le fichier fouri est bien un fichier pdf
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")
    
    try:
        # Vérification si le document est déjà dans la collection / table
        db_service = DbService()
        collection_info = db_service.get_collection_info(collection_name=collection_name)
        if file.filename in [doc.filename for doc in collection_info.documents]:
            raise Exception("Le fichier a déjà été inséré")

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
        liste_collections = db_service.list_tables()
        if collection_name not in liste_collections:
            db_service.create_chunk_table(collection_name)

        # Chunk du document
        chunking_service = ChunkingService(filename=file.filename)
        chunking_result = chunking_service.basic_chunking(document=conversion_result.document)

        # Enregistrement des informations liées au document inséré
        document = DocumentInfo(
            filename=file.filename,
            collection_name=collection_name,
            insertion_date=datetime.now(),
            user="erick jourdain"
        )
        db_service.insert_documents(collection_name=collection_name, document=document)

        # Enregistrement des chunks dans la base de données
        db_service.insert_data(
            chunks=chunking_result.chunks, 
            collection_name=collection_name
        )
        
        return ProcessingResponse(
            success=True, 
            detail="PDF traité et stocké avec succès.",
            conversion_time=conversion_result.conversion_time,
            embedding_time=chunking_result.embedding_time
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors du traitement du PDF: {str(e)}"
        )