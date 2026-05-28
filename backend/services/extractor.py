"""LexaTrace — Text Extraction Service

Extracts text from PDF, DOCX, TXT, and code files.
"""

import zipfile
from pathlib import Path

from backend.config import CHUNK_SIZE, CHUNK_OVERLAP


def extract_text(file_path: str, file_type: str) -> str:
    """Extract raw text from a file based on its type."""
    path = Path(file_path)

    if file_type == "pdf":
        return _extract_pdf(path)
    elif file_type == "docx":
        return _extract_docx(path)
    elif file_type == "txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    elif file_type == "code":
        return _extract_zip(path)
    elif file_type in ("png", "jpg", "jpeg", "image"):
        return "[Image file — visual analysis only]"
    else:
        return path.read_text(encoding="utf-8", errors="ignore")


def _extract_pdf(path: Path) -> str:
    """Extract text from PDF using pdfminer."""
    try:
        from pdfminer.high_level import extract_text as pdf_extract
        return pdf_extract(str(path))
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def _extract_docx(path: Path) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def _extract_zip(path: Path) -> str:
    """Extract text from source code files in a ZIP archive."""
    code_extensions = {".py", ".js", ".java", ".ts", ".jsx", ".tsx", ".c", ".cpp", ".h", ".go", ".rs"}
    texts = []
    try:
        with zipfile.ZipFile(str(path), "r") as zf:
            for name in zf.namelist():
                ext = Path(name).suffix.lower()
                if ext in code_extensions:
                    try:
                        content = zf.read(name).decode("utf-8", errors="ignore")
                        texts.append(f"// === {name} ===\n{content}")
                    except Exception:
                        continue
    except Exception as e:
        return f"[ZIP extraction error: {e}]"

    return "\n\n".join(texts) if texts else "[No source code files found in archive]"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by approximate token count.

    Uses simple word-based splitting (1 word ≈ 1.3 tokens).
    """
    words = text.split()
    if not words:
        return []

    # Approximate: 1 token ≈ 0.75 words
    words_per_chunk = int(chunk_size * 0.75)
    words_overlap = int(overlap * 0.75)

    chunks = []
    start = 0
    while start < len(words):
        end = start + words_per_chunk
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += words_per_chunk - words_overlap

    return chunks
