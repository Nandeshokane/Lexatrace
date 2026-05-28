"""LexaTrace — FastAPI Application Entry Point

Run with: uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import PROJECT_DIR
from backend.database import init_db
from backend.auth import router as auth_router
from backend.routes.upload import router as upload_router
from backend.routes.analysis import router as analysis_router
from backend.routes.reports import router as reports_router

# ── Create app ──
app = FastAPI(
    title="LexaTrace API",
    description="AI-Powered Copyright Detection & IP Protection Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS — allow frontend to connect ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routers ──
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(analysis_router)
app.include_router(reports_router)

# ── Serve frontend static files ──
app.mount("/", StaticFiles(directory=str(PROJECT_DIR), html=True), name="frontend")


# ── Startup event ──
@app.on_event("startup")
def on_startup():
    print("=" * 50)
    print("  LexaTrace API — Starting Up")
    print("=" * 50)
    init_db()
    print("[✓] Database initialized")
    print("[✓] API docs at: http://localhost:8000/api/docs")
    print("[✓] Frontend at: http://localhost:8000/")
    print("=" * 50)
