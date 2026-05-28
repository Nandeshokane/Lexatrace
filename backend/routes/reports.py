"""LexaTrace — Report Routes

Generates risk reports and PDF exports.
"""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from backend.database import get_db, UploadedFile, AnalysisJob, User
from backend.auth import get_current_user
from backend.services.patent_search import search_patents

router = APIRouter(prefix="/api", tags=["Reports"])


@router.get("/reports/{job_id}")
def get_report(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a full risk report for a completed analysis."""
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Analysis not complete. Status: {job.status}")

    file = db.query(UploadedFile).filter(UploadedFile.id == job.file_id).first()
    matches = json.loads(job.results_json) if job.results_json else []

    # Get patent matches (simulated)
    patent_results = []
    if file and file.extracted_text:
        patent_results = search_patents(file.extracted_text[:500])

    return {
        "report_id": job.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "file": {
            "filename": file.filename if file else "unknown",
            "file_type": file.file_type if file else "unknown",
            "file_size": file.file_size if file else 0,
            "word_count": len(file.extracted_text.split()) if file and file.extracted_text else 0,
        },
        "risk_summary": {
            "overall_score": job.risk_score,
            "risk_level": job.risk_level,
            "total_matches": job.total_matches,
            "high_risk": job.high_matches,
            "medium_risk": job.medium_matches,
            "low_risk": job.low_matches,
        },
        "copyright_matches": matches,
        "patent_matches": patent_results,
        "recommendations": _generate_recommendations(matches, patent_results),
        "disclaimer": (
            "This is an automated similarity check, not legal advice. "
            "Consult a qualified IP attorney for legal decisions."
        ),
    }


@router.get("/reports/{job_id}/html")
def get_report_html(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a printable HTML report (can be saved as PDF from browser)."""
    job = db.query(AnalysisJob).filter(
        AnalysisJob.id == job_id,
        AnalysisJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    file = db.query(UploadedFile).filter(UploadedFile.id == job.file_id).first()
    matches = json.loads(job.results_json) if job.results_json else []
    patent_results = search_patents(file.extracted_text[:500]) if file and file.extracted_text else []

    html = _render_report_html(job, file, matches, patent_results)
    return HTMLResponse(content=html)


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get dashboard summary stats for the current user."""
    total_files = db.query(UploadedFile).filter(UploadedFile.user_id == current_user.id).count()
    total_jobs = db.query(AnalysisJob).filter(AnalysisJob.user_id == current_user.id).count()
    completed = db.query(AnalysisJob).filter(
        AnalysisJob.user_id == current_user.id,
        AnalysisJob.status == "completed",
    ).all()

    high_risk_count = sum(1 for j in completed if j.risk_level == "high")
    avg_score = sum(j.risk_score for j in completed) / len(completed) if completed else 0

    recent_jobs = db.query(AnalysisJob).filter(
        AnalysisJob.user_id == current_user.id,
    ).order_by(AnalysisJob.started_at.desc()).limit(5).all()

    return {
        "total_files": total_files,
        "total_analyses": total_jobs,
        "completed_analyses": len(completed),
        "high_risk_files": high_risk_count,
        "average_risk_score": round(avg_score, 1),
        "recent_jobs": [
            {
                "job_id": j.id,
                "status": j.status,
                "risk_score": j.risk_score,
                "risk_level": j.risk_level,
                "started_at": j.started_at.isoformat() if j.started_at else None,
            }
            for j in recent_jobs
        ],
    }


def _generate_recommendations(matches: list, patents: list) -> list[str]:
    """Generate actionable recommendations based on analysis results."""
    recs = []
    high_matches = [m for m in matches if m.get("risk_level") == "high"]
    medium_matches = [m for m in matches if m.get("risk_level") == "medium"]

    if high_matches:
        recs.append("⚠️ HIGH PRIORITY: Rewrite or remove sections with >90% similarity to avoid infringement claims.")
        sources = set(m["source"] for m in high_matches)
        for src in sources:
            recs.append(f"  → Review match with: {src}")

    if medium_matches:
        recs.append("⚡ Add proper citations and attributions for medium-risk matches (75–89% similarity).")

    code_matches = [m for m in matches if m.get("type") == "Source Code"]
    if code_matches:
        recs.append("💻 Check license compatibility for matched code. GPL-licensed code requires derivative works to also be GPL.")

    patent_high = [p for p in patents if p.get("risk_level") == "high"]
    if patent_high:
        recs.append("📋 Consult a patent attorney — potential overlap with existing patents detected.")

    if not recs:
        recs.append("✅ No significant risks detected. Your content appears to be original.")

    recs.append("📌 This analysis is automated. Always consult qualified legal counsel for IP decisions.")
    return recs


def _render_report_html(job, file, matches, patents) -> str:
    """Render a printable HTML report."""
    risk_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e", "clear": "#06b6d4"}
    color = risk_color.get(job.risk_level, "#06b6d4")

    matches_html = ""
    for m in matches:
        mc = risk_color.get(m.get("risk_level", "clear"), "#ccc")
        matches_html += f"""
        <tr>
            <td style="color:{mc};font-weight:700;">{round(m.get('score',0)*100)}%</td>
            <td>{m.get('source','')}</td>
            <td>{m.get('type','')}</td>
            <td>{m.get('section','')}</td>
            <td>{m.get('jurisdiction','')}</td>
        </tr>"""

    patents_html = ""
    for p in patents:
        pc = risk_color.get(p.get("risk_level", "clear"), "#ccc")
        patents_html += f"""
        <tr>
            <td style="color:{pc};font-weight:700;">{round(p.get('relevance_score',0)*100)}%</td>
            <td>{p.get('patent_id','')}</td>
            <td>{p.get('title','')}</td>
            <td>{p.get('office','')}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>LexaTrace Report — {file.filename if file else 'N/A'}</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 0 auto; padding: 40px 24px; color: #1e293b; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  .badge {{ display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;
            background: {color}22; color: {color}; border: 1px solid {color}44; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }}
  th {{ text-align: left; padding: 8px; border-bottom: 2px solid #e2e8f0; font-size: 11px; text-transform: uppercase;
       color: #64748b; letter-spacing: 0.5px; }}
  td {{ padding: 8px; border-bottom: 1px solid #f1f5f9; }}
  .score {{ font-size: 48px; font-weight: 800; color: {color}; }}
  .meta {{ color: #64748b; font-size: 13px; margin: 8px 0; }}
  .disclaimer {{ background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px 16px;
                 font-size: 12px; color: #92400e; margin-top: 32px; }}
  .section {{ margin: 32px 0; }}
  .section h2 {{ font-size: 18px; color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; }}
</style></head><body>
<h1>⬡ LexaTrace — Copyright Analysis Report</h1>
<p class="meta">File: <strong>{file.filename if file else 'N/A'}</strong> · Generated: {job.completed_at or 'N/A'}</p>
<div style="margin:24px 0;">
  <span class="score">{job.risk_score}</span><span style="font-size:20px;color:#64748b;">/100</span>
  <br><span class="badge">{job.risk_level.upper()} RISK</span>
</div>
<div style="display:flex;gap:24px;margin:20px 0;">
  <div><strong style="color:#ef4444;font-size:24px;">{job.high_matches}</strong><br><span class="meta">High Risk</span></div>
  <div><strong style="color:#f59e0b;font-size:24px;">{job.medium_matches}</strong><br><span class="meta">Medium</span></div>
  <div><strong style="color:#22c55e;font-size:24px;">{job.low_matches}</strong><br><span class="meta">Low Risk</span></div>
</div>
<div class="section"><h2>Copyright Matches</h2>
<table><tr><th>Score</th><th>Source</th><th>Type</th><th>Section</th><th>Jurisdiction</th></tr>{matches_html}</table></div>
<div class="section"><h2>Patent Matches</h2>
<table><tr><th>Relevance</th><th>Patent ID</th><th>Title</th><th>Office</th></tr>{patents_html}</table></div>
<div class="disclaimer">⚠️ <strong>Disclaimer:</strong> This is an automated similarity check, not legal advice.
Consult a qualified IP attorney for legal decisions.</div>
</body></html>"""
