import os
import time
import shutil
import uuid
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

from core.config import settings
from schemas import ConvertPdfResponse
from schemas.conversion import PDFConversionMd

class ConversionService:
    """Service pour gérer l'envoi des fichiers pdf"""

    def __init__(self):
        pass

    def convert_pdf_to_md(self, file_path: Path | str, collection_name: str) -> ConvertPdfResponse:
        """_summary_

        Args:
            file_path (Path | str): chemin vers le fichier pdf à traiter
            collection_name (str): nom de la collection / table pour le stockage des données

        Raises:
            Exception: Erreur lors de l'éxécution de la fonction

        Returns:
            ConvertPdfResponse: Modèle représentant la réponse intégrant
                le document au format Docling
                le nom du fichier md sauvegardé avec son chemin
                le temps de traitement de la conversion
        """

        try: 
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
            md_dir = Path(settings.static_dir) / collection_name
            md_dir.mkdir(exist_ok=True)
            doc_uuid = convert_doc.input.file.stem
            md_filename = md_dir / f"{doc_uuid}.md"
            
            # Suppression des fichiers existants
            if md_filename.exists():
                md_filename.unlink()
            
            images_dir = md_dir / "images" / doc_uuid
            if images_dir.exists():
                shutil.rmtree(images_dir)

            # Calcul du temps écoulé
            elapsed_time = time.time() - start_time

            # Sauvegarde du fichier Markdown
            convert_doc.document.save_as_markdown(
                filename=md_filename,
                artifacts_dir=Path("images") / doc_uuid, 
                image_mode=ImageRefMode.REFERENCED
            )

            # Retour de la réponse
            return ConvertPdfResponse(
                document=convert_doc.document,
                markdown=md_filename,
                conversion_time=elapsed_time
            )
        
        except Exception as e:
            raise Exception(e)
        
    def pdf_to_md(self, file_path: Path | str) -> PDFConversionMd:
        """Convertir un fichier PDF en Markdown et sauvegarder le résultat.

        Args:
            file_path (Path | str): Chemin vers le fichier PDF à convertir.
            output_md_path (Path | str): Chemin où sauvegarder le fichier Markdown converti.

        Raises:
            Exception: Erreur lors de la conversion du PDF.
        """
        try:
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
            doc_uuid = uuid.uuid4()
            md_filename = f"{doc_uuid}.md"
            full_md_path = os.path.join(Path(settings.static_temp_dir), md_filename)
            relative_img_dir = Path("images") / str(doc_uuid)
            full_img_dir = os.path.join(Path(settings.static_temp_dir), relative_img_dir)

            # Suppression des fichiers existants
            if Path(full_md_path).exists():
                Path(full_md_path).unlink()

            if Path(full_img_dir).exists():
                shutil.rmtree(full_img_dir)

            # Sauvegarde du fichier Markdown
            convert_doc.document.save_as_markdown(
                filename=full_md_path,
                artifacts_dir=relative_img_dir, 
                image_mode=ImageRefMode.REFERENCED
            )

            # Calcul du temps écoulé
            elapsed_time = time.time() - start_time

            return PDFConversionMd(
                markdown_uuid=str(doc_uuid),
                conversion_time=elapsed_time
            )
        
        except Exception as e:
            raise Exception(e)
        