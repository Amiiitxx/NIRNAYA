"""
Module: Database Data Ingestion Pipeline
Description: High-performance batch ingestion pipeline loading cleaned job market data
into PostgreSQL / SQLite relational tables with duplicate prevention and validation.
"""

import os
import sys
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from database.db import (
    Company,
    JobPosting,
    JobSkill,
    Skill,
    check_db_connection,
    get_database_url,
    get_db_session,
    get_engine,
    init_db,
)
from src.skill_analyzer import ROLE_NORMALIZATION_MAP

DEFAULT_DATA_PATH = os.path.join("data", "processed", "cleaned_job_market_all.csv")


def load_dataset_file(csv_path: Optional[str] = None) -> pd.DataFrame:
    """Validates and loads the cleaned CSV dataset."""
    path = csv_path or DEFAULT_DATA_PATH
    if not os.path.exists(path):
        candidate_paths = [
            path,
            os.path.join("..", path),
            os.path.join("data", "processed", "cleaned_job_market_all.csv"),
            os.path.join("..", "data", "processed", "cleaned_job_market_all.csv"),
        ]
        path = next((p for p in candidate_paths if os.path.exists(p)), None)

    if path is None or not os.path.exists(path):
        raise FileNotFoundError(f"Cleaned job market dataset not found at: {path}")

    df = pd.read_csv(path)

    required_cols = ["job_id", "job_title", "skills_required_clean"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset missing mandatory schema columns: {missing}")

    return df


def import_job_market_data(
    csv_path: Optional[str] = None,
    batch_size: int = 2000,
    engine=None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Ingests cleaned job postings, normalizes companies and technical skills,
    and maps relationships with duplicate prevention.

    Args:
        csv_path: Path to cleaned_job_market_all.csv.
        batch_size: Number of records to insert per batch.
        engine: SQLAlchemy engine. If None, uses default configured engine.
        limit: Optional cap on imported records (useful for testing).

    Returns:
        Dict summarizing import metrics.
    """
    start_time = time.time()
    eng = engine or get_engine()

    # 1. Initialize schema tables
    init_db(eng)

    # 2. Ingest CSV data
    df = load_dataset_file(csv_path)
    if limit is not None and limit > 0:
        df = df.head(limit)

    total_rows = len(df)
    print(f"Starting database import: {total_rows:,} records from CSV...")

    with get_db_session(eng) as session:
        # 3. Cache existing Companies to prevent duplicates
        existing_companies = {c.name: c.id for c in session.query(Company).all()}
        unique_companies_in_csv = df["company_name"].dropna().unique()
        new_companies = [
            Company(name=str(name).strip())
            for name in unique_companies_in_csv
            if str(name).strip() and str(name).strip() not in existing_companies
        ]
        if new_companies:
            session.add_all(new_companies)
            session.flush()
            # Refresh cache
            existing_companies = {c.name: c.id for c in session.query(Company).all()}
        print(f"Companies synced: {len(existing_companies)} companies in database.")

        # 4. Cache existing Skills to prevent duplicates
        existing_skills = {s.name: s.id for s in session.query(Skill).all()}
        all_skills_in_csv = set()
        for s_str in df["skills_required_clean"].dropna():
            for s in str(s_str).split(","):
                clean = s.strip()
                if clean:
                    all_skills_in_csv.add(clean)

        new_skills = [
            Skill(name=skill)
            for skill in all_skills_in_csv
            if skill not in existing_skills
        ]
        if new_skills:
            session.add_all(new_skills)
            session.flush()
            existing_skills = {s.name: s.id for s in session.query(Skill).all()}
        print(f"Skills synced: {len(existing_skills)} unique skills in database.")

        # 5. Cache existing Job IDs to prevent duplicate insertion
        existing_job_ids = {row[0] for row in session.query(JobPosting.job_id).all()}
        print(f"Existing job postings in database: {len(existing_job_ids):,}.")

        # 6. Process and Insert Job Postings and JobSkills in batches
        jobs_to_insert: List[JobPosting] = []
        job_skills_mapping: List[Tuple[str, Set[str]]] = []  # (job_id, set of skill names)
        skipped_count = 0

        for _, row in df.iterrows():
            jid = str(row["job_id"]).strip()
            if jid in existing_job_ids:
                skipped_count += 1
                continue

            raw_title = str(row["job_title"]).strip()
            clean_role = (
                ROLE_NORMALIZATION_MAP.get(raw_title.lower())
                or raw_title.title()
            )

            comp_name = str(row.get("company_name", "")).strip()
            comp_id = existing_companies.get(comp_name)

            # Safe numeric conversion
            exp_yrs = float(row["experience_years"]) if pd.notna(row.get("experience_years")) else None
            sal_min = float(row["salary_min_lpa"]) if pd.notna(row.get("salary_min_lpa")) else None
            sal_max = float(row["salary_max_lpa"]) if pd.notna(row.get("salary_max_lpa")) else None
            sal_mid = float(row["salary_mid_lpa"]) if pd.notna(row.get("salary_mid_lpa")) else None
            sal_inr = int(row["salary_annual_inr"]) if pd.notna(row.get("salary_annual_inr")) else None
            p_year = int(row["posted_year"]) if pd.notna(row.get("posted_year")) else None
            p_month = int(row["posted_month"]) if pd.notna(row.get("posted_month")) else None

            job_obj = JobPosting(
                job_id=jid,
                job_title=raw_title,
                clean_role=clean_role,
                company_id=comp_id,
                city=str(row.get("city", "")).strip() or None,
                state=str(row.get("state", "")).strip() or None,
                experience_level=str(row.get("experience_level", "")).strip() or None,
                experience_years=exp_yrs,
                education=str(row.get("education", "")).strip() or None,
                employment_type=str(row.get("employment_type", "")).strip() or None,
                work_mode=str(row.get("work_mode", "")).strip() or None,
                salary_min_lpa=sal_min,
                salary_max_lpa=sal_max,
                salary_mid_lpa=sal_mid,
                salary_annual_inr=sal_inr,
                is_salary_valid=bool(row.get("is_salary_valid", False)),
                company_size=str(row.get("company_size", "")).strip() or None,
                industry=str(row.get("industry", "")).strip() or None,
                posted_date=str(row.get("posted_date", "")).strip() or None,
                posted_year=p_year,
                posted_month=p_month,
            )
            jobs_to_insert.append(job_obj)

            # Unique skills per posting
            skills_str = str(row.get("skills_required_clean", ""))
            unique_posting_skills = set(s.strip() for s in skills_str.split(",") if s.strip())
            job_skills_mapping.append((jid, unique_posting_skills))

            # Flush in batches
            if len(jobs_to_insert) >= batch_size:
                session.add_all(jobs_to_insert)
                session.flush()
                jobs_to_insert.clear()

        # Flush remaining
        if jobs_to_insert:
            session.add_all(jobs_to_insert)
            session.flush()
            jobs_to_insert.clear()

        # 7. Map JobSkills with newly generated primary keys
        db_job_lookup = {
            jp.job_id: jp.id
            for jp in session.query(JobPosting.job_id, JobPosting.id).all()
        }

        # Cache existing JobSkill pairs to prevent duplicate key errors
        existing_job_skills = {
            (js.job_posting_id, js.skill_id)
            for js in session.query(JobSkill.job_posting_id, JobSkill.skill_id).all()
        }

        job_skill_objects: List[JobSkill] = []
        for jid, skill_set in job_skills_mapping:
            db_pk = db_job_lookup.get(jid)
            if not db_pk:
                continue
            for skill_name in skill_set:
                skill_id = existing_skills.get(skill_name)
                if skill_id and (db_pk, skill_id) not in existing_job_skills:
                    job_skill_objects.append(
                        JobSkill(job_posting_id=db_pk, skill_id=skill_id)
                    )
                    existing_job_skills.add((db_pk, skill_id))

                    if len(job_skill_objects) >= batch_size * 2:
                        session.add_all(job_skill_objects)
                        session.flush()
                        job_skill_objects.clear()

        if job_skill_objects:
            session.add_all(job_skill_objects)
            session.flush()
            job_skill_objects.clear()

    elapsed = round(time.time() - start_time, 2)
    final_postings_count = total_rows - skipped_count
    print(f"Import completed in {elapsed}s: {final_postings_count:,} inserted, {skipped_count:,} skipped duplicates.")

    return {
        "status": "SUCCESS",
        "total_rows_processed": total_rows,
        "new_postings_inserted": final_postings_count,
        "skipped_duplicate_postings": skipped_count,
        "total_companies": len(existing_companies),
        "total_skills": len(existing_skills),
        "duration_seconds": elapsed,
    }


if __name__ == "__main__":
    print(f"Target Database URL: {get_database_url()}")
    conn_ok, msg = check_db_connection()
    if not conn_ok:
        print(f"Connection check note: {msg}")
        print("Using local SQLite database for ingestion...")
        sqlite_url = "sqlite:///./data/job_market.db"
        eng = get_engine(sqlite_url)
    else:
        eng = get_engine()

    res = import_job_market_data(engine=eng)
    print("Ingestion Summary:", res)
