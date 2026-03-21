"""
src/rag_pipeline.py
Orchestrates the full RAG pipeline: load -> chunk -> embed -> retrieve -> generate
"""

import os
import logging
from typing import Dict, Optional

from src.loader import load_documents_from_dir, load_document
from src.chunker import chunk_all_documents, chunk_document
from src.vectorstore import VectorStore
from src.generator import AnswerGenerator

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self, docs_dir: str = "./documents", chroma_dir: str = "./chroma_db", top_k: int = 5):
        self.docs_dir = docs_dir
        self.top_k = top_k
        logger.info("Initializing RAG Pipeline...")
        self.vector_store = VectorStore(persist_dir=chroma_dir)
        self.generator = AnswerGenerator()
        self._ingest()

    def _ingest(self):
        if not os.path.isdir(self.docs_dir):
            logger.warning("Documents directory not found: %s", self.docs_dir)
            return
        docs = load_documents_from_dir(self.docs_dir)
        if not docs:
            logger.warning("No documents found in: %s", self.docs_dir)
            return
        added = self.vector_store.index_chunks(chunk_all_documents(docs))
        logger.info("Ingestion complete. %d new chunks indexed.", added)

    def ingest_file(self, filepath: str) -> Dict:
        doc = load_document(filepath)
        if not doc:
            return {"status": "error", "message": f"Could not load: {filepath}"}
        added = self.vector_store.index_chunks(chunk_document(doc))
        return {"status": "success", "filename": doc["filename"], "chunks_added": added, "doc_type": doc["doc_type"], "year": doc["year"]}

    def query(self, question: str, search_mode: str = "hybrid", doc_type_filter: Optional[str] = None, year_filter: Optional[str] = None, top_k: Optional[int] = None) -> Dict:
        k = top_k or self.top_k
        if not question.strip():
            return {"error": "Empty question."}

        if search_mode == "keyword":
            chunks = self.vector_store.keyword_search(question, k, doc_type_filter, year_filter)
        elif search_mode == "semantic":
            chunks = self.vector_store.semantic_search(question, k, doc_type_filter, year_filter)
        else:
            chunks = self.vector_store.hybrid_search(question, k, doc_type_filter, year_filter)

        result = self.generator.generate(question, chunks)

        return {
            "question": question,
            "answer": result["answer"],
            "citations": result["citations"],
            "retrieved_chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "filename": c["filename"],
                    "doc_type": c["doc_type"],
                    "year": c["year"],
                    "snippet": c["text"][:300] + ("..." if len(c["text"]) > 300 else ""),
                    "score": c.get("score"),
                    "search_type": c.get("search_type"),
                }
                for c in chunks
            ],
            "search_mode": search_mode,
            "model_used": result["model"],
            "filters_applied": {"doc_type": doc_type_filter or "all", "year": year_filter or "all"},
        }

    def get_stats(self) -> Dict:
        return {"vector_store": self.vector_store.get_stats(), "docs_dir": self.docs_dir, "generator_model": self.generator.model_name}

    def reindex(self) -> Dict:
        self.vector_store.clear()
        self._ingest()
        return {"status": "reindexed", "total_chunks": self.vector_store.get_stats()["total_chunks"]}
