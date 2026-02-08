from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import delete, select, text

from db.models import CollectionMetadata, DocumentMetadata

class CollectionRepository:
    
    @staticmethod
    def list_collections(
        session: Session,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[CollectionMetadata]:
        """liste paginée des collections

        Args:
            session_session (Session): session sqlite
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
        result = session.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    def get_by_name(
        session: Session, 
        name: str
    ) -> CollectionMetadata | None:
        """Récupérer une collection à partir de son nom

        Args:
            session_session (Session): session sqlite
            name (str): nom de la collection

        Returns:
            CollectionMetadata | None: collection recherchée ou None
        """
        stmt = select(CollectionMetadata).where(
            CollectionMetadata.name == name
        )
        result = session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def create(
        session: Session,
        collection: CollectionMetadata
    ) -> None:
        """Ajout d'une collection

        Args:
            session_session (Session): session sqlite
            collection (CollectionMetadata): collection à ajouter
        """
        session.add(collection)

    @staticmethod
    def get_document_collection_by_md5(
        session: Session,
        collection_id: str,
        md5: str,
    ) -> DocumentMetadata | None:
        stmt = (
            select(DocumentMetadata)
            .where(
                (DocumentMetadata.collection_id == collection_id) &
                (DocumentMetadata.md5 == md5)
            )
        )
        result = session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_document_collection_by_id(
        session: Session,
        document_id: str
    ) -> DocumentMetadata | None:
        stmt = (
            select(DocumentMetadata)
            .where(DocumentMetadata.id == document_id)
        )
        result = session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    def get_collection_documents(
        session: Session,
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
        result = session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    def delete_documents(
        session: Session,
        collection_id: str
    ) -> None:
        """Suppression d'un document d'une collection

        Args:
            session (Session): session sqlite
            collection_id (str): id de la collection
        """
        stmt = delete(DocumentMetadata).where(
            DocumentMetadata.collection_id == collection_id
        )
        session.execute(stmt)

    @staticmethod
    def delete_collection(
        session: Session,
        collection_id: str
    ) -> None:
        """Suppresion d'une collection

        Args:
            session (Session): session sqlite
            collection_id (str): id de la collection
        """
        stmt = delete(CollectionMetadata).where(
            CollectionMetadata.id == collection_id
        )
        session.execute(stmt)

    @staticmethod
    def add_document(
        session: Session,
        document: DocumentMetadata
    ) -> DocumentMetadata:
        session.add(document)
        session.commit()
        session.refresh(document)
        return document
    
    @staticmethod
    def update_document(
        session: Session,
        document: DocumentMetadata
    ) -> DocumentMetadata:
        doc = session.get(DocumentMetadata, document.id)
        if doc:
            session.commit()
            session.refresh(doc)
            return doc
        raise ValueError("Le document est absent de la base de données")

    @staticmethod
    def check_sqlite(session: Session) -> bool:
        try:
            session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False