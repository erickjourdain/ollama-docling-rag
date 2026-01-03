
import os
from typing import List

import lancedb
from fastapi import HTTPException
from ollama import Client, GenerateResponse
from dotenv import load_dotenv

from config import settings
from models import Chunks

load_dotenv()

class QueryService:
    """Service pour l'interrogation de la base de données vectorielles"""

    def __init__(self, limit: int = 5):
        self.db = lancedb.connect(settings.lancedb_dir)
        self.limit = limit
        self.ollama_client = Client(host=os.environ.get("OLLAMA_BASE_URL"))

    def query_db(self, query: str, collection_name: str) -> List[Chunks]:
        try:
            reponse = self.ollama_client.generate(
                model=settings.ollama_model,
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
                think=False
            )
            table = self.db.open_table(collection_name)
            return table.search(query=reponse.response).limit(self.limit).to_pydantic(Chunks)
        
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF (chunking): {str(e)}")

    def rerank_chunks_llm(self, query: str, chunks: list[Chunks]) -> list[Chunks]:
        
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

        response = self.ollama_client.generate(
            model=settings.ollama_model,
            prompt=prompt,
            options={"temperature": 0}
        )

        ranked_indices = [
            int(i.strip())
            for i in response["response"].split(",")
            if i.strip().isdigit()
        ]

        return [chunks[i] for i in ranked_indices[:self.limit]]

    def define_context(self, chunks: List[Chunks]) -> str:
        try:
            context_blocks = []

            for idx, chunk in enumerate(chunks, start=1):
                filename = chunk.metadata.filename or "source inconnue"
                context = chunk.metadata.context or ""
                text = chunk.text.strip()

                block = f"""Source {idx}
                Fichier : {filename}
                SECTION : {context}
                Contenu :
                {text}
                """
                context_blocks.append(block)

            full_context = "CONTEXTE DOCUMENTAIRE\n\n" + "\n".join(context_blocks)
            return full_context

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF (chunking): {str(e)}")

    def create_answer(self, context: str, query: str) -> GenerateResponse:
        try:
            return self.ollama_client.generate(
                model=settings.ollama_model,
                prompt=f"""
                Tu es un assistant IA dans un système RAG.

                RÈGLES STRICTES :
                - Utilise EXCLUSIVEMENT les informations du CONTEXTE DOCUMENTAIRE
                - Si la réponse n’est pas trouvable dans le contexte, réponds :
                {{
                    "answer": "Je ne dispose pas d’informations suffisantes dans les documents fournis.",
                    "sources": []
                }}
                - N’invente rien
                - Ne fais aucune supposition
                - Cite uniquement les sources réellement utilisées
                - Réponds uniquement en JSON VALIDE
                - Aucune phrase hors JSON

                FORMAT DE SORTIE :
                {{
                "answer": "texte de la réponse",
                "sources": ["nom_fichier_1", "nom_fichier_2"]
                }}

                {context}

                QUESTION :
                {query}

                RÉPONSE JSON :
                """,
                think=False,
                options={"temperature": 0}
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF (chunking): {str(e)}")
