from pathlib import Path
from pydantic import BaseModel, Field
from docling_core.types.doc.document import DoclingDocument

class ConvertPdfResponse(BaseModel):
    """Réponse conversion d'un fichier PDF"""
    document: DoclingDocument = Field(..., description="Contenu du document au format docling")
    markdown: Path = Field(..., description="Nom du ficher markdown")
    conversion_time: float = Field(..., description="Temps de conversion du fichier")