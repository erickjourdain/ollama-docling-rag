import time
import shutil
from fastapi import UploadFile
from pathlib import Path
from sqlalchemy.orm import Session

from docling_core.types.doc.base import ImageRefMode
from docling_core.types.doc.document import DoclingDocument

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PaginatedPipelineOptions,
    PdfPipelineOptions,
    TableStructureOptions,
    TableFormerMode
)
from docling.document_converter import DocumentConverter, PdfFormatOption, WordFormatOption


from core.config import settings
from core.exceptions import DocumentParsingError, RAGException
from core.security import hash_file
from schemas import ConvertPdfResponse
from repositories.collections_repository import CollectionRepository

class ConversionService:
    """Service pour gérer l'envoi des fichiers pdf"""
    
    @staticmethod
    async def save_imported_file(
        file: UploadFile,
        collection_name: str,
        doc_id: str
    ) -> Path:
        """Sauvegarde du fichier pdf

        Args:
            file (UploadFile): fichier à sauvegarder
            collection_name (str): nom de la base de connaissance d'insertion du fichier

        Raises:
            ValueError: Erreur lors de l'enregistrement du fichier

        Returns:
            Path: chemin du fichier sauvegardé
        """
        try:
            # Gestion du répertoires de stockage
            md_dir = Path(settings.STATIC_DIR) / collection_name
            md_dir.mkdir(exist_ok=True)

            # Enregistrement du fichier
            if file.filename is None or not file.filename.lower().endswith((".pdf", ".docx")):
                raise ValueError("Format de fichier non supporté. Seuls les fichiers PDF et DOCX sont autorisés.")
            filename = f"{doc_id}.{file.filename.split('.')[-1]}"
            path = md_dir / filename
            pdf_bytes = await file.read()
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            return path
        except Exception as e:
            raise ValueError(e)
        
    @staticmethod
    def check_md5(
        file_path: Path,
        collection_id: str,
        session: Session
    ) -> bool:
        """Vérification de la présence du fichier dans la collection

        Args:
            filepath (Path): chemin du fichier à vérifier
            collection_id (str): l'identifant de la collection
            session (Session): session d'accès à la base de données

        Raises:
            ValueError: erreur lors de la vérification de la présence du fichier

        Returns:
            bool: présence du fichier
        """
        try:
            md5 = hash_file(file_path=file_path)
            document = CollectionRepository.get_document_collection_by_md5(
                session=session,
                collection_id=collection_id,
                md5=md5
            )
            return document is not None
        except Exception as e:
            raise ValueError(e)
        
    @staticmethod
    def save_converted_markdown(
        convert_doc: DoclingDocument,
        collection_name: str,
        doc_id: str
    ) -> Path:
            
        try:
            # Gestion des répertoires de stockage
            md_dir = Path(settings.STATIC_DIR) / collection_name
            md_dir.mkdir(exist_ok=True)
            md_filename = md_dir / f"{doc_id}.md"
            
            images_dir = md_dir / "images" / doc_id
            if images_dir.exists():
                shutil.rmtree(images_dir)

            # Sauvegarde du fichier Markdown
            convert_doc.save_as_markdown(
                filename=md_filename,
                artifacts_dir=Path("images") / doc_id, 
                image_mode=ImageRefMode.REFERENCED
            )

            return md_filename

        except Exception as e:
            raise ValueError(e)

    @staticmethod
    def convert_to_md(file_path: Path | str, collection_name: str, doc_id: str) -> ConvertPdfResponse:
        """_summary_

        Args:
            file_path (Path | str): chemin vers le fichier à traiter
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
            try: 
                # Configuration des options de conversion PDF
                pdf_pipeline_options = PdfPipelineOptions()
                pdf_pipeline_options.do_ocr = False
                pdf_pipeline_options.images_scale = settings.IMAGE_RESOLUTION_SCALE
                pdf_pipeline_options.generate_picture_images = True
                pdf_pipeline_options.do_table_structure = True
                pdf_pipeline_options.table_structure_options = TableStructureOptions(
                    mode = TableFormerMode.ACCURATE
                )
                pdf_pipeline_options.accelerator_options = AcceleratorOptions(
                    num_threads=4, device=AcceleratorDevice.AUTO
                )

                # Configuration des options de conversion DOCX
                docx_pipepline_options = PaginatedPipelineOptions()
                docx_pipepline_options.images_scale = settings.IMAGE_RESOLUTION_SCALE
                docx_pipepline_options.generate_picture_images = True
                docx_pipepline_options.accelerator_options = AcceleratorOptions(
                    num_threads=4, device=AcceleratorDevice.AUTO
                )

                # Conversion du document
                start_time = time.time()
                doc_converter = DocumentConverter(
                    allowed_formats=[InputFormat.PDF, InputFormat.DOCX],
                    format_options={
                        InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_pipeline_options),
                        InputFormat.DOCX: WordFormatOption(pipeline_options=docx_pipepline_options)
                    }
                )
                convert_doc = doc_converter.convert(file_path)
            
            except Exception as e:
                raise DocumentParsingError("Erreur docling", str(e))
            
            md_filename = ConversionService.save_converted_markdown(
                convert_doc=convert_doc.document,
                collection_name=collection_name,
                doc_id=doc_id
            )

            # Calcul du temps écoulé
            elapsed_time = time.time() - start_time

            # Retour de la réponse
            return ConvertPdfResponse(
                document=convert_doc.document,
                markdown=md_filename,
                conversion_time=elapsed_time
            )
        
        except RAGException as re:
            raise re

        except Exception as e:
            raise e

        