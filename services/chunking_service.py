import time
from fastapi import HTTPException

from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc.document import DoclingDocument
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.serializer.markdown import MarkdownTableSerializer
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)

import lancedb
from transformers import AutoTokenizer

from config import settings
from models import Chunks, ChunkingResponse

class MDTableSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc):
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),  # configuring a different table serializer
        )

class ChunkingService:
    """Service pour la gestion des chunks"""

    def __init__(self):
        pass

    def basic_chunking(self, document: DoclingDocument, collection_name: str, file_name: str) -> ChunkingResponse:
        """Chunking du document docling"""

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

            db = lancedb.connect(settings.lancedb_dir)

            table = db.create_table(
                name=collection_name, 
                schema=Chunks, 
                mode="overwrite"
            )

            # Create table with processed chunks
            processed_chunks = [
                {
                    "text": chunk.text,
                    "metadata": {
                        "filename": file_name,
                        "page_numbers": [0],
                        "context": chunker.contextualize(chunk=chunk),
                    },
                }
                for chunk in chunks
            ]

            table.add(processed_chunks)

            # Calcul du temps écoulé
            elapsed_time = time.time() - start_time

            return ChunkingResponse(
                embedding_time=elapsed_time
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors du traitement du PDF (chunking): {str(e)}")
