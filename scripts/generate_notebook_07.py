"""
Script to generate notebooks/07_skill_gap_analysis.ipynb
"""

import json
import os

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# AI-Powered Job Market Intelligence & Salary Prediction System\n",
                "## Step 7: Skill Gap Analysis & Recommendation Engine (Module 4)\n",
                "\n",
                "**Target Notebook:** `notebooks/07_skill_gap_analysis.ipynb`  \n",
                "**Core Module:** `src/skill_analyzer.py`  \n",
                "**Input Dataset:** `data/processed/cleaned_job_market_all.csv` (30,250 verified job postings)  \n",
                "\n",
                "### Objectives & Analytical Methodology:\n",
                "1. **Empirical Job Market Demand Profiling:** Calculate overall technical skill demand, frequencies, and percentages across 30,250 job postings without double-counting duplicate skills within the same posting.\n",
                "2. **Dynamic Job Role Benchmarking:** Filter and aggregate skill requirements dynamically across the 12 canonical tech job roles (e.g. Data Scientist, Cloud Engineer, Software Engineer).\n",
                "3. **Skill Prioritization Tiers:** Categorize role requirements into project-defined demand thresholds:\n",
                "   - **Essential Skills:** Demand $\\ge 50\\%$\n",
                "   - **Important Skills:** Demand $\\ge 25\\%$ and $< 50\\%$\n",
                "   - **Additional Skills:** Demand $< 25\\%$\n",
                "4. **Demand-Weighted Skill Match Scoring:** Formulate an intelligent, transparent match score weighted by market demand:\n",
                "   $$\\text{Skill Match Score} = \\left( \\frac{\\sum_{s \\in \\text{Matched}} \\text{Demand}(s)}{\\sum_{s \\in \\text{Required}} \\text{Demand}(s)} \\right) \\times 100$$\n",
                "5. **Personalized Learning Pathways:** Diagnose missing skills, prioritize essential gaps, and generate actionable learning recommendations and project practice assignments."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 1. Environment Setup & Library Imports\n",
                "import os\n",
                "import sys\n",
                "import json\n",
                "import warnings\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "\n",
                "# Add project root to sys.path\n",
                "project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))\n",
                "if project_root not in sys.path:\n",
                "    sys.path.insert(0, project_root)\n",
                "\n",
                "from src.skill_analyzer import (\n",
                "    SkillGapAnalyzer,\n",
                "    get_available_job_roles,\n",
                "    analyze_market_skill_demand,\n",
                "    get_role_required_skills,\n",
                "    compare_candidate_skills,\n",
                "    calculate_skill_match_score,\n",
                "    generate_learning_recommendations,\n",
                "    generate_skill_gap_report,\n",
                "    get_dataset,\n",
                ")\n",
                "from src.resume_parser import extract_skills_from_text\n",
                "\n",
                "warnings.filterwarnings('ignore')\n",
                "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n",
                "pd.set_option('display.max_columns', None)\n",
                "\n",
                "print('Skill Gap Analysis module imported successfully.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Loading Cleaned Job Market Dataset\n",
                "Ingesting `data/processed/cleaned_job_market_all.csv` and inspecting available canonical job roles."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "df = get_dataset()\n",
                "available_roles = get_available_job_roles(df)\n",
                "\n",
                "print(f'Total Job Postings Loaded: {len(df):,}')\n",
                "print(f'Total Distinct Canonical Tech Roles: {len(available_roles)}')\n",
                "print('Available Job Roles:')\n",
                "for i, role in enumerate(available_roles, 1):\n",
                "    postings_count = len(df[df['clean_role'] == role])\n",
                "    print(f'  {i:2d}. {role:<26} ({postings_count:,} postings)')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. Overall Market Skill Demand Analysis\n",
                "Aggregating skill frequencies across all 30,250 job postings without double-counting duplicate skills within the same posting."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "overall_demand = analyze_market_skill_demand(df, top_n=20)\n",
                "print('Top 10 Most Demanded Technical Skills in Indian Tech Market:')\n",
                "overall_demand.head(10)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 4. Visualizing Top 20 In-Demand Skills\n",
                "Generating and saving Figure `reports/figures/market_skill_demand_top20.png`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, ax = plt.subplots(figsize=(11, 8), dpi=300)\n",
                "top20 = overall_demand.head(20).sort_values(by='demand_percentage', ascending=True)\n",
                "colors = plt.cm.Blues(np.linspace(0.4, 0.95, len(top20)))\n",
                "bars = ax.barh(top20['skill'], top20['demand_percentage'], color=colors, height=0.68)\n",
                "\n",
                "ax.set_xlabel('Market Demand Percentage (%)', fontsize=12)\n",
                "ax.set_title('Top 20 Technical Skills Demanded Across 30,250 Tech Postings', fontsize=14, fontweight='bold', pad=12)\n",
                "for bar in bars:\n",
                "    w = bar.get_width()\n",
                "    ax.text(w + 0.35, bar.get_y() + bar.get_height()/2, f'{w:.1f}%', va='center', fontsize=9, fontweight='bold', color='#1E3A8A')\n",
                "ax.set_xlim(0, max(top20['demand_percentage']) * 1.12)\n",
                "plt.tight_layout()\n",
                "\n",
                "figures_dir = os.path.join('..', 'reports', 'figures') if os.path.exists(os.path.join('..', 'reports', 'figures')) else os.path.join('reports', 'figures')\n",
                "os.makedirs(figures_dir, exist_ok=True)\n",
                "fig.savefig(os.path.join(figures_dir, 'market_skill_demand_top20.png'))\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 5. Role-Specific Skill Requirements Analysis\n",
                "Examining skill distributions for target roles (e.g. Data Scientist, Cloud Engineer, Software Engineer) categorized into Essential ($\\ge 50\\%$), Important ($25\\% - 50\\%$), and Additional ($< 25\\%$)."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "target_role = 'Data Scientist'\n",
                "role_skills = get_role_required_skills(target_role, df=df)\n",
                "role_skills_df = pd.DataFrame(role_skills)\n",
                "\n",
                "print(f'=== Skill Requirements for {target_role} (N = {len(df[df[\"clean_role\"] == target_role]):,}) ===')\n",
                "print(f'Total Skills Observed: {len(role_skills_df)}')\n",
                "print(f'Essential Skills (>= 50%): {role_skills_df[role_skills_df[\"category\"] == \"Essential\"][\"skill\"].tolist()}')\n",
                "print(f'Important Skills (25-50%): {role_skills_df[role_skills_df[\"category\"] == \"Important\"][\"skill\"].tolist()}')\n",
                "print('\\nTop 12 Skills Breakdown:')\n",
                "role_skills_df.head(12)"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 6. Candidate Skill Extraction from Resume\n",
                "Extracting candidate skills from a realistic candidate resume text using Module 3's `extract_skills_from_text`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "candidate_resume_text = '''\n",
                "Vikram Malhotra\n",
                "Bengaluru, India | vikram.sample@example.com\n",
                "\n",
                "PROFESSIONAL SUMMARY\n",
                "Data Analyst with 3 years of experience specializing in SQL querying, Python scripting, and business reporting.\n",
                "\n",
                "TECHNICAL SKILLS\n",
                "Languages: Python, SQL\n",
                "Libraries & Tools: Pandas, NumPy, Excel, Power BI, Git\n",
                "\n",
                "WORK EXPERIENCE\n",
                "Analytics Specialist | Retail Dynamics (2021 - Present)\n",
                "- Automated weekly executive KPI dashboards using Power BI and Excel.\n",
                "- Built data extraction scripts in Python and optimized SQL queries on PostgreSQL.\n",
                "'''\n",
                "\n",
                "candidate_skills = extract_skills_from_text(candidate_resume_text)\n",
                "print(f'Extracted Candidate Skills ({len(candidate_skills)}): {candidate_skills}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 7. Candidate Skill Comparison & Demand-Weighted Match Scoring\n",
                "Evaluating the candidate's skills against the target role requirements using demand-weighted scoring."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "comparison = compare_candidate_skills(candidate_skills, target_role, df=df)\n",
                "match_score = calculate_skill_match_score(candidate_skills, target_role, df=df)\n",
                "\n",
                "print(f'Target Role: {target_role}')\n",
                "print(f'Demand-Weighted Skill Match Score: {match_score:.2f}%')\n",
                "print(f'Matched Skills ({len(comparison[\"matched_skills\"])}): {comparison[\"matched_skills\"]}')\n",
                "print(f'Missing Essential Skills ({len(comparison[\"missing_essential_skills\"])}): {comparison[\"missing_essential_skills\"]}')\n",
                "print(f'Missing Important Skills ({len(comparison[\"missing_important_skills\"])}): {comparison[\"missing_important_skills\"]}')\n",
                "print(f'Missing Additional Skills Count: {len(comparison[\"missing_additional_skills\"])}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 8. Prioritized Personalized Learning Recommendations\n",
                "Generating prioritized learning actions and project practice recommendations for missing skills."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "recommendations = generate_learning_recommendations(candidate_skills, target_role, df=df)\n",
                "recs_df = pd.DataFrame(recommendations)\n",
                "\n",
                "print(f'=== Personalized Learning Pathways for {target_role} ===\\n')\n",
                "for idx, row in recs_df.head(6).iterrows():\n",
                "    print(f'[{row[\"priority\"].upper()}] Skill: {row[\"skill\"]} (Market Demand: {row[\"demand_percentage\"]:.1f}%)')\n",
                "    print(f'  Learning Action:  {row[\"suggested_learning_action\"]}')\n",
                "    print(f'  Project Practice: {row[\"suggested_project_practice\"]}\\n')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 9. Visualizing Matched vs. Missing Skills\n",
                "Generating a visual diagnostic chart comparing the candidate's matched skills versus missing skills ordered by market demand."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Visualize top 15 role skills with Matched/Missing status\n",
                "top15_role_skills = role_skills_df.head(15).copy()\n",
                "top15_role_skills['status'] = top15_role_skills['skill'].apply(\n",
                "    lambda s: 'Matched' if s in candidate_skills else 'Missing Gap'\n",
                ")\n",
                "top15_role_skills = top15_role_skills.sort_values(by='demand_percentage', ascending=True)\n",
                "\n",
                "fig, ax = plt.subplots(figsize=(10, 7), dpi=300)\n",
                "colors = ['#10B981' if st == 'Matched' else '#EF4444' for st in top15_role_skills['status']]\n",
                "bars = ax.barh(top15_role_skills['skill'], top15_role_skills['demand_percentage'], color=colors, height=0.68)\n",
                "\n",
                "ax.set_xlabel('Skill Demand in Role (%)', fontsize=12)\n",
                "ax.set_title(f'Skill Gap Diagnostic: {target_role} (Score: {match_score:.1f}%)', fontsize=14, fontweight='bold', pad=12)\n",
                "\n",
                "# Legend\n",
                "from matplotlib.patches import Patch\n",
                "legend_elements = [\n",
                "    Patch(facecolor='#10B981', label=f'Matched Skills ({len(comparison[\"matched_skills\"])})'),\n",
                "    Patch(facecolor='#EF4444', label=f'Missing Gaps ({len(comparison[\"missing_skills\"])})')\n",
                "]\n",
                "ax.legend(handles=legend_elements, loc='lower right', frameon=True, facecolor='white')\n",
                "\n",
                "for bar in bars:\n",
                "    w = bar.get_width()\n",
                "    ax.text(w + 0.8, bar.get_y() + bar.get_height()/2, f'{w:.1f}%', va='center', fontsize=9, fontweight='bold', color='#1E3A8A')\n",
                "\n",
                "ax.set_xlim(0, max(top15_role_skills['demand_percentage']) * 1.15)\n",
                "plt.tight_layout()\n",
                "fig.savefig(os.path.join(figures_dir, 'skill_gap_match_comparison.png'))\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 10. Complete Structured Skill Gap Report Generation\n",
                "Executing `generate_skill_gap_report` to generate the complete JSON report."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "complete_report = generate_skill_gap_report(\n",
                "    candidate_skills=candidate_skills,\n",
                "    job_role=target_role,\n",
                "    df=df\n",
                ")\n",
                "\n",
                "print('=== Complete Structured Skill Gap Report ===')\n",
                "summary_keys = [\n",
                "    'job_role', 'skill_match_score', 'total_required_skills',\n",
                "    'matched_skills', 'missing_essential_skills',\n",
                "    'essential_match_count', 'essential_missing_count'\n",
                "]\n",
                "for k in summary_keys:\n",
                "    print(f'  {k}: {complete_report[k]}')\n",
                "\n",
                "print(f'\\nTotal Learning Recommendations Generated: {len(complete_report[\"learning_recommendations\"])}')\n",
                "print(f'Warnings: {complete_report[\"analysis_warnings\"]}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 11. Findings & Governance Notes\n",
                "\n",
                "1. **Demand-Weighted Match Accuracy:** Weighting skills by market demand percentage ensures that missing core requirements (e.g. `Machine Learning` for Data Scientist at $71.5\\%$) appropriately impacts the match score more than niche secondary tools ($16\\%$).\n",
                "2. **Dynamic Role Sourcing:** Roles and requirements are queried dynamically from the 30,250 job posting dataset rather than being static or hardcoded.\n",
                "3. **Ethical Responsible AI Statement:** The skill match score reflects alignment with technical requirements in historical job postings. It does not represent an employability guarantee, candidate quality rating, or predictive hiring probability."
            ]
        }
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

notebook_path = os.path.join("notebooks", "07_skill_gap_analysis.ipynb")
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print(f"Generated {notebook_path} with {len(notebook['cells'])} cells.")

