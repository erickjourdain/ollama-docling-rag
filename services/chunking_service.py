import time
from typing import List, Set

from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.base import BaseChunk
from docling_core.types.doc.document import DoclingDocument
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.serializer.markdown import MarkdownTableSerializer
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from transformers import AutoTokenizer

from schemas import ChunkMetada, ChunkWithoutVector, ChunkingResponse

class MDTableSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),  # configuring a different table serializer
        )

class ChunkingService:
    """Service pour la gestion des chunks"""

    def __init__(self, filename: str) -> None:
        self.filename = filename
    
    def __docling_chunk_to_db_chunk(self, chunk: BaseChunk) -> ChunkWithoutVector:
        """Transforme un chunk Docling en payload compatible LanceDB
        (texte + metadonnées enrichies)

        Args:
            chunk (BaseChunk): le chunk Docling à traiter

        Raises:
            Exception: 500 - errreur lors de l'éxécution de la fonction

        Returns:
            dict: le dictionnaire avec le texte et les metadonnées
        """

        try:
            # Extraction du texte
            text = chunk.text.strip()
            
            # Noeud avec les métadonnées du chunk
            node = getattr(chunk, "meta")
            # Récupère la hiérarchie des titres
            sections: Set[str] = set()
            if node.headings:
                for head in node.headings:
                    section = head.text if hasattr(head, "text") else head
                    sections.add(section)
            full_section_path = ">".join(sections)

            # Récupère les numéros de page
            pages: Set[int] = set()
            for prov in node.doc_items:
                if hasattr(prov, 'prov') and prov.prov:
                    for p in prov.prov:
                        pages.add(p.page_no)

            return ChunkWithoutVector(
                text=text,
                metadata=ChunkMetada(
                    filename=self.filename,
                    page_numbers=sorted(pages),
                    context= full_section_path
                )
            )

        except Exception as e:
            raise Exception(e)
        

    def basic_chunking(self, document: DoclingDocument) -> ChunkingResponse:
        """Chunking du document Docling

        Args:
            document (DoclingDocument): le document à chunker
 
        Raises:
            Exception: 500 - errreur lors de l'éxécution de la fonction

        Returns:
            ChunkingResponse: durée de l'éxécution de la fonction
        """

        try:
            start_time = time.time()
            EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
            MAX_TOKENS = 512  # set to a small number for illustrative purposes

            tokenizer = HuggingFaceTokenizer(
                tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
                max_tokens=MAX_TOKENS,  # optional, by default derived from `tokenizer` for HF case
            )
            
            chunker = HybridChunker(
                tokenizer=tokenizer,
                serializer_provider=MDTableSerializerProvider(),
                merge_peers=True,  # optional, defaults to True
                always_emit_headings=True,
            )
            chunk_iter = chunker.chunk(dl_doc=document)
            chunks = list(chunk_iter)

            # Création des chunks pour insertin dans la base LanceDB
            chunks_for_db: List[ChunkWithoutVector] = []

            for chunk in chunks:
                if len(chunk.text.strip()):
                    payload = self.__docling_chunk_to_db_chunk(chunk=chunk)

                    # 🔥 OPTION RECOMMANDÉE : enrichir le texte pour l'embedding
                    if payload.metadata.context:
                        payload.text = (
                            f"[SECTION] {payload.metadata.context}\n\n"
                            + payload.text
                        )

                    chunks_for_db.append(payload)

            # Calcul du temps écoulé
            elapsed_time = time.time() - start_time

            return ChunkingResponse(
                chunks=chunks_for_db,
                embedding_time=elapsed_time
            )

        except Exception as e:
            raise Exception(e)
        