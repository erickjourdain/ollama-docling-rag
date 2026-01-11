import os
from typing import List

from dotenv import load_dotenv
from ollama import Client, GenerateResponse

from schemas import Chunks, Model
from core.config import settings

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
        
    def __define_context(self, chunks: List[Chunks]) -> str:
        """ Définition du contexte à partir des chunks fournis par la base vectorielle

        Args:
            chunks (List[Chunks]): la liste des chunks à insérer dans le contexte

        Returns:
            str: la chaine de caractère constituant le contexte à fournir au LLM
        """
        try:
            context_blocks = []

            if len(chunks):
                for idx, chunk in enumerate(chunks, start=1):
                    filename = chunk.metadata.filename or "source inconnue"
                    section = chunk.metadata.context or "section non precisée"
                    pages = chunk.metadata.page_numbers or []

                    pages_str = ", ".join(str(p) for p in pages) if pages else "non spécifiées"

                    block = f"""Source {idx}
                    Fichier : {filename}
                    Section : {section}
                    Pages: {pages_str}
                    Contenu :
                    {chunk.text.strip()}
                    """
                    context_blocks.append(block)
                    full_context = "\n\n".join(context_blocks)
                    return full_context
            
            return str()
        
        except Exception as e:
            raise Exception(e)
        
    def create_answer(self, chunks: List[Chunks], query: str, model: str = settings.llm_model) -> GenerateResponse:
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
            context = self.__define_context(chunks=chunks)
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
        
    def rerank_chunks_llm(self, query: str, chunks: list[Chunks], limit: int = 5) -> list[Chunks]:
        """ Reranking des réponses (chunks) en fonction de leur pertinence

        Args:
            query (str): la requête initiale de l'utilisateur
            chunks (list[Chunks]): liste de chuncks à réordonner
            limit (Optional(int)): le nombre max de chuncks à retourner (5 par défaut)
            model (Optional(str)): le modèle à utiliser par défaut celui présent dans le fichier config

        Raises:
            Exception: Erreur lors de l'éxecution de la fonction

        Returns:
            list[Chunks]: la liste des chuncks réordonnées
        """
        
        try: 
            chunks_text = "\n\n".join(
                f"[{i}] {chunk.text}"
                for i, chunk in enumerate(chunks)
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
            """

            response = self.llm_client.generate(
                model=settings.llm_model,
                prompt=prompt,
                options={"temperature": 0}
            )

            ranked_indices = [
                int(i.strip())
                for i in response["response"].split(",")
                if i.strip().isdigit()
            ]

            return [chunks[i] for i in ranked_indices[:limit]]
        
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