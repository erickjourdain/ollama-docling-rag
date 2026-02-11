from pathlib import Path
import shutil
import uuid
from typing import Sequence
from sqlalchemy.orm import Session

from core.config import settings
from services import DbVectorielleService
from repositories.collections_repository import CollectionRepository
from db.models import CollectionMetadata, DocumentMetadata

class CollectionService:

    @staticmethod
    def list_collections(
        session: Session,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[CollectionMetadata]:
        """Liste des collections paginée

        Args:
            session (AsyncSession): session sqlite
            limit (int, optional): nombre de collections max à retourner. Defaults to 50.
            offset (int, optional): offset. Defaults to 0.

        Returns:
            Sequence[CollectionMetadata]: liste de collections
        """
        return CollectionRepository.list_collections(
            session=session,
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    def get_by_name(
        session: Session,
        name: str
    ) -> CollectionMetadata | None:
        """_summary_

        Args:
            session (AsyncSession): session sqlite
            name (str): nom de la collection à récupérer

        Returns:
            CollectionMetadata | None: collection recherchée ou None
        """
        return CollectionRepository.get_by_name(
            session=session,
            name=name
        )
    
    @staticmethod
    def create_collection(
        session: Session,
        vector_session: DbVectorielleService,
        name: str,
        description: str | None,
        user_id: str
    ) -> CollectionMetadata:
        """Création d'une collection dans la base de données sqlite et chromasession

        Args:
            session (AsyncSession): session sqlite
            name (str): nom de la collection
            description (str | None): description de la collection
            user_id (str): id de l'utilisateur

        Raises:
            ValueError: erreur lors de la création

        Returns:
            CollectionMetadata: collection insérée
        """
        # Vérifier existence
        existing = CollectionRepository.get_by_name(session, name)
        if existing:
            raise ValueError("La collection existe déjà dans la base")

        # Créer l’objet session
        collection = CollectionMetadata(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_by=user_id
        )

        try:
            # session first
            CollectionRepository.create(session, collection)
            session.flush()  # force INSERT sans commit

            # Side-effect : Chroma
            vector_session.create_collection(collection_name=name)

            # Commit final
            session.commit()

        except Exception as e:
            session.rollback()
            raise Exception(e)

        return collection
    
    @staticmethod
    def documents_collection(
        session: Session,
        collection_name: str,
        limit: int = 50,
        offset: int = 0
    ) -> Sequence[DocumentMetadata]:
        # Vérifier existence collection
        collection = CollectionRepository.get_by_name(session=session, name=collection_name)
        if not collection:
            raise ValueError("Collection not found")
        # Récupérer la liste des documents de la collection
        return CollectionRepository.get_collection_documents(
            session=session, 
            collecion_id=str(collection.id),
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    def delete_collection(
        session: Session,
        vector_session: DbVectorielleService,
        name: str,
    ):
        """Suppression d'une collection

        Args:
            session (AsyncSession): session sqlite
            name (str): nom de la collection

        Raises:
            ValueError: erreur levée lors de la suppression
        """
        # Vérifier existence
        collection = CollectionRepository.get_by_name(session, name)
        if not collection:
            raise ValueError("Collection not found")

        try:
            # Supprimer côté Chroma
            vector_session.delete_collection(collection_name=name)

            # Supprimer les documents session
            CollectionRepository.delete_documents(
                session=session,
                collection_id=str(collection.id)
            )

            # Supprimer la collection session
            CollectionRepository.delete_collection(
                session=session,
                collection_id=str(collection.id)
            )

            # Suppression des fichiers sur le disque
            md_dir = Path(settings.static_dir) / collection.name
            shutil.rmtree(md_dir, ignore_errors=False)

            # Commit final
            session.commit()

        except Exception as e:
            session.rollback()
            raise Exception(e)

    @staticmethod
    def check_db(session: Session) -> bool:
        try:
            return CollectionRepository.check_sqlite(session=session)
        except Exception:
            return False