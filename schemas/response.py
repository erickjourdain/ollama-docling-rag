from pydantic import BaseModel, Field

class PDFConversionResponse(BaseModel):
    """Réponse après la conversion d'un PDF en Markdown"""
    markdown_uuid: str = Field(..., description="UUID du fichier Markdown converti à partir du PDF")
    conversion_time: float = Field(..., description="Durée de la conversion en secondes")

class ViewMDResponse(BaseModel):
    """Réponse pour l'affichage d'un fichier Markdown converti"""
    markdown: str = Field(..., description="Contenu Markdown du fichier converti")

class InfoMDResponse(BaseModel):
    """Réponse pour les informations d'un fichier Markdown converti"""
    markdown_uuid: str = Field(..., description="UUID du fichier Markdown converti")
    creation_date: str = Field(..., description="Date de création du fichier Markdown")
    size: int = Field(..., description="Taille du fichier Markdown en octets")