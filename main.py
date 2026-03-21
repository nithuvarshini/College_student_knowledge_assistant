"""
main.py — College Student Knowledge Assistant API
Run with: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import logging
import tempfile
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "documents")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")

rag = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag
    logger.info("Starting College RAG system...")
    from src.rag_pipeline import RAGPipeline
    rag = RAGPipeline(docs_dir=DOCS_DIR, chroma_dir=CHROMA_DIR, top_k=5)
    logger.info("RAG system ready!")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="College Student Knowledge Assistant",
    description="RAG-powered API that answers student queries using official college documents.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Models ──────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    search_mode: str = "hybrid"
    doc_type_filter: Optional[str] = None
    year_filter: Optional[str] = None
    top_k: int = 5

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What is the minimum attendance required?",
                "search_mode": "hybrid",
                "doc_type_filter": None,
                "year_filter": "2025",
                "top_k": 5,
            }
        }
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "College Student Knowledge Assistant is running!",
        "swagger_ui": "/docs",
        "endpoints": ["POST /query", "POST /upload", "GET /stats", "POST /reindex", "GET /doc-types"],
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "pipeline_ready": rag is not None}


@app.post("/query", tags=["RAG"])
def query(request: QueryRequest):
    """
    Ask a student question. Returns an answer grounded in official college documents with citations.

    - search_mode: hybrid (recommended) | semantic | keyword
    - doc_type_filter: handbook | syllabus | placement | fees_scholarships | library | admin | calendar
    - year_filter: e.g. 2025
    """
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if request.search_mode not in ("hybrid", "semantic", "keyword"):
        raise HTTPException(status_code=400, detail="search_mode must be hybrid, semantic, or keyword.")

    result = rag.query(
        question=request.question,
        search_mode=request.search_mode,
        doc_type_filter=request.doc_type_filter,
        year_filter=request.year_filter,
        top_k=request.top_k,
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/upload", tags=["Documents"])
async def upload(file: UploadFile = File(...)):
    """Upload a TXT, PDF, DOCX, or HTML file to be indexed immediately."""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready.")

    allowed = {".txt", ".pdf", ".docx", ".html", ".htm"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed)}")

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = rag.ingest_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    if result.get("status") == "error":
        raise HTTPException(status_code=422, detail=result["message"])

    return {"message": f"'{file.filename}' ingested successfully.", "details": result}


@app.get("/stats", tags=["Admin"])
def stats():
    """Returns total indexed chunks, model info, and vector store details."""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready.")
    return rag.get_stats()


@app.post("/reindex", tags=["Admin"])
def reindex():
    """Clears the vector store and re-ingests all documents from the documents folder."""
    if rag is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not ready.")
    return rag.reindex()


@app.get("/doc-types", tags=["Documents"])
def doc_types():
    """Returns all valid doc_type_filter values for the /query endpoint."""
    return {
        "doc_types": ["handbook", "syllabus", "placement", "fees_scholarships", "library", "admin", "calendar", "general"],
        "usage": "Pass one as doc_type_filter in POST /query to restrict search to that document type.",
    }
