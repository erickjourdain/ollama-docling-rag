from datetime import datetime
import uuid
from pathlib import Path
from typing import Sequence
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from services import ChunkingService, ConversionService, DbVectorielleService
from repositories.collections_repository import CollectionRepository
from db.models import CollectionMetadata, DocumentMetadata
from schemas import ProcessingResponse

class CollectionService:

    @staticmethod
    async def list_collections(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[CollectionMetadata]:
        """Liste des collections paginée

        Args:
            db (AsyncSession): session sqlite
            limit (int, optional): nombre de collections max à retourner. Defaults to 50.
            offset (int, optional): offset. Defaults to 0.

        Returns:
            Sequence[CollectionMetadata]: liste de collections
        """
        return await CollectionRepository.list_collections(
            db,
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    async def get_by_name(
        db: AsyncSession,
        name: str
    ) -> CollectionMetadata | None:
        """_summary_

        Args:
            db (AsyncSession): session sqlite
            name (str): nom de la collection à récupérer

        Returns:
            CollectionMetadata | None: collection recherchée ou None
        """
        return await CollectionRepository.get_by_name(
            db=db,
            name=name
        )
    
    @staticmethod
    async def create_collection(
        db: AsyncSession,
        vector_db: DbVectorielleService,
        name: str,
        description: str | None,
        user_id: str
    ) -> CollectionMetadata:
        """Création d'une collection dans la base de données sqlite et chromadb

        Args:
            db (AsyncSession): session sqlite
            name (str): nom de la collection
            description (str | None): description de la collection
            user_id (str): id de l'utilisateur

        Raises:
            ValueError: erreur lors de la création

        Returns:
            CollectionMetadata: collection insérée
        """
        # Vérifier existence
        existing = await CollectionRepository.get_by_name(db, name)
        if existing:
            raise ValueError("La collection existe déjà dans la base")

        # Créer l’objet DB
        collection = CollectionMetadata(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_by=user_id
        )

        try:
            # DB first
            await CollectionRepository.create(db, collection)
            await db.flush()  # force INSERT sans commit

            # Side-effect : Chroma
            vector_db.create_collection(collection_name=name)

            # Commit final
            await db.commit()

        except Exception:
            await db.rollback()
            raise

        return collection
    
    @staticmethod
    async def document_in_collection(
        db: AsyncSession,
        collection_name: str,
        document_name: str
    ) -> bool:
        """Recherche un document dans une collection

        Args:
            db (AsyncSession): session sqlite
            collection_name (str): nom de la collection
            document_name (str): nom du document

        Raises:
            ValueError: erreur lors de la recherche du document

        Returns:
            bool: état du résultat de la recherche
        """
        # Vérifier existence collection
        collection = await CollectionRepository.get_by_name(db=db, name=collection_name)
        if not collection:
            raise ValueError("Collection not found")
        # Vérifier existence document
        document = await CollectionRepository.get_document_collection(
            db=db,
            collection_id=str(collection.id),
            document_name=document_name
        )
        return (document is not None)
    
    @staticmethod
    async def documents_collection(
        db: AsyncSession,
        collection_name: str,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[DocumentMetadata]:
        # Vérifier existence collection
        collection = await CollectionRepository.get_by_name(db=db, name=collection_name)
        if not collection:
            raise ValueError("Collection not found")
        # Récupérer la liste des documents de la collection
        return await CollectionRepository.get_collection_documents(
            db=db, 
            collecion_id=str(collection.id),
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    async def delete_collection(
        db: AsyncSession,
        vector_db: DbVectorielleService,
        name: str,
    ):
        """Suppression d'une collection

        Args:
            db (AsyncSession): session sqlite
            name (str): nom de la collection

        Raises:
            ValueError: erreur levée lors de la suppression
        """
        # Vérifier existence
        collection = await CollectionRepository.get_by_name(db, name)
        if not collection:
            raise ValueError("Collection not found")

        try:
            # Supprimer côté Chroma
            vector_db.delete_collection(collection_name=name)

            # Supprimer les documents DB
            await CollectionRepository.delete_documents(
                db=db,
                collection_id=str(collection.id)
            )

            # Supprimer la collection DB
            await CollectionRepository.delete_collection(
                db=db,
                collection_id=str(collection.id)
            )

            # Commit final
            await db.commit()

        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def insert_pdf(
        file: UploadFile,
        collection_name: str,
        db: AsyncSession,
        vector_db: DbVectorielleService
    ):
        # Vérification que le fichier fouri est bien un fichier pdf
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise ValueError("Le fichier fourni n'est pas un fichier pdf")

        try:
            # Vérification que le document n'est pas déjà présent dans la collection
            if await CollectionService.document_in_collection(
                db=db,
                collection_name=collection_name,
                document_name=file.filename
            ):
                raise ValueError("Un fichier avec le même nom est déjà inséré dans la collection")
            
            # Enregistrement du fichier dans le répertoire temporaire
            pdf_bytes = await file.read()
            temp_dir = Path(settings.temp_dir)
            temp_dir.mkdir(parents=True, exist_ok=True)
            with open(temp_dir / file.filename, "wb") as f:
                f.write(pdf_bytes)

            # Conversion du fichier pdf
            conversion_service = ConversionService()
            conversion_result = conversion_service.convert_pdf_to_md(
                file_path=temp_dir / file.filename, 
                collection_name=collection_name
            )
            # Suppression du fichier temporaire
            (temp_dir / file.filename).unlink()

            # Enregistrement des informations liées au document inséré
            collection = await CollectionRepository.get_by_name(db=db, name=collection_name)
            if collection is None:
                raise ValueError("La collection n'exsite pas")
            id = str(uuid.uuid4())
            document = DocumentMetadata(
                id=id,
                filename=file.filename,
                collection_id=collection.id,
                inserted_by="a12b8b9d-e0b0-4e84-a7c0-36da6ec16907",
                date_insertion=datetime.now()
            )
            await CollectionRepository.add_document(db=db, document=document)
            await db.flush()  # force INSERT sans commit

            # Chunk du document
            chunking_service = ChunkingService(filename=file.filename)
            chunking_result = chunking_service.basic_chunking(
                document=conversion_result.document, 
                document_id=id
            )

            # Enregistrement des chunks dans la base de données vectorielles
            vector_db.insert_chunk(
                collection_name=collection_name,
                chunks=chunking_result.chunks
            )

            await db.commit()

            return ProcessingResponse(
                success=True, 
                detail="PDF traité et stocké avec succès.",
                conversion_time=conversion_result.conversion_time,
                embedding_time=chunking_result.elapsed_time
            )
            
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def check_db(db: AsyncSession) -> bool:
        try:
            return await CollectionRepository.check_sqlite(db=db)
        except Exception:
            return False