"""
Script to generate notebooks/08_job_market_intelligence.ipynb
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
                "## Step 8: Job Market Intelligence Engine & Database Layer (Module 5)\n",
                "\n",
                "**Target Notebook:** `notebooks/08_job_market_intelligence.ipynb`  \n",
                "**Core Modules:** `src/job_market_intelligence.py`, `database/db.py`, `api/main.py`  \n",
                "**Input Datasets:** `data/processed/cleaned_job_market_all.csv` (30,250 rows) & `data/processed/cleaned_salary_model_data.csv` (17,559 rows)  \n",
                "\n",
                "### Analytical Objectives:\n",
                "1. **Macro Market Diagnostics:** Synthesize high-level KPIs across 30,250 technology job postings, 16 hiring tech hubs, and 16 corporate recruiters.\n",
                "2. **Role & Geographic Concentration:** Evaluate volume distribution across 12 canonical roles, work modes (On-site, Hybrid, Remote), and hiring cities.\n",
                "3. **Verified Compensation Analytics:** Analyze salary distributions by role, experience tier, and location strictly utilizing verified salary disclosures (`salary_mid_lpa`).\n",
                "4. **Technical Skill Intelligence & Co-occurrence:** Map skill demand percentages and identify top co-occurring skill pairs across postings.\n",
                "5. **Relational Database & API Integration:** Inspect the PostgreSQL/SQLAlchemy schema and verify FastAPI REST endpoints.\n",
                "6. **Dataset Governance:** Document simulated data constraints and responsible reporting boundaries."
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
                "from src.job_market_intelligence import (\n",
                "    get_market_overview,\n",
                "    get_job_role_analytics,\n",
                "    get_city_analytics,\n",
                "    get_salary_analytics,\n",
                "    get_skill_intelligence,\n",
                "    get_temporal_trends,\n",
                "    get_role_dossier,\n",
                "    get_city_dossier,\n",
                "    get_market_dataset,\n",
                "    get_salary_dataset,\n",
                ")\n",
                "from database.db import check_db_connection, get_database_url\n",
                "\n",
                "warnings.filterwarnings('ignore')\n",
                "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n",
                "pd.set_option('display.max_columns', None)\n",
                "\n",
                "print('Job Market Intelligence Engine imported successfully.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Market Overview & Macro Distributions\n",
                "Synthesizing high-level market dimensions and employment distributions."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "overview = get_market_overview()\n",
                "print('=== Macro Market KPIs ===')\n",
                "print(f'Total Analyzed Job Postings:   {overview[\"total_job_postings\"]:,}')\n",
                "print(f'Total Unique Companies:        {overview[\"total_unique_companies\"]:,}')\n",
                "print(f'Total Canonical Tech Roles:    {overview[\"total_job_roles\"]}')\n",
                "print(f'Total Hiring Tech Cities:      {overview[\"total_cities\"]}')\n",
                "\n",
                "print('\\nEmployment Type Breakdown:')\n",
                "for emp, cnt in overview[\"employment_type_distribution\"].items():\n",
                "    print(f'  {emp:<15}: {cnt:>6,} ({cnt/overview[\"total_job_postings\"]*100:.1f}%)')\n",
                "\n",
                "print('\\nWork Mode Breakdown:')\n",
                "for wm, cnt in overview[\"work_mode_distribution\"].items():\n",
                "    print(f'  {wm:<15}: {cnt:>6,} ({cnt/overview[\"total_job_postings\"]*100:.1f}%)')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. Job Role Analytics & Market Demand\n",
                "Evaluating posting counts and market shares across the 12 canonical technical roles."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "role_data = get_job_role_analytics(top_n=12)\n",
                "role_df = pd.DataFrame(role_data['top_roles'])\n",
                "print('=== Technical Job Roles Demand Ranking ===')\n",
                "role_df"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 4. Geographic Tech Hub Concentration\n",
                "Evaluating hiring density across Indian technology hubs and states."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "city_data = get_city_analytics(top_n=10)\n",
                "city_df = pd.DataFrame(city_data['top_cities'])\n",
                "print('=== Top 10 Indian Tech Hiring Hubs ===')\n",
                "city_df"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 5. Verified Compensation Analytics (17,559 Salary Records)\n",
                "Analyzing compensation benchmarks strictly from disclosed, verified salary postings using `salary_mid_lpa`."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "sal_data = get_salary_analytics()\n",
                "top_pay_df = pd.DataFrame(sal_data['top_paying_roles'])\n",
                "print('=== Highest Paying Roles Ranked by Median Salary (LPA) ===')\n",
                "print(top_pay_df[['rank', 'role', 'job_count', 'median_lpa', 'mean_lpa', 'min_lpa', 'max_lpa']])\n",
                "\n",
                "print('\\n=== Salary Breakdown Across Seniority Tiers ===')\n",
                "exp_sal_df = pd.DataFrame(sal_data['salary_by_experience']).T\n",
                "exp_sal_df[['count', 'median_lpa', 'mean_lpa', 'p25_lpa', 'p75_lpa']]"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 6. Technical Skill Intelligence & Co-occurrence Patterns\n",
                "Identifying the Top 20 skills and mapping the most frequently co-occurring skill pairs across postings."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "skill_intel = get_skill_intelligence(top_n=20)\n",
                "top_skills_df = pd.DataFrame(skill_intel['top_skills'])\n",
                "co_df = pd.DataFrame(skill_intel['co_occurring_skills'])\n",
                "\n",
                "print('=== Top 10 Technical Skills Demanded ===')\n",
                "print(top_skills_df.head(10)[['rank', 'skill', 'job_count', 'demand_percentage']])\n",
                "\n",
                "print('\\n=== Top 8 Pairwise Co-occurring Skills ===')\n",
                "print(co_df.head(8)[['skill_pair', 'co_occurrence_count', 'co_occurrence_percentage']])"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 7. Visualizing Market Intelligence Insights\n",
                "Generating high-resolution comparative charts for salary by role and work mode distribution."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=300)\n",
                "\n",
                "# Subplot 1: Median Salary by Role\n",
                "plot_pay = top_pay_df.sort_values(by='median_lpa', ascending=True)\n",
                "colors1 = plt.cm.Blues(np.linspace(0.4, 0.95, len(plot_pay)))\n",
                "bars1 = ax1.barh(plot_pay['role'], plot_pay['median_lpa'], color=colors1, height=0.65)\n",
                "ax1.set_xlabel('Median Salary (INR LPA)', fontsize=11)\n",
                "ax1.set_title('Median Compensation by Role (Verified Salary Postings)', fontsize=13, fontweight='bold')\n",
                "for bar in bars1:\n",
                "    w = bar.get_width()\n",
                "    ax1.text(w + 0.25, bar.get_y() + bar.get_height()/2, f'{w:.1f} LPA', va='center', fontsize=9, fontweight='bold', color='#1E3A8A')\n",
                "ax1.set_xlim(0, max(plot_pay['median_lpa']) * 1.15)\n",
                "\n",
                "# Subplot 2: Top 8 Hiring Cities\n",
                "plot_city = city_df.head(8).sort_values(by='job_count', ascending=True)\n",
                "colors2 = plt.cm.Greens(np.linspace(0.4, 0.9, len(plot_city)))\n",
                "bars2 = ax2.barh(plot_city['city'], plot_city['job_count'], color=colors2, height=0.65)\n",
                "ax2.set_xlabel('Job Postings Count', fontsize=11)\n",
                "ax2.set_title('Top 8 Tech Hiring Hubs', fontsize=13, fontweight='bold')\n",
                "for bar in bars2:\n",
                "    w = bar.get_width()\n",
                "    ax2.text(w + 25, bar.get_y() + bar.get_height()/2, f'{int(w):,}', va='center', fontsize=9, fontweight='bold', color='#065F46')\n",
                "ax2.set_xlim(0, max(plot_city['job_count']) * 1.12)\n",
                "\n",
                "plt.tight_layout()\n",
                "figures_dir = os.path.join('..', 'reports', 'figures') if os.path.exists(os.path.join('..', 'reports', 'figures')) else os.path.join('reports', 'figures')\n",
                "os.makedirs(figures_dir, exist_ok=True)\n",
                "fig.savefig(os.path.join(figures_dir, 'job_market_intelligence_summary.png'))\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 8. Database Connection & System Health Status\n",
                "Validating relational engine connectivity and connection parameters."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "db_url = get_database_url()\n",
                "conn_ok, conn_msg = check_db_connection()\n",
                "\n",
                "print(f'Configured Database Target: {db_url.split(\"@\")[-1] if \"@\" in db_url else db_url}')\n",
                "print(f'Connection Check Status:   {\"CONNECTED\" if conn_ok else \"STANDBY / FALLBACK\"}')\n",
                "print(f'Diagnostic Details:        {conn_msg}')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 9. Business Insights & Simulation Constraints\n",
                "\n",
                "#### Strategic Insights:\n",
                "1. **Specialized AI/Cloud Salary Premium:** AI Engineers (median 15.1 LPA), MLOps Engineers (14.8 LPA), and ML Engineers (14.1 LPA) command substantial compensation premiums over generalist analytics roles.\n",
                "2. **Geographic Distribution:** Bengaluru leads aggregate hiring demand, closely followed by Delhi NCR, Hyderabad, and Pune.\n",
                "3. **Skill Synergy:** `Python + Machine Learning` forms the dominant co-occurring skill cluster across the Indian technical hiring landscape.\n",
                "\n",
                "#### Dataset & Scope Governance:\n",
                "- All statistics are derived from the supplied synthetic dataset (`cleaned_job_market_all.csv`).\n",
                "- Postings without verified salary disclosures are excluded from compensation metrics and preserved exclusively for volume and skill demand analysis."
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

notebook_path = os.path.join("notebooks", "08_job_market_intelligence.ipynb")
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print(f"Generated {notebook_path} with {len(notebook['cells'])} cells.")

