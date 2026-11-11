"""
Comprehensive End-to-End Integration Verification Script for Workflows A, B, C, D, and E.
"""
import sys
import os
import fitz
import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("."))

from src.job_market_intelligence import (
    get_market_overview,
    get_job_role_analytics,
    get_city_analytics,
    get_skill_intelligence,
    get_salary_analytics,
)
from src.salary_model import predict_salary, SalaryPredictor
from src.resume_parser import parse_resume
from src.skill_analyzer import generate_skill_gap_report, get_available_job_roles
from database.db import check_db_connection, get_db_session, JobPosting, Company, Skill
from api.main import app

print("==================================================")
print("TESTING WORKFLOW A: JOB MARKET INTELLIGENCE")
print("==================================================")
overview = get_market_overview()
role_stats = get_job_role_analytics()
city_stats = get_city_analytics()
skill_stats = get_skill_intelligence()
salary_stats = get_salary_analytics()

print(f"  Total Postings: {overview['total_job_postings']:,}")
print(f"  Total Unique Companies: {overview['total_unique_companies']}")
print(f"  Top In-Demand Role: {role_stats['top_roles'][0]['role']} ({role_stats['top_roles'][0]['job_count']} postings)")
print(f"  Top Hiring City: {city_stats['top_cities'][0]['city']} ({city_stats['top_cities'][0]['job_count']} postings)")
print(f"  Top Technical Skill: {skill_stats['top_skills'][0]['skill']} ({skill_stats['top_skills'][0]['demand_percentage']}%)")
print(f"  Verified Salary Median: ₹{salary_stats['salary_range_analysis']['median_lpa']:.2f} LPA")
assert overview['total_job_postings'] == 30250
print("  Workflow A: PASSED")

print("\n==================================================")
print("TESTING WORKFLOW B: SALARY PREDICTION")
print("==================================================")
predictor = SalaryPredictor()
candidate = {
    "job_title": "Data Scientist",
    "experience_years": 5.0,
    "city": "Bengaluru",
    "state": "Karnataka",
    "skills": ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn"],
    "education": "Master's",
    "work_mode": "Hybrid",
    "company_size": "Large (1000+)",
    "industry": "Technology",
    "employment_type": "Full-time",
}
sal_res = predictor.predict(**candidate)
print(f"  Candidate: {candidate['job_title']} ({candidate['experience_years']} yrs exp, {candidate['city']})")
print(f"  Predicted Benchmark: ₹{sal_res['predicted_salary_lpa']:.2f} LPA (₹{sal_res['predicted_salary_annual_inr']:,} / yr)")
print(f"  Confidence Interval: ₹{sal_res['lower_bound_lpa']:.2f} LPA – ₹{sal_res['upper_bound_lpa']:.2f} LPA")
assert sal_res['predicted_salary_lpa'] > 0
print("  Workflow B: PASSED")

print("\n==================================================")
print("TESTING WORKFLOW C: RESUME SKILL EXTRACTION")
print("==================================================")
# Build synthetic PDF in memory
doc = fitz.open()
p = doc.new_page()
p.insert_text(
    (50, 72),
    "Aarav Sharma - Machine Learning Engineer\n\n"
    "Summary:\nExperienced ML engineer building scalable models.\n\n"
    "Technical Skills:\nPython, PyTorch, Docker, Kubernetes, SQL, FastAPI, Machine Learning, Scikit-learn, Git\n\n"
    "Experience:\nSenior Engineer at Tech Corp deploying computer vision microservices.\n\n"
    "Education:\nBachelor of Technology in Computer Science.\n"
)
pdf_bytes = doc.tobytes()
doc.close()

resume_res = parse_resume(pdf_bytes, filename="aarav_sharma_resume.pdf")
print(f"  Extraction Status: {resume_res['extraction_status']}")
print(f"  Detected Skill Count: {resume_res['skill_count']}")
print(f"  Extracted Skills: {resume_res['extracted_skills']}")
print(f"  Segmented Sections: {list(resume_res['sections'].keys())}")
assert resume_res['extraction_status'] == "SUCCESS"
assert "Python" in resume_res['extracted_skills']
assert "PyTorch" in resume_res['extracted_skills']
print("  Workflow C: PASSED")

print("\n==================================================")
print("TESTING WORKFLOW D: SKILL GAP ANALYSIS")
print("==================================================")
# Transfer extracted skills from Workflow C to target role
extracted_skills = resume_res['extracted_skills']
target_role = "Machine Learning Engineer"

gap_report = generate_skill_gap_report(
    candidate_skills=extracted_skills,
    job_role=target_role,
)
print(f"  Target Role: {gap_report['job_role']}")
print(f"  Demand-Weighted Match Score: {gap_report['skill_match_score']}%")
print(f"  Matched Skills ({len(gap_report['matched_skills'])}): {gap_report['matched_skills']}")
print(f"  Missing Essential ({len(gap_report['missing_essential_skills'])}): {gap_report['missing_essential_skills']}")
print(f"  Missing Important ({len(gap_report['missing_important_skills'])}): {gap_report['missing_important_skills']}")
print(f"  Missing Additional ({len(gap_report['missing_additional_skills'])}): {gap_report['missing_additional_skills']}")
print(f"  Learning Recommendations Generated: {len(gap_report['learning_recommendations'])}")
if gap_report['learning_recommendations']:
    rec = gap_report['learning_recommendations'][0]
    print(f"    Top Priority Recommendation: {rec['skill']} ({rec['priority']}) -> {rec['suggested_learning_action']}")
assert 0.0 <= gap_report['skill_match_score'] <= 100.0
print("  Workflow D: PASSED")

print("\n==================================================")
print("TESTING WORKFLOW E: DATABASE & REST API")
print("==================================================")
conn_ok, conn_msg = check_db_connection()
print(f"  Database Connection: {'CONNECTED' if conn_ok else 'DISCONNECTED'} ({conn_msg})")

with get_db_session() as session:
    total_db_postings = session.query(JobPosting).count()
    total_db_companies = session.query(Company).count()
    total_db_skills = session.query(Skill).count()
    print(f"  Database Postings Count: {total_db_postings:,}")
    print(f"  Database Companies Count: {total_db_companies}")
    print(f"  Database Skills Count: {total_db_skills}")
assert total_db_postings == 30250

client = TestClient(app)
r_health = client.get("/health")
print(f"  GET /health: {r_health.status_code} - {r_health.json()['status']}")
assert r_health.status_code == 200

r_overview = client.get("/api/market/overview")
print(f"  GET /api/market/overview: {r_overview.status_code} - Total Postings: {r_overview.json()['total_job_postings']:,}")
assert r_overview.status_code == 200

r_roles = client.get("/api/market/job-roles?limit=5")
print(f"  GET /api/market/job-roles: {r_roles.status_code} - Top Role: {r_roles.json()['top_roles'][0]['role']}")
assert r_roles.status_code == 200

r_dossier = client.get("/api/market/role/Data%20Scientist")
print(f"  GET /api/market/role/Data Scientist: {r_dossier.status_code} - Median Salary: ₹{r_dossier.json()['salary_stats']['median_lpa']} LPA")
assert r_dossier.status_code == 200
print("  Workflow E: PASSED")

print("\n==================================================")
print("ALL 5 END-TO-END WORKFLOWS COMPLETED SUCCESSFULLY!")
print("==================================================")
