"""
src/chunker.py
Splits document text into overlapping chunks for embedding and retrieval.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

CHUNK_SIZE = 600
CHUNK_OVERLAP = 150


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current.strip())
            if len(para) > chunk_size:
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sub = ""
                for sent in sentences:
                    if len(sub) + len(sent) + 1 <= chunk_size:
                        sub += (" " if sub else "") + sent
                    else:
                        if sub:
                            chunks.append(sub.strip())
                        sub = sent
                current = sub
            else:
                overlap_text = chunks[-1][-overlap:] if chunks else ""
                current = (overlap_text + "\n\n" + para) if overlap_text else para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def chunk_document(doc: Dict) -> List[Dict]:
    text = doc.get("content", "")
    if not text:
        return []
    chunks = split_into_chunks(text)
    return [
        {
            "chunk_id": f"{doc['filename']}_chunk_{i}",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "text": chunk_text,
            "filename": doc["filename"],
            "filepath": doc["filepath"],
            "doc_type": doc.get("doc_type", "general"),
            "year": doc.get("year", "unknown"),
        }
        for i, chunk_text in enumerate(chunks)
    ]


def chunk_all_documents(docs: List[Dict]) -> List[Dict]:
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    logger.info("Total chunks created: %d from %d documents", len(all_chunks), len(docs))
    return all_chunks
