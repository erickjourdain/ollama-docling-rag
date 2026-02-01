from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, text

from db.models import CollectionMetadata, DocumentMetadata

class CollectionRepository:
    
    @staticmethod
    async def list_collections(
        db_session: AsyncSession,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[CollectionMetadata]:
        """liste paginée des collections

        Args:
            db_session (AsyncSession): session sqlite
            limit (int, optional): nombre max de collections retournées. Defaults to 50.
            offset (int, optional): offset. Defaults to 0.

        Returns:
            Sequence[CollectionMetadata]: liste de collections
        """
        stmt = (
            select(CollectionMetadata)
            .order_by(CollectionMetadata.date_creation.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db_session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_by_name(
        db: AsyncSession, 
        name: str
    ) -> CollectionMetadata | None:
        """Récupérer une collection à partir de son nom

        Args:
            db_session (AsyncSession): session sqlite
            name (str): nom de la collection

        Returns:
            CollectionMetadata | None: collection recherchée ou None
        """
        stmt = select(CollectionMetadata).where(
            CollectionMetadata.name == name
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(
        db: AsyncSession,
        collection: CollectionMetadata
    ) -> None:
        """Ajout d'une collection

        Args:
            db_session (AsyncSession): session sqlite
            collection (CollectionMetadata): collection à ajouter
        """
        db.add(collection)

    @staticmethod
    async def get_document_collection(
        db: AsyncSession,
        collection_id: str,
        document_name: str,
    ) -> DocumentMetadata | None:
        stmt = (
            select(DocumentMetadata)
            .where(
                (DocumentMetadata.collection_id == collection_id) &
                (DocumentMetadata.filename == document_name)
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_collection_documents(
        db: AsyncSession,
        collecion_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[DocumentMetadata]:
        stmt = (
            select(DocumentMetadata)
            .where(
                (DocumentMetadata.collection_id == collecion_id)
            )
            .limit(limit=limit)
            .offset(offset=offset)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def delete_documents(
        db: AsyncSession,
        collection_id: str
    ) -> None:
        """Suppression d'un document d'une collection

        Args:
            db (AsyncSession): session sqlite
            collection_id (str): id de la collection
        """
        stmt = delete(DocumentMetadata).where(
            DocumentMetadata.collection_id == collection_id
        )
        await db.execute(stmt)

    @staticmethod
    async def delete_collection(
        db: AsyncSession,
        collection_id: str
    ) -> None:
        """Suppresion d'une collection

        Args:
            db (AsyncSession): session sqlite
            collection_id (str): id de la collection
        """
        stmt = delete(CollectionMetadata).where(
            CollectionMetadata.id == collection_id
        )
        await db.execute(stmt)

    @staticmethod
    async def add_document(
        db: AsyncSession,
        document: DocumentMetadata
    ) -> None:
        db.add(document)

    @staticmethod
    async def check_sqlite(db: AsyncSession) -> bool:
        try:
            await db.execute(text("SELECT 1"))
            return True
        except Exception:
            return False