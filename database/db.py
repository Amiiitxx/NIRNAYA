"""
Module: Database Models & Session Management
Description: Production SQLAlchemy ORM models, connection validation, and session
management supporting PostgreSQL and SQLite for job postings, companies, and skills.
"""

import os
from contextlib import contextmanager
from typing import Generator, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
    text,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session

# Load environment configuration
load_dotenv()

Base = declarative_base()


# ---------------------------------------------------------
# DATABASE CONFIGURATION & URL BUILDER
# ---------------------------------------------------------

def get_database_url() -> str:
    """
    Constructs the database connection string from environment variables.
    Supports PostgreSQL configuration with SQLite fallback.
    """
    # 1. Direct DATABASE_URL in .env
    env_url = os.getenv("DATABASE_URL")
    if env_url and env_url.strip():
        # Handle postgres:// legacy prefixes
        if env_url.startswith("postgres://"):
            return env_url.replace("postgres://", "postgresql+psycopg2://", 1)
        return env_url

    # 2. Reconstruct PostgreSQL URL from standard DB_* or POSTGRES_* environment variables
    user = os.getenv("DB_USER") or os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("DB_HOST") or os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("DB_PORT") or os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("DB_NAME") or os.getenv("POSTGRES_DB", "job_market_db")

    # Use psycopg2 driver for stability
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"


# ---------------------------------------------------------
# RELATIONAL MODELS
# ---------------------------------------------------------

class Company(Base):
    """
    Normalized company entity representing recruiting organizations.
    """
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_postings = relationship("JobPosting", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name='{self.name}')>"


class Skill(Base):
    """
    Canonical technical skill entity.
    """
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job_skills = relationship("JobSkill", back_populates="skill", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}')>"


class JobPosting(Base):
    """
    Core job market posting entity storing clean market attributes, salary disclosures,
    and metadata.
    """
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), unique=True, nullable=False, index=True)
    job_title = Column(String(150), nullable=False, index=True)
    clean_role = Column(String(150), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    city = Column(String(100), nullable=True, index=True)
    state = Column(String(100), nullable=True)
    experience_level = Column(String(50), nullable=True, index=True)
    experience_years = Column(Float, nullable=True)
    education = Column(String(100), nullable=True)
    employment_type = Column(String(50), nullable=True)
    work_mode = Column(String(50), nullable=True, index=True)
    salary_min_lpa = Column(Float, nullable=True)
    salary_max_lpa = Column(Float, nullable=True)
    salary_mid_lpa = Column(Float, nullable=True, index=True)
    salary_annual_inr = Column(BigInteger, nullable=True)
    is_salary_valid = Column(Boolean, default=False, index=True)
    company_size = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    posted_date = Column(String(50), nullable=True)
    posted_year = Column(Integer, nullable=True)
    posted_month = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company = relationship("Company", back_populates="job_postings")
    job_skills = relationship("JobSkill", back_populates="job_posting", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_job_role_city", "clean_role", "city"),
        Index("ix_job_exp_salary", "experience_level", "salary_mid_lpa"),
    )

    def __repr__(self) -> str:
        return f"<JobPosting(id={self.id}, job_id={self.job_id}, role='{self.clean_role}', city='{self.city}')>"


class JobSkill(Base):
    """
    Association table linking job postings with individual technical skills.
    Enforces uniqueness so a skill is linked at most once per job posting.
    """
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    job_posting = relationship("JobPosting", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills")

    __table_args__ = (
        UniqueConstraint("job_posting_id", "skill_id", name="uq_job_posting_skill"),
    )

    def __repr__(self) -> str:
        return f"<JobSkill(job_id={self.job_posting_id}, skill_id={self.skill_id})>"


# ---------------------------------------------------------
# ENGINE & SESSION MANAGEMENT
# ---------------------------------------------------------

_ENGINE = None
_SESSION_FACTORY = None


def get_engine(db_url: Optional[str] = None):
    """
    Creates and caches the SQLAlchemy engine with pool management.
    """
    global _ENGINE, _SESSION_FACTORY
    target_url = db_url or get_database_url()

    # If already created with same URL, return cached
    if _ENGINE is not None and db_url is None:
        return _ENGINE

    # Engine arguments
    connect_args = {}
    if target_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(
        target_url,
        connect_args=connect_args,
        pool_pre_ping=True,
    )

    if db_url is None:
        _ENGINE = engine
        _SESSION_FACTORY = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)

    return engine


def get_session_factory(engine=None):
    """Returns sessionmaker bound to current engine."""
    eng = engine or get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=eng)


def check_db_connection(db_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validates database connectivity.
    Returns (True, 'Connected') or (False, error_details).
    """
    target_url = db_url or get_database_url()
    try:
        engine = create_engine(target_url, connect_args={"connect_timeout": 3} if "postgresql" in target_url else {})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Database connection successful."
    except Exception as e:
        return False, str(e)


def init_db(engine=None) -> None:
    """
    Creates all relational tables defined on Base if they do not exist.
    """
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)


@contextmanager
def get_db_session(engine=None) -> Generator[Session, None, None]:
    """
    Transactional context manager providing a safe SQLAlchemy session with
    automatic commit and rollback.
    """
    factory = get_session_factory(engine)
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency generator yielding a database session per request.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()
