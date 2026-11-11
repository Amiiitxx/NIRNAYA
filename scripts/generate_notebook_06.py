"""
Script to generate notebooks/06_resume_skill_extraction.ipynb
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
                "## Step 6: Resume Skill Extraction & Parsing Engine (Module 3)\n",
                "\n",
                "**Target Notebook:** `notebooks/06_resume_skill_extraction.ipynb`  \n",
                "**Core Module:** `src/resume_parser.py`  \n",
                "**Underlying Engine:** PyMuPDF (`fitz`), Regular Expressions, Curated Skill Taxonomy  \n",
                "\n",
                "### Objectives & Strict Engineering Governance:\n",
                "1. **Robust PDF Text Ingestion:** Parse multi-page PDF documents using PyMuPDF, preserving layout and line-breaks while gracefully handling scanned, empty, or corrupted files.\n",
                "2. **Scanned PDF Diagnostics:** Accurately detect image-only PDFs lacking selectable text layers and emit explicit warnings explaining that OCR is not supported.\n",
                "3. **Heuristic Section Segmentation:** Partition document content into canonical sections (`skills`, `experience`, `projects`, `education`, `certifications`) without hallucinating missing fields.\n",
                "4. **Curated Skill Taxonomy & Alias Normalization:** Match candidate skills against our canonical tech dictionary, standardizing variations (e.g., `py` $\\rightarrow$ Python, `k8s` $\\rightarrow$ Kubernetes, `sklearn` $\\rightarrow$ Scikit-learn) with strict word-boundary protection to eliminate false positives.\n",
                "5. **Zero Data Retention:** Process resume byte streams purely in memory without persistent storage, ensuring strict privacy and credential isolation."
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
                "import io\n",
                "import json\n",
                "import tempfile\n",
                "import warnings\n",
                "import numpy as np\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "\n",
                "try:\n",
                "    import pymupdf as fitz\n",
                "except ImportError:\n",
                "    import fitz\n",
                "\n",
                "# Add project root to sys.path\n",
                "project_root = os.path.abspath(os.path.join(os.getcwd(), '..'))\n",
                "if project_root not in sys.path:\n",
                "    sys.path.insert(0, project_root)\n",
                "\n",
                "from src.resume_parser import (\n",
                "    ResumeParser,\n",
                "    parse_resume,\n",
                "    extract_text_from_pdf,\n",
                "    extract_sections_from_text,\n",
                "    extract_skills_from_text,\n",
                "    CANONICAL_SKILL_PATTERNS\n",
                ")\n",
                "\n",
                "warnings.filterwarnings('ignore')\n",
                "plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')\n",
                "pd.set_option('display.max_columns', None)\n",
                "\n",
                "print(f'PyMuPDF Version: {fitz.__version__}')\n",
                "print(f'Total Curated Canonical Skills in Taxonomy: {len(CANONICAL_SKILL_PATTERNS)}')\n",
                "print('Resume Parser module imported successfully.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2. Creation of Synthetic Test Resumes\n",
                "To rigorously validate the parser without compromising private personal data, we synthesize four controlled test resumes covering diverse technical disciplines, seniorities, and edge cases:"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Create in-memory synthetic resumes\n",
                "test_resumes = {}\n",
                "\n",
                "# 1. Senior Data Scientist Resume (Multi-skill, Data & Cloud)\n",
                "doc1 = fitz.open()\n",
                "p1 = doc1.new_page()\n",
                "text_ds = '''\n",
                "Aditi Sharma\n",
                "Bengaluru, Karnataka | aditi.sharma.sample@example.com\n",
                "\n",
                "SUMMARY\n",
                "Senior Data Scientist with 5+ years of experience leading machine learning, deep learning, and predictive modeling initiatives.\n",
                "\n",
                "TECHNICAL SKILLS\n",
                "Programming Languages: Python, SQL, C++\n",
                "Machine Learning & AI: Scikit-learn, PyTorch, TensorFlow, NLP, Computer Vision, Statistics\n",
                "Cloud & DevOps: AWS, Docker, Kubernetes, Git, Linux\n",
                "Databases: PostgreSQL, Redis, MongoDB\n",
                "\n",
                "PROFESSIONAL EXPERIENCE\n",
                "Lead Data Scientist | FinTech Innovations (2022 - Present)\n",
                "- Architected real-time fraud detection pipelines using Python, PyTorch, and Kafka, decreasing fraudulent transactions by 32%.\n",
                "- Deployed scalable inference endpoints using FastAPI and Docker on AWS EKS.\n",
                "\n",
                "Senior Machine Learning Engineer | DataCorp India (2019 - 2022)\n",
                "- Engineered recommendation systems with Pandas, NumPy, and Scikit-learn on a 50M-record customer dataset.\n",
                "- Orchestrated automated retraining pipelines with Apache Airflow and PostgreSQL.\n",
                "\n",
                "PROJECTS\n",
                "AI Market Intelligence Platform\n",
                "- Built end-to-end salary forecasting models using XGBoost, FastAPI, and Streamlit.\n",
                "\n",
                "EDUCATION\n",
                "M.Tech in Artificial Intelligence - IISc Bengaluru (2017 - 2019)\n",
                "B.Tech in Computer Science - NIT Karnataka (2013 - 2017)\n",
                "\n",
                "CERTIFICATIONS\n",
                "AWS Certified Machine Learning - Specialty\n",
                "'''\n",
                "p1.insert_text((50, 60), text_ds.strip())\n",
                "test_resumes['Senior_Data_Scientist'] = doc1.tobytes()\n",
                "doc1.close()\n",
                "\n",
                "# 2. Full-Stack Cloud Developer Resume (Web, APIs, Cloud)\n",
                "doc2 = fitz.open()\n",
                "p2_1 = doc2.new_page()\n",
                "text_fs_1 = '''\n",
                "Rohan Verma\n",
                "Hyderabad, Telangana\n",
                "\n",
                "TECHNICAL SKILLS\n",
                "Languages: JavaScript, TypeScript, Python, Java, HTML/CSS\n",
                "Frameworks: React, Node.js, Django, FastAPI\n",
                "Databases: MySQL, PostgreSQL, Redis\n",
                "Cloud & Tools: GCP, Docker, Kubernetes, Git\n",
                "\n",
                "WORK EXPERIENCE\n",
                "Senior Full Stack Engineer | CloudTech Solutions (2021 - Present)\n",
                "- Developed microservices using Node.js and FastAPI with React single-page frontend.\n",
                "'''\n",
                "p2_1.insert_text((50, 60), text_fs_1.strip())\n",
                "p2_2 = doc2.new_page()\n",
                "text_fs_2 = '''\n",
                "PROJECTS\n",
                "Enterprise Resource Dashboard\n",
                "- Integrated React frontend with PostgreSQL and Redis cache.\n",
                "\n",
                "EDUCATION\n",
                "B.Tech in Information Technology - BITS Pilani (2017 - 2021)\n",
                "'''\n",
                "p2_2.insert_text((50, 60), text_fs_2.strip())\n",
                "test_resumes['FullStack_Cloud_Developer'] = doc2.tobytes()\n",
                "doc2.close()\n",
                "\n",
                "# 3. Fresher Business Intelligence Analyst Resume (BI, Analytics, SQL)\n",
                "doc3 = fitz.open()\n",
                "p3 = doc3.new_page()\n",
                "text_bi = '''\n",
                "Kavya Nair\n",
                "Pune, Maharashtra\n",
                "\n",
                "CORE COMPETENCIES\n",
                "Power BI, Tableau, Excel, SQL, Python, Statistics\n",
                "\n",
                "PROJECTS\n",
                "Sales Performance Analytics Dashboard\n",
                "- Designed interactive executive dashboards in Power BI and Excel.\n",
                "- Extracted and transformed retail sales records using SQL and Pandas.\n",
                "\n",
                "EDUCATION\n",
                "B.Sc in Statistics - Pune University (2020 - 2023)\n",
                "'''\n",
                "p3.insert_text((50, 60), text_bi.strip())\n",
                "test_resumes['Fresher_BI_Analyst'] = doc3.tobytes()\n",
                "doc3.close()\n",
                "\n",
                "# 4. Scanned / Image-Only PDF (Edge Case: No Text Layer)\n",
                "doc4 = fitz.open()\n",
                "doc4.new_page()  # Blank page mimicking an image scan without selectable text\n",
                "test_resumes['Scanned_Image_Resume'] = doc4.tobytes()\n",
                "doc4.close()\n",
                "\n",
                "print(f'Successfully generated {len(test_resumes)} synthetic test PDFs in memory.')"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 3. PDF Text Extraction & Error Handling\n",
                "Testing PyMuPDF text extraction across valid single-page, multi-page, and image-only documents."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "for resume_name, pdf_data in test_resumes.items():\n",
                "    extracted_text, page_count, warnings, status = extract_text_from_pdf(pdf_data)\n",
                "    print(f'=== Resume: {resume_name} ===')\n",
                "    print(f'  Status: {status} | Pages: {page_count} | Extracted Characters: {len(extracted_text)}')\n",
                "    if warnings:\n",
                "        print(f'  Warning: {warnings[0]}')\n",
                "    else:\n",
                "        print(f'  Snippet: {extracted_text[:120].replace(chr(10), \" \")}...')\n",
                "    print()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 4. Resume Section Segmentation\n",
                "Evaluating line-level section identification for Technical Skills, Experience, Projects, Education, and Certifications."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "ds_text, _, _, _ = extract_text_from_pdf(test_resumes['Senior_Data_Scientist'])\n",
                "sections = extract_sections_from_text(ds_text)\n",
                "\n",
                "print('=== Section Segmentation for Senior Data Scientist ===')\n",
                "for sec_name, content in sections.items():\n",
                "    line_count = len(content.splitlines()) if content else 0\n",
                "    preview = content.replace('\\n', ' ')[:90] if content else '[EMPTY / NOT FOUND]'\n",
                "    print(f'Section: {sec_name.upper():<15} | Lines: {line_count:<2} | Preview: {preview}...')\n"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 5. Technical Skill Extraction & Alias Normalization\n",
                "Demonstrating alias resolution (e.g., `py` $\\rightarrow$ Python, `k8s` $\\rightarrow$ Kubernetes) and verifying that substrings inside unrelated words do not trigger false matches."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Test Alias Mapping\n",
                "alias_test_text = 'Candidate with strong expertise in py, k8s, postgres, sklearn, powerbi, and dl pipelines.'\n",
                "detected_aliases = extract_skills_from_text(alias_test_text)\n",
                "print('=== Alias Resolution Test ===')\n",
                "print(f'Input Text: \"{alias_test_text}\"')\n",
                "print(f'Extracted Canonical Skills: {detected_aliases}')\n",
                "\n",
                "# Test False-Positive Protection\n",
                "adversarial_text = 'She is reacting positively to a table in the office while spying on an excellent cat going home.'\n",
                "false_matches = extract_skills_from_text(adversarial_text)\n",
                "print('\\n=== False-Positive Protection Test ===')\n",
                "print(f'Input Text: \"{adversarial_text}\"')\n",
                "print(f'Extracted Skills (Expected: None): {false_matches}')\n",
                "assert len(false_matches) == 0, 'False positive match detected!'"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 6. End-to-End Structured Resume Parsing\n",
                "Executing `parse_resume(...)` across all candidate resumes and inspecting the structured JSON output."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "parsed_records = []\n",
                "\n",
                "for resume_name, pdf_bytes in test_resumes.items():\n",
                "    res = parse_resume(pdf_bytes, filename=f'{resume_name}.pdf')\n",
                "    parsed_records.append({\n",
                "        'Resume Profile': resume_name.replace('_', ' '),\n",
                "        'Status': res['extraction_status'],\n",
                "        'Skills Count': res['skill_count'],\n",
                "        'Skills Extracted': ', '.join(res['extracted_skills']) if res['extracted_skills'] else '[None]',\n",
                "        'Sections Identified': ', '.join([k for k, v in res['sections'].items() if v]),\n",
                "        'Warning': res['warnings'][0] if res['warnings'] else '[None]'\n",
                "    })\n",
                "\n",
                "summary_df = pd.DataFrame(parsed_records)\n",
                "summary_df"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 7. Visualizing Skill Extraction Frequencies\n",
                "Visualizing the technical competencies detected across our test corpus."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# Aggregate skills across test profiles\n",
                "all_extracted_skills = []\n",
                "for name, pdf_bytes in test_resumes.items():\n",
                "    res = parse_resume(pdf_bytes)\n",
                "    all_extracted_skills.extend(res['extracted_skills'])\n",
                "\n",
                "skill_series = pd.Series(all_extracted_skills).value_counts().sort_values(ascending=True)\n",
                "\n",
                "# Plot skill distribution\n",
                "fig, ax = plt.subplots(figsize=(10, 7), dpi=300)\n",
                "colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(skill_series)))\n",
                "bars = ax.barh(skill_series.index, skill_series.values, color=colors, height=0.65)\n",
                "ax.set_xlabel('Skill Frequency Across Test Resumes', fontsize=12)\n",
                "ax.set_title('Extracted Technical Competencies Across Evaluated Resumes', fontsize=14, fontweight='bold', pad=12)\n",
                "for bar in bars:\n",
                "    w = bar.get_width()\n",
                "    ax.text(w + 0.05, bar.get_y() + bar.get_height()/2, f'{int(w)}', va='center', fontsize=10, fontweight='bold', color='#1E3A8A')\n",
                "ax.set_xlim(0, max(skill_series.values) + 0.5)\n",
                "plt.tight_layout()\n",
                "\n",
                "figures_dir = os.path.join('..', 'reports', 'figures') if os.path.exists(os.path.join('..', 'reports', 'figures')) else os.path.join('reports', 'figures')\n",
                "os.makedirs(figures_dir, exist_ok=True)\n",
                "fig.savefig(os.path.join(figures_dir, 'resume_skill_extraction_counts.png'))\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 8. Findings, Governance & System Limitations\n",
                "\n",
                "#### Architectural Strengths:\n",
                "1. **High Throughput & Zero Disk Footprint:** By parsing directly from byte streams in-memory via PyMuPDF, the engine eliminates intermediate disk I/O and adheres to privacy-by-design.\n",
                "2. **Strict Disambiguation:** Precision regex rules prevent partial substring overlaps (e.g. `Java` vs `JavaScript`, `py` vs `spying`, `React` vs `reacting`).\n",
                "3. **Scanned PDF Resilience:** Rather than crashing or returning false positives, image-only PDFs trigger an explicit warning message informing the candidate that OCR is not supported.\n",
                "\n",
                "#### Known Limitations:\n",
                "- **Scanned Image Resumes:** PDFs consisting entirely of flattened raster images require Optical Character Recognition (OCR, e.g. Tesseract), which is intentionally excluded to preserve lightweight backend execution.\n",
                "- **Multi-Column Formatting:** In multi-column or tabular layouts, standard line-by-line reading orders can occasionally interleave text between adjacent columns. PyMuPDF text blocks mitigate this, but complex graphic-heavy templates may require layout-aware block sorting."
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

notebook_path = os.path.join("notebooks", "06_resume_skill_extraction.ipynb")
with open(notebook_path, "w", encoding="utf-8") as f:
    json.dump(notebook, f, indent=1)

print(f"Generated {notebook_path} with {len(notebook['cells'])} cells.")

