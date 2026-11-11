"""
Unit tests for Module 5: Database Layer & Data Ingestion (database/db.py & database/load_data.py)
Tests verify schema creation, model relationships, session transactions,
and duplicate prevention during data import using an isolated test database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.db import (
    Base,
    Company,
    JobPosting,
    JobSkill,
    Skill,
    check_db_connection,
    get_db_session,
    init_db,
)
from database.load_data import import_job_market_data


@pytest.fixture
def test_db_engine(tmp_path):
    """Creates an isolated temporary SQLite database for testing."""
    db_file = tmp_path / "test_job_market.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    init_db(engine)
    return engine


def test_database_connection_checker(test_db_engine):
    """Verify connection check returns True on valid database."""
    ok, msg = check_db_connection(str(test_db_engine.url))
    assert ok is True
    assert "successful" in msg.lower()


def test_create_company_and_unique_constraint(test_db_engine):
    """Verify Company creation and uniqueness on company name."""
    with get_db_session(test_db_engine) as session:
        comp = Company(name="TestTech Analytics")
        session.add(comp)

    with get_db_session(test_db_engine) as session:
        queried = session.query(Company).filter_by(name="TestTech Analytics").first()
        assert queried is not None
        assert queried.name == "TestTech Analytics"

    # Test duplicate name raises exception and rolls back
    with pytest.raises(Exception):
        with get_db_session(test_db_engine) as session:
            session.add(Company(name="TestTech Analytics"))


def test_create_job_posting_and_company_relationship(test_db_engine):
    """Verify JobPosting creation and foreign key relationship to Company."""
    with get_db_session(test_db_engine) as session:
        comp = Company(name="InnoSoft Systems")
        session.add(comp)
        session.flush()

        posting = JobPosting(
            job_id="JOB_TEST_001",
            job_title="Senior Data Scientist",
            clean_role="Data Scientist",
            company_id=comp.id,
            city="Bengaluru",
            salary_mid_lpa=18.5,
            is_salary_valid=True,
        )
        session.add(posting)

    with get_db_session(test_db_engine) as session:
        job = session.query(JobPosting).filter_by(job_id="JOB_TEST_001").first()
        assert job is not None
        assert job.clean_role == "Data Scientist"
        assert job.company.name == "InnoSoft Systems"


def test_job_skill_association_and_uniqueness(test_db_engine):
    """Verify JobSkill link between JobPosting and Skill, and unique constraint."""
    with get_db_session(test_db_engine) as session:
        job = JobPosting(
            job_id="JOB_TEST_002",
            job_title="Cloud Engineer",
            clean_role="Cloud Engineer",
        )
        skill = Skill(name="Kubernetes")
        session.add_all([job, skill])
        session.flush()

        js = JobSkill(job_posting_id=job.id, skill_id=skill.id)
        session.add(js)

    with get_db_session(test_db_engine) as session:
        saved_js = session.query(JobSkill).first()
        assert saved_js is not None
        assert saved_js.skill.name == "Kubernetes"
        assert saved_js.job_posting.clean_role == "Cloud Engineer"

    # Verify duplicate pair raises IntegrityError
    with pytest.raises(Exception):
        with get_db_session(test_db_engine) as session:
            saved_js = session.query(JobSkill).first()
            duplicate_js = JobSkill(
                job_posting_id=saved_js.job_posting_id,
                skill_id=saved_js.skill_id,
            )
            session.add(duplicate_js)


def test_import_job_market_data_batch_and_duplicate_prevention(test_db_engine):
    """Verify batch data import and duplicate skip logic on re-import."""
    # First import
    res1 = import_job_market_data(engine=test_db_engine, limit=50)
    assert res1["status"] == "SUCCESS"
    assert res1["new_postings_inserted"] == 50
    assert res1["skipped_duplicate_postings"] == 0

    # Second import with same 50 records (safe re-run)
    res2 = import_job_market_data(engine=test_db_engine, limit=50)
    assert res2["status"] == "SUCCESS"
    assert res2["new_postings_inserted"] == 0
    assert res2["skipped_duplicate_postings"] == 50


def test_session_transaction_rollback_on_error(test_db_engine):
    """Verify automatic transaction rollback when an exception occurs inside get_db_session."""
    with pytest.raises(ValueError):
        with get_db_session(test_db_engine) as session:
            session.add(Company(name="Rollback Inc"))
            session.flush()
            raise ValueError("Intentional transaction abort")

    # Verify Company was rolled back and does not exist in DB
    with get_db_session(test_db_engine) as session:
        c = session.query(Company).filter_by(name="Rollback Inc").first()
        assert c is None

