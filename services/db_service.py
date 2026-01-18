from typing import Iterable, List
import lancedb

from core.config import settings
from schemas import ChunkWithoutVector, Chunks, CollectionInfo, DocumentInfo, CollectionInfoResponse

class DbService:
    """Service pour l'interrogation de la base de données vectorielles"""

    def __init__(self):
        self.db = lancedb.connect(settings.db_dir)

    def list_tables(self) -> Iterable[str]:
        """Liste les tables présentes dans la base de données LanceDB

        Raises:
            Exception: code: 500 - Impossible d'accéder à la base de données

        Returns:
            Iterable[str]: liste des tables présentes dans la base de données
        """
        try:
            tables = self.db.table_names()
            return tables
        except Exception as e:
            raise Exception(e)

    def create_chunk_table(self, collection_name: str) -> bool:
        """Création d'une collection / table

        Args:
            collection_name (str): nom de la collection / table
            chunk (bool): la table doit elle accueillir des chunks par défaut True

        Raises:
            Exception: Erreur lors de la création de la table

        Returns:
            bool: Tables crées avec succès
        """
        try:
            self.db.create_table(
                name=collection_name, 
                schema=Chunks, 
                mode="overwrite"
            )
            return True
        except Exception as e:
            raise Exception(e)
        
    def create_info_tables(self) -> bool:
        """Création des tables de stockage des collections et documents

        Raises:
            Exception: Erreur lors de la création des tables

        Returns:
            bool: Tables crées avec succès
        """
        try:
            self.db.create_table(
                name=settings.db_collections, 
                schema=CollectionInfo, 
                mode="overwrite"
            )
            self.db.create_table(
                name=settings.db_documents, 
                schema=DocumentInfo, 
                mode="overwrite"
            )
            return True
        except Exception as e:
            raise Exception(e)
        
    def delete_table(self, collection_name: str) -> bool:
        """Suppression d'une collection / table

        Args:
            collection_name (str): nom de la table à supprimer

        Raises:
            Exception: Erreur lors de la suppression de la table
        """
        try:
            self.db.drop_table(name=collection_name)
            self.delete_collection_documents(collection_name=collection_name)
            return True
        except Exception as e:
            raise Exception(e)
        
    def insert_data(self, chunks: List[ChunkWithoutVector], collection_name: str):
        """Insertion de données dans la base de données

        Args:
            chunks (List[Chunks]): liste des chunks à insérer dans la table
            collection_name (str): nom de la collection / table à utiliser pour l'insertion des données

        Raises:
            Exception: Erreur lors de l'écriture des données
        """
        try:
            table = self.db.open_table(name=collection_name)
            table.add(chunks)
        except Exception as e:
            raise Exception(e)
        
    def insert_collection(self, collection: CollectionInfo):
        try:
            table = self.db.open_table(settings.db_collections)
            col = table.search().where(f"name = '{collection.name}'").limit(1).to_pydantic(model=CollectionInfo)
            if len(col) >= 1:
                raise Exception("La collection est déjà présente dans la base")    
            table.add([collection])
        except Exception as e:
            raise Exception(e)
        
    def insert_documents(self, collection_name: str, document: DocumentInfo):
        try:
            # Vérification que la collection existe
            collection_table = self.db.open_table(settings.db_collections)
            collection = collection_table.search().where(f"name = '{collection_name}'").limit(1).to_pydantic(model=CollectionInfo)
            if len(collection) < 1:
                raise Exception("Aucune collection trouvée")
            elif len(collection) > 1:
                raise Exception("Plusieurs collections trouvées")
            # Test si le document est déjà présent
            document_table = self.db.open_table(settings.db_documents)
            doc = document_table.search().where(f"collection_name = '{collection_name}' and filename='{document.filename}'").limit(1).to_pydantic(model=DocumentInfo)
            if len(doc) >= 1:
                raise Exception("Le document est déjà indexé")    
            # Insertion du nouveau document dans la liste des docuemnts liés à la collection
            document_table.add([document])
        except Exception as e:
            raise Exception(e)
        
    def get_collection_info(self, collection_name: str) -> CollectionInfoResponse:
        """Information sur la collection / table

        Args:
            collection_name (str): nom de la collection / table à inspecter

        Raises:
            Exception: Erreur lors de la lecture des informations de la collection

        Returns:
            CollectionInfo: nombre de documents présents dans la collection / table
        """
        try:
            table_collection = self.db.open_table(settings.db_collections)
            collection = table_collection.search().where(where=f"name='{collection_name}'").limit(1).to_pydantic(model=CollectionInfo)[0]
            table_documents = self.db.open_table(settings.db_documents)
            documents = table_documents.search().where(where=f"collection_name = '{collection_name}'").to_pydantic(model=DocumentInfo)
            return CollectionInfoResponse(
                name=collection.name,
                description=collection.description,
                user=collection.user,
                created_date=collection.created_date,
                documents=documents
            )
        except Exception as e:
            raise Exception(e)
        
    def delete_collection_documents(self, collection_name: str):
        """Suppression des documents liés à une collection

        Args:
            collection_name (str): nom de la collection

        Raises:
            Exception: Erreur lors de la suppression des documents
        """
        try:
            table_collection = self.db.open_table(name=settings.db_collections)
            table_collection.delete(where=f"name = '{collection_name}'")
            table_document = self.db.open_table(name=settings.db_documents)
            table_document.delete(where=f"collection_name = '{collection_name}'")
        except Exception as e:
            raise Exception(e)

    def delete_documents(self, filename: str, collection_name: str):
        """Suppression d'un document d'une collection

        Args:
            filename (str): nom du fichier à supprimer
            collection_name (str): nom de la collection auquel est liée le fichier

        Raises:
            Exception: Erreur lors de la suppression du document
        """
        try:
            table = self.db.open_table(name=settings.db_documents)
            table.delete(f"collection = '{collection_name}' AND filename='{filename}")
        except Exception as e:
            raise Exception(e)

    def query_db(self, query: str, collection_name: str, limit: int = 5) -> List[Chunks]:
        """_summary_

        Args:
            query (str): requête à appliquer pour la recherche dans la base de données vectorielles
            collection_name (str): nom de la collection / table dans laquelle faire la recherche

        Raises:
            Exception: 500 - Erreur lors de l'éxecution de la recherche

        Returns:
            List[Chunks]: Liste des chunks retournées par la requête
        """
        try:
            table = self.db.open_table(collection_name)
            return table.search(query=query).limit(limit).to_pydantic(Chunks)
        
        except Exception as e:
            raise Exception(e)