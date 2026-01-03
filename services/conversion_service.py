import time
import shutil
from pathlib import Path

from docling_core.types.doc.base import ImageRefMode

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode
)
from docling.document_converter import DocumentConverter, PdfFormatOption

from config import settings
from models import ConvertPdfResponse

class ConversionService:
    """Service pour gérer l'envoi des fichiers pdf"""

    def __init__(self):
        pass

    def convert_pdf_to_md(self, file_path: Path | str, collection_name: str) -> ConvertPdfResponse:
        """Convertit un fichier PDF en Markdown"""

        # Configuration des options de conversion PDF
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.images_scale = settings.image_resolution_scale
        pipeline_options.generate_picture_images = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options = TableStructureOptions(
            mode = TableFormerMode.ACCURATE
        )
        pipeline_options.accelerator_options = AcceleratorOptions(
            num_threads=4, device=AcceleratorDevice.AUTO
        )

        # Conversion du document
        start_time = time.time()
        doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        convert_doc = doc_converter.convert(file_path)

        # Gestion des répertoires de stockage
        md_dir = Path(settings.md_dir) / collection_name
        md_dir.mkdir(exist_ok=True)
        doc_filename = convert_doc.input.file.stem
        md_filename = md_dir / f"{doc_filename}.md"
        
        # Suppression des fichiers existants
        if md_filename.exists():
            md_filename.unlink()
        
        images_dir = md_dir / "images" / doc_filename
        if images_dir.exists():
            shutil.rmtree(images_dir)

        # Calcul du temps écoulé
        elapsed_time = time.time() - start_time

        # Sauvegarde du fichier Markdown
        convert_doc.document.save_as_markdown(
            filename=md_filename,
            artifacts_dir=Path("images") / doc_filename, 
            image_mode=ImageRefMode.REFERENCED
        )

        # Retour de la réponse
        return  ConvertPdfResponse(
            document=convert_doc.document,
            markdown=md_filename,
            conversion_time=elapsed_time
        )