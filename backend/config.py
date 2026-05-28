"""LexaTrace — Application Configuration"""

import os
from pathlib import Path

# ── Paths ──
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ── Database ──
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'lexatrace.db'}")

# ── JWT Auth ──
SECRET_KEY = os.getenv("SECRET_KEY", "lexatrace-dev-secret-change-in-production-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# ── File Upload ──
MAX_FILE_SIZE_MB = 15
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".txt",
    ".png", ".jpg", ".jpeg",
    ".zip", ".mp3", ".wav",
}

# ── Similarity Thresholds ──
THRESHOLD_HIGH = 0.90
THRESHOLD_MEDIUM = 0.75
THRESHOLD_LOW = 0.60

# ── ML Model ──
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 512  # tokens per chunk
CHUNK_OVERLAP = 50  # token overlap between chunks
