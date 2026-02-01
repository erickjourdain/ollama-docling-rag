from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.util import rewrite_markdown_image_urls
from depencies.sqlite_session import get_db
from depencies.vector_db import get_vector_db_service
from schemas import PDFConversionResponse
from services import ConversionService
from schemas import ProcessingResponse, ViewMDResponse, InfoMDResponse
from core.config import settings
from services import CollectionService, DbVectorielleService

router_insert = APIRouter(prefix="/insert", tags=["Insertion fichier"])

@router_insert.post(
    "/pdf",
    response_model=ProcessingResponse,
    summary="Traiter un PDF et le stocker dans la base de données vectorielle",
    description="""
    Insertion d'un fichier PDF complet et stockage dans une collection / table.
    """
)
async def process_pdf(
    file: UploadFile = File(..., description="Fichier PDF à traiter"),
    collection_name: str = "",
    db: AsyncSession = Depends(get_db),
    vector_db: DbVectorielleService = Depends(get_vector_db_service)
) -> ProcessingResponse:
    """Traitement d'un fichier PDF et stockage dans la base de données"""

    
    try:
        return await CollectionService.insert_pdf(
            file=file, 
            collection_name=collection_name, 
            db=db,
            vector_db=vector_db
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors du traitement du PDF: {str(e)}"
        )
    
@router_insert.post(
    "/convert_pdf",
    response_model=PDFConversionResponse,
    summary="Convertir un PDF en Markdown",
    description="""
    Conversion d'un fichier PDF en Markdown sans insertion dans la base de données.
    """
)
async def convert_pdf(
    file: UploadFile = File(..., description="Fichier PDF à convertir")
) -> PDFConversionResponse:
    """Conversion d'un fichier PDF en Markdown sans insertion dans la base de données"""
    # Vérification que le fichier fourni est bien un fichier pdf
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un PDF.")
    
    try:
        # Enregistrement du fichier dans le répertoire temporaire
        pdf_bytes = await file.read()
        temp_dir = Path(settings.temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)
        with open(temp_dir / file.filename, "wb") as f:
            f.write(pdf_bytes)

        # Conversion du fichier pdf
        conversion_service = ConversionService()
        conversion_result = conversion_service.pdf_to_md(temp_dir / file.filename)
        # Suppression du fichier temporaire
        (temp_dir / file.filename).unlink()

        return PDFConversionResponse(
            markdown_uuid=conversion_result.markdown_uuid,
            conversion_time=conversion_result.conversion_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la conversion du PDF: {str(e)}"
        )
    
@router_insert.get(
    "/view_md/{md_uuid}",
    response_model=ViewMDResponse,
    summary="Afficher un fichier Markdown converti",
    description="""
    Affichage du contenu HTML d'un fichier Markdown converti.
    """
)
async def view_md(
    request: Request,
    md_uuid: str
) -> ViewMDResponse:
    """Affichage du contenu HTML d'un fichier Markdown converti"""
    try:
        temp_dir = Path(settings.static_temp_dir)
        md_file_path = temp_dir / f"{md_uuid}.md"
        if not md_file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier Markdown non trouvé.")
        
        content = md_file_path.read_text(encoding="utf-8")

        content = rewrite_markdown_image_urls(
            markdown=content,
            markdown_path=md_file_path,
            base_url=str(request.base_url).rstrip("/")
        )  

        return ViewMDResponse(markdown=str(content))
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de l'affichage du fichier Markdown: {str(e)}"
        )
    
@router_insert.get(
    "/list_md",
    response_model=list[InfoMDResponse],
    summary="Lister les fichiers Markdown convertis",
    description="""
    Liste des fichiers Markdown convertis présents dans le répertoire temporaire.
    """   
)
async def list_md() -> list[InfoMDResponse]:
    """Liste des fichiers Markdown convertis présents dans le répertoire temporaire"""
    try:
        temp_dir = Path(settings.static_temp_dir)
        md_files = [
            InfoMDResponse(
                markdown_uuid=f.stem,
                creation_date=datetime.fromtimestamp(f.stat().st_ctime).isoformat(),
                size=f.stat().st_size
            )
            for f in temp_dir.glob("*.md")
        ]
        return md_files
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la liste des fichiers Markdown: {str(e)}"
        )

@router_insert.delete(
    "/delete_md/{md_uuid}",
    response_model=dict,
    summary="Supprimer un fichier Markdown converti",
    description="""
    Suppression d'un fichier Markdown converti du répertoire temporaire.
    """
)
async def delete_md(
    md_uuid: str
) -> dict:
    """Suppression d'un fichier Markdown converti du répertoire temporaire"""
    try:
        temp_dir = Path(settings.static_temp_dir)
        md_file_path = temp_dir / f"{md_uuid}.md"
        if not md_file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier Markdown non trouvé.")

        # Suppression du fichier Markdown
        md_file_path.unlink()

        md_img_path = temp_dir / "images" / md_uuid
        if md_img_path.exists() and md_img_path.is_dir():
            # Suppression du répertoire d'images associé
            for img_file in md_img_path.iterdir():
                img_file.unlink()
            md_img_path.rmdir()

        return {"detail": "Fichier Markdown supprimé avec succès."}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erreur lors de la suppression du fichier Markdown: {str(e)}"
        )