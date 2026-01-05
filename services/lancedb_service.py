from typing import Iterable, List

import lancedb
from fastapi import HTTPException
from dotenv import load_dotenv

from config import settings
from models import ChunkWithoutVector, Chunks

load_dotenv()

class LanceDBService:
    """Service pour l'interrogation de la base de données vectorielles"""

    def __init__(self):
        self.db = lancedb.connect(settings.lancedb_dir)

    def list_tables(self) -> Iterable[str]:
        """Liste les tables présentes dans la base de données LanceDB

        Raises:
            HTTPException: code: 500 - Impossible d'accéder à la base de données

        Returns:
            Iterable[str]: liste des tables présentes dans la base de données
        """
        try:
            tables = self.db.table_names()
            return tables
        except Exception:
            raise HTTPException(status_code=500, detail="Erreur lors de la connection à la base de données")

    def create_table(self, collection_name: str):
        """Création d'une collection / table

        Args:
            collection_name (str): nom de la collection / table

        Raises:
            HTTPException: Erreur lors de la création de la table
        """
        try:
            self.db.create_table(
                name=collection_name, 
                schema=Chunks, 
                mode="overwrite"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impossible de créer la collection: {str(e)}")

    def delete_table(self, collection_name: str):
        """Suppression d'une collection / table

        Args:
            collection_name (str): nom de la table à supprimer

        Raises:
            HTTPException: Erreur lors de la suppression de la table
        """
        try:
            self.db.drop_table(collection_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impossible de supprimer la collection: {str(e)}")

    def insert_data(self, chunks: List[ChunkWithoutVector], collection_name: str):
        """Insertion de données dans la base de données

        Args:
            chunks (List[Chunks]): liste des chunks à insérer dans la table
            collection_name (str): nom de la collection / table à utiliser pour l'insertion des données

        Raises:
            HTTPException: Erreur lors de l'écriture des données
        """
        try:
            table = self.db.open_table(name=collection_name)
            table.add(chunks)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Impossible d'écrire les données dans la base de données: {str(e)}")

    def query_db(self, query: str, collection_name: str, limit: int = 5) -> List[Chunks]:
        """_summary_

        Args:
            query (str): requête à appliquer pour la recherche dans la base de données vectorielles
            collection_name (str): nom de la collection / table dans laquelle faire la recherche

        Raises:
            HTTPException: 500 - Erreur lors de l'éxecution de la recherche

        Returns:
            List[Chunks]: Liste des chunks retournées par la requête
        """
        try:
            table = self.db.open_table(collection_name)
            return table.search(query=query).limit(limit).to_pydantic(Chunks)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche vectorielle: {str(e)}")
