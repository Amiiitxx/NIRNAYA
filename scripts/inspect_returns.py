import sys, os
sys.path.insert(0, os.path.abspath("."))

from src.salary_model import predict_salary, SalaryPredictor
from src.job_market_intelligence import get_market_overview, get_job_role_analytics
from src.skill_analyzer import generate_skill_gap_report, get_available_job_roles

predictor = SalaryPredictor()
sample_candidate = {
    "job_title": "Data Scientist",
    "city": "Bengaluru",
    "state": "Karnataka",
    "experience_level": "Mid-level",
    "experience_years": 4.5,
    "work_mode": "Hybrid",
    "employment_type": "Full-time",
    "education": "Bachelor's",
    "company_size": "Large (1000+)",
    "industry": "Technology",
    "skills": ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn"]
}
pred_res = predict_salary(sample_candidate, predictor=predictor)
print("Salary Prediction Result Keys:", list(pred_res.keys()))
print("Salary Prediction Result:", pred_res)

roles = get_available_job_roles()
print("Available Roles:", roles)

gap_res = generate_skill_gap_report(["Python", "SQL"], "Data Scientist")
print("Skill Gap Report Keys:", list(gap_res.keys()))
print("Skill Match Score:", gap_res.get("match_score"))

overview = get_market_overview()
print("Market Overview Keys:", list(overview.keys()))

