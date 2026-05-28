"""LexaTrace — Analysis Routes

Triggers the analysis pipeline: extract → chunk → embed → search → score.
Uses FastAPI BackgroundTasks for async processing.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db, UploadedFile, AnalysisJob, User
from backend.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Analysis"])


def run_analysis(job_id: str, file_id: str, db_url: str):
    """Background task that runs the full analysis pipeline."""
    from backend.database import SessionLocal
    from backend.services.extractor import extract_text, chunk_text
    from backend.services.embeddings import embed_chunks
    from backend.services.similarity import find_matches, compute_overall_risk

    db = SessionLocal()
    try:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not job or not file:
            return

        # Step 1: Extract text
        job.status = "extracting"
        db.commit()

        text = file.extracted_text
        if not text or text.startswith("["):
            text = extract_text(file.storage_path, file.file_type)
            file.extracted_text = text
            db.commit()

        if not text or len(text.strip()) < 20:
            job.status = "completed"
            job.risk_score = 0.0
            job.risk_level = "clear"
            job.results_json = "[]"
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        # Step 2: Chunk text
        job.status = "chunking"
        db.commit()
        chunks = chunk_text(text)

        # Step 3: Generate embeddings
        job.status = "embedding"
        db.commit()
        chunk_embeddings = embed_chunks(chunks)

        # Step 4: Similarity search
        job.status = "searching"
        db.commit()
        matches = find_matches(chunk_embeddings, chunks)

        # Step 5: Compute risk score
        job.status = "scoring"
        db.commit()
        risk = compute_overall_risk(matches)

        # Save results
        job.status = "completed"
        job.risk_score = risk["risk_score"]
        job.risk_level = risk["risk_level"]
        job.total_matches = risk["total"]
        job.high_matches = risk["high"]
        job.medium_matches = risk["medium"]
        job.low_matches = risk["low"]
        job.results_json = json.dumps(matches)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/analyze/{file_id}")
def trigger_analysis(
    file_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger copyright analysis for an uploaded file."""
    file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == current_user.id,
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # Create analysis job
    job = AnalysisJob(
        file_id=file.id,
        user_id=current_user.id,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch background analysis
    from backend.config import DATABASE_URL
    background_tasks.add_task(run_analysis, job.id, file.id, DATABASE_URL)

    return {
        "job_id": job.id,
        "file_id": file.id,
        "status": "pending",
        "message": "Analysis started. Poll GET /api/analysis/{job_id} for status.",
    }


@router.get("/analysis/{job_id}")
def get_analysis(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the status and results of an analysis job."""
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Analysis job not found")

    file = db.query(UploadedFile).filter(UploadedFile.id == job.file_id).first()

    result = {
        "job_id": job.id,
        "file_id": job.file_id,
        "filename": file.filename if file else "unknown",
        "status": job.status,
        "risk_score": job.risk_score,
        "risk_level": job.risk_level,
        "total_matches": job.total_matches,
        "high_matches": job.high_matches,
        "medium_matches": job.medium_matches,
        "low_matches": job.low_matches,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }

    if job.status == "completed":
        result["matches"] = json.loads(job.results_json)
    elif job.status == "failed":
        result["error"] = job.error_message

    return result


@router.get("/jobs")
def list_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all analysis jobs for the current user."""
    jobs = db.query(AnalysisJob).filter(AnalysisJob.user_id == current_user.id).order_by(AnalysisJob.started_at.desc()).all()
    results = []
    for job in jobs:
        file = db.query(UploadedFile).filter(UploadedFile.id == job.file_id).first()
        results.append({
            "job_id": job.id,
            "filename": file.filename if file else "unknown",
            "status": job.status,
            "risk_score": job.risk_score,
            "risk_level": job.risk_level,
            "total_matches": job.total_matches,
            "started_at": job.started_at.isoformat() if job.started_at else None,
        })
    return results
