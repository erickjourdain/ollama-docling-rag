import os
from typing import List

from chromadb import Metadata
from dotenv import load_dotenv
from ollama import Client, GenerateResponse

from schemas import Model
from core.config import settings
from schemas.health import OllamaHealth

load_dotenv()

class LlmService:
    """_summary_Service pour l'interrogation du LLM"""

    def __init__(self):
        self.llm_client = Client(os.environ.get("OLLAMA_BASE_URL"))

    def vectordb_query(self, query: str, model: str = settings.llm_model) -> str:
        """Restructuration de la requête pour interrogation de la base de données vectorielle

        Args:
            query (str): la requête à reformuler
            model (Optional(str)): le modèle à utiliser par défaut celui présent dans le fichier config

        Returns:
            str: la requête à appliquer pour effectuer la recherche vectorielle
        """
        try:
            reponse = self.llm_client.generate(
                model=model,
                prompt=f"""
                Tu es un assistant spécialisé en recherche sémantique sur base de données vectorielle.

                Objectif :
                Reformuler la requête utilisateur afin de maximiser la pertinence des résultats retournés par une recherche vectorielle.

                Instructions :
                - Retourne la réponse en langue française
                - Reformule la requête de manière claire, concise et factuelle
                - Supprime les éléments conversationnels ou subjectifs
                - Conserve uniquement l’intention informationnelle
                - Ajoute des synonymes ou termes proches si cela améliore la couverture sémantique
                - Ne pose pas de questions
                - Ne donne aucune explication
                - Ne réponds pas à la requête, reformule-la uniquement

                Requête utilisateur :
                "{query}"
                """,
                think=False,
                options={"temperature": 0}
            )

            return reponse.response
        
        except Exception as e:
            raise Exception(e)
        
    def __define_context(self, docs: List[str], metadatas: List[Metadata]) -> str:
        """ Définition du contexte à partir des chunks fournis par la base vectorielle

        Args:
            docs (List[str]): la liste des chunks à insérer dans le contexte
            metadatas (List[Metadata]): liste des metadatas liés au chunks

        Returns:
            str: la chaine de caractère constituant le contexte à fournir au LLM
        """
        try:
            context_blocks = []

            if len(docs):
                for idx, doc in enumerate(docs, start=1):
                    filename = metadatas[idx].get('filename') or "source inconnue"
                    section = metadatas[idx].get('section') or "section non precisée"
                    pages = metadatas[idx].get('pages') or "non spécifiées"

                    block = f"""Source {idx}
                    Fichier : {filename}
                    Section : {section}
                    Pages: {pages}
                    Contenu :
                    {doc.strip()}
                    """
                    context_blocks.append(block)
                    full_context = "\n\n".join(context_blocks)
                    return full_context
            
            return str()
        
        except Exception as e:
            raise Exception(e)
        
    def create_answer(
            self, 
            docs: List[str], 
            metadatas: List[Metadata],
            query: str, 
            model: str = settings.llm_model
        ) -> GenerateResponse:
        """Construction de la réponse à la demande à partir des données fournies par la base vectorielle

        Args:
            chunks (List[Chunks]): la liste des chunks à insérer dans le contexte
            query (str): la requête de l'utilisateur
            model (Optional(str)): le modèle à utiliser par défaut celui présent dans le fichier config

        Raises:
            Exception: Erreur lors de l'éxecution de la fonction

        Returns:
            GenerateResponse: la réponse fournie par le LLM
        """

        try:
            context = self.__define_context(docs=docs, metadatas=metadatas)
            return self.llm_client.generate(
                model=model,
                prompt=f"""
                Tu es un moteur de réponse factuelle dans un système RAG.

                CONTRAINTES ABSOLUES :
                - Toute phrase de la réponse DOIT être justifiée par au moins une source du contexte
                - Si une information ne peut pas être justifiée, elle DOIT être omise
                - Il est interdit d’inférer, de déduire ou de compléter une information absente
                - Les sources doivent correspondre exactement aux métadonnées fournies
                - Si aucune source n’est applicable, retourne :
                {{
                    "answer": "Aucune donnée trouvée permettant de répondre à la question posée",
                    "sources": []
                }}

                FORMAT DE SORTIE STRICT (JSON UNIQUEMENT) :
                {{
                    "answer": "...",
                    "sources": [
                        {{
                            "filename": "...",
                            "section": "...",
                            "pages": [...]
                        }}
                    ]
                }}

                CONTEXTE DOCUMENTAIRE :
                {context}

                QUESTION :
                {query}

                RÉPONSE JSON :
                """,
                think=False,
                options={"temperature": 0}
            )
        
        except Exception as e:
            raise Exception(e)
        
    def rerank_chunks_llm(self, query: str, chunks: list[str]) -> list[int]:
        """ Reranking des réponses (chunks) en fonction de leur pertinence

        Args:
            query (str): la requête initiale de l'utilisateur
            chunks (list[str]): liste de chuncks à réordonner

        Raises:
            Exception: Erreur lors de l'éxecution de la fonction

        Returns:
            list[int]: la liste des chuncks réordonnées
        """
        
        try: 
            chunks_text = "\n\n".join(
                f"[{i}] {doc}"
                for i, doc in enumerate(chunks)
            )

            prompt = f"""
            Tu es un moteur de reranking pour un système RAG.

            Question utilisateur :
            {query}

            Voici des extraits de documents numérotés.
            Classe-les par ordre de pertinence pour répondre à la question.
            Réponds uniquement par une liste d’indices séparés par des virgules.

            Extraits :
            {chunks_text}

            Classement :
            """.strip()

            response = self.llm_client.generate(
                model=settings.llm_model,
                prompt=prompt,
                options={"temperature": 0}
            )

            return [
                int(i.strip())
                for i in response["response"].split(",")
                if i.strip().isdigit()
            ]
        
        except Exception as e:
            raise Exception(e)
        
    def list_models(self) -> list[Model]:
        """Récupération des modèles disponibles

        Raises:
            Exception: Erreur lors de la récupération des modèles Ollama

        Returns:
            ListResponse: Liste des modèles disponibles
        """
        try:
            liste = self.llm_client.list()
            models: List[Model] = []
            for model in liste.models:
                nom = model.model
                if model.model is not None:
                    embed = True if "embed" in model.model else False
                else:
                    embed = False
                models.append(Model(
                    nom=nom,
                    embed=embed
                ))
            return models
        
        except Exception as e:
            raise Exception(e)
        
    def check_ollama(self) -> OllamaHealth:
        try:
            models = self.list_models()
            return OllamaHealth(
                ok= True,
                models=models
            )
        except Exception as e:
            return OllamaHealth(
                ok=False,
                error=str(e)
            )