from typing import Iterable, List
import lancedb
from dotenv import load_dotenv

from core.config import settings
from schemas import ChunkWithoutVector, Chunks, Document

load_dotenv()

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

    def create_table(self, collection_name: str, doc: bool = False) -> bool:
        """Création d'une collection / table

        Args:
            collection_name (str): nom de la collection / table
            chunk (bool): la table doit elle accueillir des chunks par défaut True

        Raises:
            Exception: Erreur lors de la création de la table
        """
        try:
            if not doc:
                self.db.create_table(
                    name=collection_name, 
                    schema=Chunks, 
                    mode="overwrite"
                )
                return True
            else:
                self.db.create_table(
                    name=settings.db_documents,
                    schema=Document,
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
        
    def insert_document(self, document: Document):
        """Insertion des informations relatives à un document dans la base de données

        Args:
            document (Document): information sur le document

        Raises:
            Exception: Erreur lors de la sauvegarde du document dans la base de données
        """
        try:
            table = self.db.open_table(settings.db_documents)
            table.add([document])
        except Exception as e:
            raise Exception(e)
        
    def get_nb_documents(self, collection_name: str) -> int:
        """Nombre de documents enregistrés pour une collection / table

        Args:
            collection_name (str): nom de la collection / table à inspecter

        Raises:
            Exception: Erreur lors de la lecture du nombre de documents

        Returns:
            int: nombre de documents présents dans la collection / table
        """
        try:
            table = self.db.open_table(settings.db_documents)
            return table.count_rows(filter=f"collection = '{collection_name}'")
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
            table = self.db.open_table(name=settings.db_documents)
            table.delete(f"collection = '{collection_name}'")
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