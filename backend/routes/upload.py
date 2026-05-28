"""LexaTrace — File Upload Routes"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.config import UPLOAD_DIR, MAX_FILE_SIZE_MB, ALLOWED_EXTENSIONS
from backend.database import get_db, UploadedFile, User
from backend.auth import get_current_user

router = APIRouter(prefix="/api", tags=["File Upload"])


def _get_file_type(filename: str) -> str:
    """Determine file type category from extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    elif ext == ".txt":
        return "txt"
    elif ext in (".png", ".jpg", ".jpeg"):
        return "image"
    elif ext == ".zip":
        return "code"
    elif ext in (".mp3", ".wav"):
        return "audio"
    return "unknown"


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a file for copyright analysis."""
    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Read and validate size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File too large ({size_mb:.1f}MB). Max: {MAX_FILE_SIZE_MB}MB")

    # Save to disk
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}{ext}"
    save_path = UPLOAD_DIR / safe_name
    save_path.write_bytes(content)

    # Extract text immediately for text-based files
    file_type = _get_file_type(file.filename)
    extracted_text = ""
    if file_type in ("pdf", "docx", "txt", "code"):
        from backend.services.extractor import extract_text
        extracted_text = extract_text(str(save_path), file_type)

    # Save to database
    db_file = UploadedFile(
        id=file_id,
        filename=file.filename,
        file_type=file_type,
        file_size=len(content),
        storage_path=str(save_path),
        user_id=current_user.id,
        extracted_text=extracted_text,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return {
        "file_id": db_file.id,
        "filename": db_file.filename,
        "file_type": db_file.file_type,
        "file_size": db_file.file_size,
        "text_length": len(extracted_text),
        "message": "File uploaded successfully",
    }


@router.get("/files")
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all uploaded files for the current user."""
    files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).all()
    return [
        {
            "file_id": f.id,
            "filename": f.filename,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
            "has_text": bool(f.extracted_text),
        }
        for f in files
    ]
