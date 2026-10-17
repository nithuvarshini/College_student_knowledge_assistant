"""
src/vectorstore.py
ChromaDB vector store with semantic, keyword, and hybrid search.
Uses sentence-transformers all-MiniLM-L6-v2 (~90MB).
"""

import os
import logging
from typing import List, Dict, Optional
from tqdm import tqdm
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
COLLECTION_NAME = "college_docs"


class VectorStore:
    def __init__(self, persist_dir: str = "./chroma_db"):
        os.makedirs(persist_dir, exist_ok=True)
        logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store ready. Chunks indexed: %d", self.collection.count())
        self._embedding_cache: Dict[str, List[float]] = {}
        self.embedding_cache_hits = 0

    def embed(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        # Green optimization: query embedding caching
        if use_cache and len(texts) == 1:
            t = texts[0]
            if t in self._embedding_cache:
                self.embedding_cache_hits += 1
                return [self._embedding_cache[t]]
            vec = self.embedder.encode(texts, show_progress_bar=False).tolist()
            if len(self._embedding_cache) < 500:
                self._embedding_cache[t] = vec[0]
            return vec
        return self.embedder.encode(texts, show_progress_bar=False).tolist()

    def index_chunks(self, chunks: List[Dict], batch_size: int = 64) -> int:
        existing = set()
        if self.collection.count() > 0:
            existing = set(self.collection.get(include=[])["ids"])

        new_chunks = [c for c in chunks if c["chunk_id"] not in existing]
        if not new_chunks:
            logger.info("All chunks already indexed.")
            return 0

        logger.info("Indexing %d new chunks...", len(new_chunks))
        for i in tqdm(range(0, len(new_chunks), batch_size), desc="Indexing"):
            batch = new_chunks[i: i + batch_size]
            self.collection.add(
                ids=[c["chunk_id"] for c in batch],
                documents=[c["text"] for c in batch],
                embeddings=self.embed([c["text"] for c in batch], use_cache=False),
                metadatas=[
                    {
                        "filename": c["filename"],
                        "filepath": c["filepath"],
                        "doc_type": c["doc_type"],
                        "year": c["year"],
                        "chunk_index": c["chunk_index"],
                        "total_chunks": c["total_chunks"],
                    }
                    for c in batch
                ],
            )
        logger.info("Indexing done. Total chunks: %d", self.collection.count())
        return len(new_chunks)

    def semantic_search(self, query: str, top_k: int = 5, doc_type_filter: Optional[str] = None, year_filter: Optional[str] = None, use_cache: bool = True) -> List[Dict]:
        where = self._build_filter(doc_type_filter, year_filter)
        results = self.collection.query(
            query_embeddings=self.embed([query], use_cache=use_cache),
            n_results=min(top_k, max(self.collection.count(), 1)),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        return self._format(results, "semantic")

    def keyword_search(self, query: str, top_k: int = 5, doc_type_filter: Optional[str] = None, year_filter: Optional[str] = None, use_cache: bool = True) -> List[Dict]:
        keywords = [w for w in query.split() if len(w) > 3]
        if not keywords:
            return self.semantic_search(query, top_k, doc_type_filter, year_filter, use_cache=use_cache)
        primary = max(keywords, key=len)
        where = self._build_filter(doc_type_filter, year_filter)
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k * 2, max(self.collection.count(), 1)),
                where=where,
                where_document={"$contains": primary},
                include=["documents", "metadatas", "distances"],
            )
            formatted = self._format(results, "keyword")
            if formatted:
                return formatted[:top_k]
        except Exception as e:
            logger.debug("Keyword search failed: %s. Falling back to semantic.", e)
        return self.semantic_search(query, top_k, doc_type_filter, year_filter, use_cache=use_cache)

    def hybrid_search(self, query: str, top_k: int = 5, doc_type_filter: Optional[str] = None, year_filter: Optional[str] = None, use_cache: bool = True) -> List[Dict]:
        seen = set()
        merged = []
        for result in self.semantic_search(query, top_k, doc_type_filter, year_filter, use_cache=use_cache) + self.keyword_search(query, top_k, doc_type_filter, year_filter, use_cache=use_cache):
            if result["chunk_id"] not in seen:
                seen.add(result["chunk_id"])
                merged.append(result)
        merged.sort(key=lambda x: x.get("score", 1.0))
        return merged[:top_k]

    def _build_filter(self, doc_type: Optional[str], year: Optional[str]) -> Optional[Dict]:
        conditions = []
        if doc_type and doc_type != "all":
            conditions.append({"doc_type": {"$eq": doc_type}})
        if year and year != "all":
            conditions.append({"year": {"$eq": year}})
        if not conditions:
            return None
        return conditions[0] if len(conditions) == 1 else {"$and": conditions}

    def _format(self, results: Dict, search_type: str, threshold: float = 0.5) -> List[Dict]:
        out = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return out
        for chunk_id, text, meta, dist in zip(results["ids"][0], results["documents"][0], results["metadatas"][0], results["distances"][0]):
            if dist > threshold:
                logger.debug("Chunk '%s' rejected — score %.4f above threshold %.2f", chunk_id, dist, threshold)
                continue
            out.append({
                "chunk_id": chunk_id,
                "text": text,
                "filename": meta.get("filename", "Unknown"),
                "filepath": meta.get("filepath", ""),
                "doc_type": meta.get("doc_type", "general"),
                "year": meta.get("year", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "score": round(dist, 4),
                "search_type": search_type,
            })
        return out

    def get_stats(self) -> Dict:
        return {
            "total_chunks": self.collection.count(),
            "collection_name": COLLECTION_NAME,
            "embedding_model": EMBEDDING_MODEL,
        }

    def clear(self):
        self.client.delete_collection(COLLECTION_NAME)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("Vector store cleared.")
