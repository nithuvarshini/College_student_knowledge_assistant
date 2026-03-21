"""
src/loader.py
Loads text from TXT, PDF, DOCX, and HTML files.
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


def load_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def load_pdf(filepath: str) -> str:
    try:
        import fitz
        doc = fitz.open(filepath)
        text = ""
        for page_num, page in enumerate(doc, 1):
            text += f"\n[Page {page_num}]\n{page.get_text()}"
        doc.close()
        return text
    except Exception as e:
        logger.error("Error loading PDF %s: %s", filepath, e)
        return ""


def load_docx(filepath: str) -> str:
    try:
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        logger.error("Error loading DOCX %s: %s", filepath, e)
        return ""


def load_html(filepath: str) -> str:
    try:
        from bs4 import BeautifulSoup
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return BeautifulSoup(f.read(), "html.parser").get_text(separator="\n")
    except Exception as e:
        logger.error("Error loading HTML %s: %s", filepath, e)
        return ""


def detect_doc_type(filename: str) -> str:
    name = filename.lower()
    if "handbook" in name or "discipline" in name:
        return "handbook"
    elif "calendar" in name or "schedule" in name or "timetable" in name:
        return "calendar"
    elif "placement" in name or "internship" in name:
        return "placement"
    elif "fee" in name or "scholarship" in name or "finance" in name:
        return "fees_scholarships"
    elif "syllabus" in name or "course" in name or "curriculum" in name:
        return "syllabus"
    elif "library" in name:
        return "library"
    elif "admin" in name or "service" in name or "certificate" in name:
        return "admin"
    return "general"


def detect_year(filename: str) -> str:
    match = re.search(r"(20\d{2})", filename)
    return match.group(1) if match else "unknown"


def load_document(filepath: str) -> Dict:
    path = Path(filepath)
    ext = path.suffix.lower()
    loaders = {".txt": load_txt, ".pdf": load_pdf, ".docx": load_docx, ".html": load_html, ".htm": load_html}
    if ext not in loaders:
        return {}
    text = loaders[ext](filepath)
    if not text.strip():
        return {}
    return {
        "filename": path.name,
        "filepath": str(filepath),
        "doc_type": detect_doc_type(path.name),
        "year": detect_year(path.name),
        "content": text.strip(),
    }


def load_documents_from_dir(directory: str) -> List[Dict]:
    supported = {".txt", ".pdf", ".docx", ".html", ".htm"}
    docs = []
    for filepath in Path(directory).iterdir():
        if filepath.suffix.lower() in supported:
            doc = load_document(str(filepath))
            if doc:
                docs.append(doc)
                logger.info("Loaded: %s", filepath.name)
    logger.info("Total documents loaded: %d", len(docs))
    return docs
