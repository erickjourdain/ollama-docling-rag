from sqlalchemy.orm import Session
from sqlalchemy import delete, func, select, text, true

from db.models import CollectionMetadata, DocumentMetadata, User
from schemas import (
    CollectionFilters, 
    CollectionModel, 
    CollectionListResponse, 
    DocumentModel,
    DocumentFilters, 
    DocumentListResponse
)


class CollectionRepository:
    
    @staticmethod
    def list_collections(
        session: Session,
        filters: CollectionFilters
    ) -> CollectionListResponse:
        """liste paginée des collections

        Args:
            session_session (Session): session sqlite
            filters (CollectionFilters): filtres pour la récupération des collections (limit, offset, user, name)

        Returns:
            CollectionListResponse: liste de collections et leur nombre total
        """
        # Filtrage par utilisateur
        user_ids: list[str] = []
        if filters.user:
            stmt_users = (
                select(User.id)
                .where(User.username.ilike(f"%{filters.user}%"))
            )
            result_users = session.execute(stmt_users)
            user_ids = [user_id for (user_id,) in result_users.fetchall()]
            if len(user_ids) == 0:
                return CollectionListResponse(collections=[], count=0)
        # Création de la requête de base
        stmt = (
            select(CollectionMetadata)
            .order_by(CollectionMetadata.date_creation.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        stmt_count = select(func.count(CollectionMetadata.id))
        # Filtarge par utilisateur
        if filters.user:
            stmt = stmt.where(CollectionMetadata.created_by.in_(user_ids))
            stmt_count = stmt_count.where(CollectionMetadata.created_by.in_(user_ids))
        # Filtarge par nom de collection
        if filters.name:
            stmt = stmt.where(CollectionMetadata.name.ilike(f"%{filters.name}%"))
            stmt_count = stmt_count.where(CollectionMetadata.name.ilike(f"%{filters.name}%"))
        # Exécution des requêtes
        result = session.execute(stmt)
        result_count = session.execute(stmt_count).scalar_one()
        return CollectionListResponse(
            collections=[CollectionModel.model_validate(c) for c in result.scalars().all()],
            count=result_count
        )
    
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
    def count_documents_collection(
        session: Session,
        collection_id: str
    ) -> int:
        """Nombre de documents indexés dans une collection

        Args:
            session (Session): session d'accès à la base de données
            collection_id (str): id de la collection

        Returns:
            int: nombre de documents indexés dans la collection
        """
        stmt = (
            select(func.count(DocumentMetadata.id))
            .where(
                (DocumentMetadata.collection_id == collection_id) & 
                (DocumentMetadata.is_indexed == true())
            )
        )
        result = session.execute(stmt)
        return result.scalar_one()
    
    @staticmethod
    def get_collection_documents(
        session: Session,
        filters: DocumentFilters
    ) -> DocumentListResponse:
        """Liste des documents présents dans une collection

        Args:
            session (Session): sessions d'accès à la base de données
            filters (DocumentFilters): filtres pour la récupération des documents (collection_name, limit, offset)

        Raises:
            ValueError: si la collection n'existe pas

        Returns:
            DocumentListResponse: liste des documents de la collection et leur nombre total
        """
        collection = CollectionRepository.get_by_name(session=session, name=filters.collection_name)
        if not collection:
            raise ValueError("Collection introuvable")
        stmt = (
            select(DocumentMetadata)
            .where(
                (DocumentMetadata.collection_id == collection.id) & 
                (DocumentMetadata.is_indexed == true())
            )
            .limit(limit=filters.limit)
            .offset(offset=filters.offset)
        )
        stmt_count = (
            select(func.count(DocumentMetadata.id))
            .where(
                (DocumentMetadata.collection_id == collection.id) & 
                (DocumentMetadata.is_indexed == true())
            )
        )
        result = session.execute(stmt)
        result_count = session.execute(stmt_count).scalar_one()
        return DocumentListResponse(
            documents=[DocumentModel.model_validate(d) for d in result.scalars().all()],
            count=result_count
        )

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