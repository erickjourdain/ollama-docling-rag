from pydantic import BaseModel, Field

class PDFConversionMd(BaseModel):
    """Réponse après la conversion d'un PDF en Markdown"""
    markdown_uuid: str = Field(..., description="UUID du fichier Markdown converti à partir du PDF")
    conversion_time: float = Field(..., description="Durée de la conversion en secondes")