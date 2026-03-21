"""
src/generator.py
Generates answers using HuggingFace flan-t5-base (~300MB, CPU-friendly).
Falls back to extractive method if model fails.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)
HF_MODEL = "google/flan-t5-base"


class AnswerGenerator:
    def __init__(self):
        self.model_name = HF_MODEL
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        try:
            from transformers import pipeline
            logger.info("Loading LLM: %s (first run downloads ~300MB)...", self.model_name)
            self.pipeline = pipeline(
                "text2text-generation",
                model=self.model_name,
                max_new_tokens=256,
                do_sample=False,
            )
            logger.info("LLM loaded successfully.")
        except Exception as e:
            logger.warning("Could not load HuggingFace model: %s. Using extractive fallback.", e)
            self.pipeline = None

    def generate(self, query: str, chunks: List[Dict]) -> Dict:
        if not chunks:
            return {
                "answer": "I could not find any relevant information for this question in the official college documents. This topic may not be covered in the available documents. Please contact the relevant office directly or check the college portal.",
                "citations": [],
                "model": "no-results",
            }

        context = "\n\n---\n\n".join(
            f"[Source: {c.get('filename', 'Unknown')}]\n{c.get('text', '').strip()}"
            for c in chunks
        )

        prompt = (
            "You are a helpful college information assistant. "
            "Answer the student question using ONLY the context below. "
            "Be clear and concise. "
            "If the answer is not in the context say: I could not find this in the official documents.\n\n"
            f"Context:\n{context}\n\n"
            f"Student Question: {query}\n\n"
            "Answer:"
        )

        if self.pipeline:
            try:
                output = self.pipeline(prompt, max_new_tokens=256)
                answer = output[0]["generated_text"].strip()
                if "Answer:" in answer:
                    answer = answer.split("Answer:")[-1].strip()
                if answer:
                    return {"answer": answer, "citations": self._citations(chunks), "model": self.model_name}
            except Exception as e:
                logger.warning("Generation error: %s. Using extractive fallback.", e)

        return {
            "answer": self._extractive(query, chunks),
            "citations": self._citations(chunks),
            "model": "extractive-fallback",
        }

    def _extractive(self, query: str, chunks: List[Dict]) -> str:
        """Return clean relevant paragraphs from the best matching chunk."""
        if not chunks:
            return "No answer found."

        query_words = set(query.lower().split())
        scored_paras = []

        for chunk in chunks[:3]:
            text = chunk.get("text", "").strip()
            paragraphs = [p.strip() for p in text.split("\n") if p.strip() and len(p.strip()) > 20]
            for para in paragraphs:
                overlap = len(query_words & set(para.lower().split()))
                if overlap >= 1:
                    scored_paras.append((overlap, para))

        if scored_paras:
            scored_paras.sort(reverse=True)
            top_paras = [p for _, p in scored_paras[:3]]
            return "\n".join(top_paras)

        # Last resort: return first 600 chars of best chunk
        return chunks[0]["text"][:600]

    def _citations(self, chunks: List[Dict]) -> List[Dict]:
        seen = set()
        out = []
        for c in chunks:
            fname = c.get("filename", "Unknown")
            if fname not in seen:
                seen.add(fname)
                out.append({
                    "source": fname,
                    "doc_type": c.get("doc_type", "general"),
                    "year": c.get("year", "unknown"),
                    "snippet": c.get("text", "")[:200] + "...",
                })
        return out