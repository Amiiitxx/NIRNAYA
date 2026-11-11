"""
Script to perform complete model verification and generate predictions for standard profiles.
"""
import sys
import os
import json
import joblib
import pandas as pd
import numpy as np

# Add project root
sys.path.insert(0, os.path.abspath("."))

from src.salary_model import SalaryPredictor, predict_salary

print("=== 1. VERIFYING ARTIFACTS EXISTENCE AND INTEGRITY ===")
artifacts = [
    "models/best_salary_model.joblib",
    "models/salary_prediction_pipeline.joblib",
    "models/model_metadata.json",
    "models/feature_pipeline.joblib",
    "models/feature_metadata.json",
    "models/model_comparison.csv",
    "models/feature_importance.csv"
]
for art in artifacts:
    exists = os.path.exists(art)
    size_kb = os.path.getsize(art) / 1024 if exists else 0
    print(f"  {art}: Exists={exists} ({size_kb:.1f} KB)")
    assert exists, f"Missing artifact: {art}"

print("\n=== 2. INSPECTING MODEL METADATA ===")
with open("models/model_metadata.json", "r") as f:
    meta = json.load(f)
for k, v in meta.items():
    print(f"  {k}: {v}")

print("\n=== 3. MODEL COMPARISON SUMMARY ===")
comp_df = pd.read_csv("models/model_comparison.csv")
print(comp_df.to_string(index=False))

print("\n=== 4. TESTING PREDICTOR INITIALIZATION & SAMPLE PROFILES ===")
predictor = SalaryPredictor()

profiles = [
    {
        "name": "Fresher Data Analyst",
        "inputs": {
            "job_title": "Data Analyst",
            "experience_years": 0.5,
            "city": "Bengaluru",
            "state": "Karnataka",
            "skills": ["SQL", "Excel", "Python"],
            "education": "Bachelor's",
            "work_mode": "On-site",
            "company_size": "Startup (1-50)",
            "industry": "IT Services",
            "employment_type": "Full-time",
        }
    },
    {
        "name": "Mid-level Data Scientist",
        "inputs": {
            "job_title": "Data Scientist",
            "experience_years": 4.5,
            "city": "Hyderabad",
            "state": "Telangana",
            "skills": ["Python", "Machine Learning", "SQL", "Pandas", "Scikit-learn"],
            "education": "Master's",
            "work_mode": "Hybrid",
            "company_size": "Mid-sized (201-500)",
            "industry": "Software Product",
            "employment_type": "Full-time",
        }
    },
    {
        "name": "Senior ML Engineer",
        "inputs": {
            "job_title": "Machine Learning Engineer",
            "experience_years": 8.5,
            "city": "Bengaluru",
            "state": "Karnataka",
            "skills": ["Python", "Machine Learning", "PyTorch", "Docker", "Kubernetes", "AWS", "FastAPI"],
            "education": "Master's",
            "work_mode": "Remote",
            "company_size": "Enterprise (1000+)",
            "industry": "Technology",
            "employment_type": "Full-time",
        }
    },
    {
        "name": "Edge Case: Unseen Categoricals & Extreme Values",
        "inputs": {
            "job_title": "Quantum Blockchain Architect",  # Unseen
            "experience_years": 45.0,  # Extreme
            "city": "CyberCity",  # Unseen
            "state": "Atlantis",  # Unseen
            "skills": ["ObscureLanguage", "MysticCode"],  # Unseen
            "education": "PhD in Quantum Magic",  # Unseen
            "work_mode": "Telepathic",  # Unseen
            "company_size": "OmniCorp (100k+)",  # Unseen
            "industry": "Interstellar",  # Unseen
            "employment_type": "Ephemeral",  # Unseen
        }
    }
]

for p in profiles:
    print(f"\n--- Running: {p['name']} ---")
    res = predictor.predict(**p["inputs"])
    print(f"  Predicted Point Estimate: ₹{res['predicted_salary_lpa']:.2f} LPA (₹{res['predicted_salary_annual_inr']:,} / yr)")
    print(f"  90% Confidence Interval: ₹{res['lower_bound_lpa']:.2f} LPA – ₹{res['upper_bound_lpa']:.2f} LPA")
    print(f"  Residual Std: ±₹{res['residual_std_lpa']:.2f} LPA")
    print(f"  Model: {res['model_name']} (v{res['model_version']})")

