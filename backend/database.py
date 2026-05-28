"""LexaTrace — Database Models & Session Setup"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime,
    ForeignKey, Enum, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from backend.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def gen_uuid() -> str:
    return str(uuid.uuid4())


# ── User Model ──
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    projects = relationship("Project", back_populates="owner")


# ── Project Model ──
class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    files = relationship("UploadedFile", back_populates="project")


# ── Uploaded File Model ──
class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, docx, txt, image, code
    file_size = Column(Integer, default=0)
    storage_path = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    extracted_text = Column(Text, default="")

    project = relationship("Project", back_populates="files")
    analysis_jobs = relationship("AnalysisJob", back_populates="file")


# ── Analysis Job Model ──
class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=gen_uuid)
    file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(
        String, default="pending"
    )  # pending, extracting, embedding, searching, scoring, completed, failed
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="clear")  # high, medium, low, clear
    total_matches = Column(Integer, default=0)
    high_matches = Column(Integer, default=0)
    medium_matches = Column(Integer, default=0)
    low_matches = Column(Integer, default=0)
    results_json = Column(Text, default="[]")  # JSON array of match results
    error_message = Column(Text, default="")
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    file = relationship("UploadedFile", back_populates="analysis_jobs")


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
