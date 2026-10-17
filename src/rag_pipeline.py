"""
src/rag_pipeline.py
Green-Optimized RAG Pipeline with Two-Tier Caching, Lean Context Processing,
and GSF-Compliant Software Carbon Intensity (SCI) Tracking.
"""

import os
import time
import logging
import hashlib
import json
from collections import OrderedDict
from typing import Dict, Optional

from src.loader import load_documents_from_dir, load_document
from src.chunker import chunk_all_documents, chunk_document
from src.vectorstore import VectorStore
from src.generator import AnswerGenerator
from src.green_tracker import GreenTracker

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(
        self,
        docs_dir: str = "./documents",
        chroma_dir: str = "./chroma_db",
        top_k: int = 5,
        cache_size: int = 200,
    ):
        self.docs_dir = docs_dir
        self.top_k = top_k
        self.cache_size = max(0, cache_size)

        # In-memory response cache (LRU)
        self._response_cache = OrderedDict()
        self._cache_version = 0

        # Sustainability Tracker (CodeCarbon + GSF SCI metric)
        self.green_tracker = GreenTracker()

        logger.info("Initializing Green-Optimized RAG Pipeline...")
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
        if added:
            self._invalidate_cache()
        logger.info("Ingestion complete. %d new chunks indexed.", added)

    def _invalidate_cache(self):
        self._response_cache.clear()
        self._cache_version += 1

    def _cache_key(
        self,
        question: str,
        search_mode: str,
        doc_type_filter: Optional[str],
        year_filter: Optional[str],
        top_k: int,
    ) -> str:
        payload = {
            "question": question.strip().lower(),
            "search_mode": search_mode,
            "doc_type_filter": doc_type_filter,
            "year_filter": year_filter,
            "top_k": top_k,
            "cache_version": self._cache_version,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def query(
        self,
        question: str,
        search_mode: str = "hybrid",
        doc_type_filter: Optional[str] = None,
        year_filter: Optional[str] = None,
        top_k: Optional[int] = None,
        green_mode: bool = True,
    ) -> Dict:
        """
        Executes query with carbon tracking and green optimization.
        
        Args:
            question: Student inquiry string.
            search_mode: 'hybrid' | 'semantic' | 'keyword'
            doc_type_filter: Optional document category filter
            year_filter: Optional academic year filter
            top_k: Number of chunks retrieved
            green_mode: If True, uses LRU response caching and lean context to minimize energy.
                        If False, bypasses cache to simulate baseline execution.
        """
        k = top_k or self.top_k

        if not question.strip():
            return {"error": "Empty question."}

        key = self._cache_key(question, search_mode, doc_type_filter, year_filter, k)
        task_id = self.green_tracker.start_measurement()
        start_time = time.perf_counter()

        # ── GREEN PATH: Check LRU Response Cache ──────────────────────────────
        if green_mode and self.cache_size > 0 and key in self._response_cache:
            self._response_cache.move_to_end(key)
            duration_sec = time.perf_counter() - start_time
            green_metrics = self.green_tracker.stop_measurement(
                task_name=task_id,
                is_cache_hit=True,
                fallback_duration_sec=duration_sec,
            )
            green_metrics["green_mode"] = True

            cached_resp = dict(self._response_cache[key])
            cached_resp["green_metrics"] = green_metrics
            logger.info("Green optimization: served from cache in %.2f ms", duration_sec * 1000)
            return cached_resp

        # ── STANDARD COMPUTATION PATH (Uncached / Baseline) ────────────────────
        if search_mode == "keyword":
            chunks = self.vector_store.keyword_search(
                question, k, doc_type_filter, year_filter
            )
        elif search_mode == "semantic":
            chunks = self.vector_store.semantic_search(
                question, k, doc_type_filter, year_filter
            )
        else:
            chunks = self.vector_store.hybrid_search(
                question, k, doc_type_filter, year_filter
            )

        # Generate answer using LLM / extractive fallback
        result = self.generator.generate(question, chunks)

        duration_sec = time.perf_counter() - start_time
        green_metrics = self.green_tracker.stop_measurement(
            task_name=task_id,
            is_cache_hit=False,
            fallback_duration_sec=duration_sec,
        )
        green_metrics["green_mode"] = green_mode

        response = {
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
            "filters_applied": {
                "doc_type": doc_type_filter or "all",
                "year": year_filter or "all",
            },
            "green_metrics": green_metrics,
        }

        # Store in LRU cache only if green_mode is enabled
        if green_mode and self.cache_size > 0:
            self._response_cache[key] = response
            self._response_cache.move_to_end(key)
            while len(self._response_cache) > self.cache_size:
                self._response_cache.popitem(last=False)

        return response

    def get_stats(self) -> Dict:
        return {
            "vector_store": self.vector_store.get_stats(),
            "docs_dir": self.docs_dir,
            "generator_model": self.generator.model_name,
            "embedding_cache_hits": getattr(self.vector_store, "embedding_cache_hits", 0),
            "green_sustainability": self.green_tracker.get_summary(),
        }

    def ingest_file(self, filepath: str) -> Dict:
        doc = load_document(filepath)
        if not doc:
            return {"status": "error", "message": f"Could not load: {filepath}"}

        added = self.vector_store.index_chunks(chunk_document(doc))
        if added:
            self._invalidate_cache()

        return {
            "status": "success",
            "filename": doc["filename"],
            "chunks_added": added,
            "doc_type": doc["doc_type"],
            "year": doc["year"],
        }

    def reindex(self) -> Dict:
        self._invalidate_cache()
        self.vector_store.clear()
        self._ingest()
        return {
            "status": "reindexed",
            "total_chunks": self.vector_store.get_stats()["total_chunks"],
        }