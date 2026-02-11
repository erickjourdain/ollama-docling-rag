from typing import List, Sequence
import uuid
import chromadb
from chromadb import Collection, QueryResult
from chromadb.utils.embedding_functions import OllamaEmbeddingFunction
from chromadb.api.types import EmbeddingFunction

from schemas import Chunk

class DbVectorielleService:
    """Service pour la gestion de la base de données vectorielles"""

    def __init__(self, chroma_db_dir: str, embedding_model: str, ollama_url: str):
        self.client = chromadb.PersistentClient(path=chroma_db_dir)
        self.embedding_function: EmbeddingFunction = OllamaEmbeddingFunction(
            model_name=embedding_model,
            url=ollama_url
        )

    def create_collection(self, collection_name: str) -> bool:
        """Création d'une collection

        Args:
            collection_name (str): nom de la collection

        Raises:
            Exception: Erreur lors de la création de la collection

        Returns:
            bool: Collection créée avec succès
        """
        try:
            self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            return True
        except Exception as e:
            raise Exception(e)
        
    def delete_collection(self, collection_name: str) -> bool:
        """Suppression d'une collection

        Args:
            collection_name (str): nom de la collection

        Raises:
            Exception: Erreur lors de la suppression de la collection

        Returns:
            bool: Collection supprimée avec succès
        """
        try:
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            raise Exception(e)
        
    def query_collection(self, query: str, collection_name: str) -> QueryResult:
        """Interrogation d'une collection de la base de données

        Args:
            query (str): requête d'ionterrogation
            collection_name (str): nom de la collection à interroger

        Returns:
            QueryResult: résultat de la recherche
        """
        try:
            collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=self.embedding_function
            )
            return collection.query(
                query_texts=[query],
                include=["documents", "metadatas"], 
                n_results=5
            )
        except Exception as e:
            raise Exception(e)
        
    def list_collections(self) -> Sequence[Collection]:
        """Obtenir la liste des collections présentes dans la base de données vectorielles

        Raises:
            Exception: erreur lors de la lecture de la base

        Returns:
            Sequence[Collection]: liste des collections
        """
        try:
            return self.client.list_collections()
        except Exception as e:
            raise Exception(e)
        
    def check_db(self):
        try:
            self.client.list_collections()
            return True
        except Exception:
            return False
                    
    def insert_chunk(self, collection_name: str, chunks: List[Chunk]):
        try:
            collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=self.embedding_function
            )
            ids = []
            documents = []
            metadatas = []
            for chunk in chunks:
                ids.append(str(uuid.uuid4()))
                documents.append(chunk.text)
                metadatas.append(chunk.metadata.model_dump())

            collection.add(
                ids=ids,
                metadatas=metadatas,
                documents=documents
            )
        except Exception as e:
            raise Exception(e)
        