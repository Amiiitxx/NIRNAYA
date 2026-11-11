"""
Inspect empirical role skill profiles from data/processed/cleaned_job_market_all.csv
"""

import os
import json
import pandas as pd
from collections import Counter

DATA_PATH = "data/processed/cleaned_job_market_all.csv"
df = pd.read_csv(DATA_PATH)

role_map = {
    'data scientist': 'Data Scientist',
    'nlp engineer': 'NLP Engineer',
    'ai engineer': 'AI Engineer',
}
df['clean_role'] = df['job_title'].replace(role_map).str.strip()

role_profiles = {}
all_roles = sorted(df['clean_role'].unique())

for role in all_roles:
    sub = df[df['clean_role'] == role]
    total_jobs = len(sub)
    skill_counts = Counter()
    for s_str in sub['skills_required_clean'].dropna():
        for s in str(s_str).split(','):
            skill = s.strip()
            if skill:
                skill_counts[skill] += 1

    skills_data = []
    for skill, count in skill_counts.most_common():
        pct = round((count / total_jobs) * 100, 1)
        skills_data.append({
            'skill': skill,
            'job_count': count,
            'demand_percentage': pct
        })
    role_profiles[role] = {
        'total_postings': total_jobs,
        'skills': skills_data
    }

print(f"Computed profiles for {len(role_profiles)} canonical roles:")
for r, p in role_profiles.items():
    top3 = [f"{s['skill']} ({s['demand_percentage']}%)" for s in p['skills'][:3]]
    print(f"  {r} (N={p['total_postings']:,}): {', '.join(top3)}")

