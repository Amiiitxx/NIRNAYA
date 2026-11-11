import sys
import os
sys.path.insert(0, os.path.abspath("."))

import src.job_market_intelligence as jmi
import src.salary_model as sm
import src.resume_parser as rp
import src.skill_analyzer as sa
import database.db as db

print("=== JOB MARKET INTELLIGENCE ===")
for name in dir(jmi):
    if not name.startswith("_"):
        print(f"  {name}")

print("\n=== SALARY MODEL ===")
for name in dir(sm):
    if not name.startswith("_"):
        print(f"  {name}")

print("\n=== RESUME PARSER ===")
for name in dir(rp):
    if not name.startswith("_"):
        print(f"  {name}")

print("\n=== SKILL ANALYZER ===")
for name in dir(sa):
    if not name.startswith("_"):
        print(f"  {name}")

print("\n=== DATABASE ===")
for name in dir(db):
    if not name.startswith("_"):
        print(f"  {name}")
