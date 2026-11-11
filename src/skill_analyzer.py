"""
Module: Skill Analyzer
Description: Production-ready Job Market Skill Demand Analysis, Empirical Role
Benchmark Profiling, Demand-Weighted Skill Match Scoring, and Prioritized
Personalized Learning Recommendations.
"""

import json
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import pandas as pd

from src.resume_parser import extract_skills_from_text


# ---------------------------------------------------------
# CONSTANTS & CONFIGURATION
# ---------------------------------------------------------

DEFAULT_DATA_PATH = os.path.join("data", "processed", "cleaned_job_market_all.csv")

# Standard demand classification thresholds (project-defined defaults)
DEFAULT_ESSENTIAL_THRESHOLD: float = 50.0  # >= 50% demand within role
DEFAULT_IMPORTANT_THRESHOLD: float = 25.0  # >= 25% and < 50% demand within role

ROLE_NORMALIZATION_MAP: Dict[str, str] = {
    "ai engineer": "AI Engineer",
    "bi developer": "BI Developer",
    "business analyst": "Business Analyst",
    "cloud engineer": "Cloud Engineer",
    "data analyst": "Data Analyst",
    "data engineer": "Data Engineer",
    "data scientist": "Data Scientist",
    "mlops engineer": "MLOps Engineer",
    "machine learning engineer": "Machine Learning Engineer",
    "nlp engineer": "NLP Engineer",
    "python developer": "Python Developer",
    "software engineer": "Software Engineer",
}

# Curated actionable learning recommendations and project practice by skill
SKILL_LEARNING_GUIDANCE: Dict[str, Dict[str, str]] = {
    "Python": {
        "action": "Master Python 3 core fundamentals, generator pipelines, OOP principles, and type hints.",
        "project": "Build an end-to-end data pipeline or REST API microservice with pytest unit tests.",
    },
    "SQL": {
        "action": "Practice multi-table JOINs, subqueries, CTEs, and window functions (RANK, ROW_NUMBER, LAG/LEAD).",
        "project": "Design a normalized PostgreSQL schema and optimize complex queries using EXPLAIN ANALYZE.",
    },
    "Machine Learning": {
        "action": "Study supervised and unsupervised algorithms, cross-validation, and metric evaluation with Scikit-learn.",
        "project": "Build and tune an end-to-end regression/classification pipeline with cross-validated hyperparameter search.",
    },
    "Deep Learning": {
        "action": "Learn neural network fundamentals (MLPs, CNNs, Transformers), loss functions, and backpropagation.",
        "project": "Train and fine-tune an image classification or text sequence model using PyTorch or TensorFlow.",
    },
    "NLP": {
        "action": "Study text tokenization, embeddings (Word2Vec, BERT), sentiment analysis, and sequence-to-sequence models.",
        "project": "Build an NLP pipeline for resume classification or semantic document search using Hugging Face.",
    },
    "Computer Vision": {
        "action": "Master image filtering, convolutional neural networks, object detection (YOLO), and OpenCV.",
        "project": "Develop a real-time object detection or face recognition application with OpenCV and PyTorch.",
    },
    "AWS": {
        "action": "Study core AWS services: EC2, S3, Lambda, IAM policies, and VPC networking fundamentals.",
        "project": "Deploy a serverless data ingestion pipeline triggered by S3 uploads using AWS Lambda and CloudWatch.",
    },
    "Azure": {
        "action": "Learn Azure compute services, Azure Blob Storage, Azure SQL Database, and Azure DevOps pipelines.",
        "project": "Configure an automated CI/CD pipeline deploying an API container to Azure Container Instances.",
    },
    "GCP": {
        "action": "Learn Google Cloud Platform compute options, Cloud Run, Cloud Storage, and BigQuery data warehousing.",
        "project": "Build an analytics dashboard backed by partitioned BigQuery tables and deployed on Cloud Run.",
    },
    "Docker": {
        "action": "Master containerization, multi-stage Dockerfiles, image caching, and volume mapping.",
        "project": "Containerize a multi-service web application (FastAPI + PostgreSQL + Redis) using Docker Compose.",
    },
    "Kubernetes": {
        "action": "Understand pod architecture, deployments, services, ingress controllers, and horizontal pod autoscaling.",
        "project": "Deploy a containerized microservice onto a local Minikube cluster using declarative YAML manifests.",
    },
    "Git": {
        "action": "Master branching workflows, rebasing, merge conflict resolution, commit hygiene, and pull request reviews.",
        "project": "Maintain a modular GitHub repository with branch protection, semantic version tags, and GitHub Actions CI.",
    },
    "Linux": {
        "action": "Learn bash shell scripting, user permissions, process management (htop, systemd), and network diagnostics.",
        "project": "Write automated shell scripts for server backup, log rotation, and environment provisioning.",
    },
    "FastAPI": {
        "action": "Study asynchronous endpoint creation, Pydantic data validation schemas, dependency injection, and OpenAPI.",
        "project": "Build an asynchronous REST API serving ML predictions with request validation and rate limiting.",
    },
    "Flask": {
        "action": "Master Flask routing, blueprints, session management, and SQLAlchemy ORM database integration.",
        "project": "Develop a lightweight microservice with modular blueprints and comprehensive pytest test coverage.",
    },
    "Django": {
        "action": "Learn Django ORM, authentication system, class-based views, and Django REST Framework (DRF).",
        "project": "Create a full-featured web app with relational models, user authentication, and admin dashboard.",
    },
    "React": {
        "action": "Master React functional components, hooks (useState, useEffect, useMemo), and state management.",
        "project": "Build a responsive candidate analytics dashboard with interactive charts and REST API integration.",
    },
    "Node.js": {
        "action": "Learn asynchronous event-driven JavaScript/TypeScript, Express.js middleware, and RESTful routing.",
        "project": "Build an API backend with JWT authentication, rate limiting, and PostgreSQL integration.",
    },
    "Power BI": {
        "action": "Master Power Query data transformation, star-schema data modeling, and DAX calculated measures.",
        "project": "Create an executive corporate KPI dashboard with interactive drill-down filters and DAX time intelligence.",
    },
    "Tableau": {
        "action": "Learn calculated fields, level of detail (LOD) expressions, parameters, and dashboard storytelling.",
        "project": "Build a multi-worksheet business performance dashboard published to Tableau Public.",
    },
    "Excel": {
        "action": "Master advanced formulas (XLOOKUP, INDEX/MATCH), dynamic arrays, PivotTables, and Power Query.",
        "project": "Build an automated financial consolidation or sales tracking model with Pivot Charts.",
    },
    "Statistics": {
        "action": "Study probability distributions, hypothesis testing (t-tests, ANOVA, chi-square), p-values, and confidence intervals.",
        "project": "Conduct an end-to-end A/B test analysis calculating sample size, statistical significance, and effect size.",
    },
    "PyTorch": {
        "action": "Study PyTorch tensors, autograd, custom Dataset/DataLoader classes, and modular nn.Module architectures.",
        "project": "Implement a custom neural network from scratch with checkpoint saving and validation metrics logging.",
    },
    "TensorFlow": {
        "action": "Study Keras functional API, custom layers, tf.data input pipelines, and model deployment via TF-Lite/TF-Serving.",
        "project": "Train an end-to-end convolutional neural network with data augmentation and learning rate scheduling.",
    },
    "Scikit-learn": {
        "action": "Learn Scikit-learn Pipeline and ColumnTransformer construction, custom transformers, and hyperparameter tuning.",
        "project": "Construct a leak-free preprocessing and modeling pipeline with cross-validated grid search.",
    },
    "Pandas": {
        "action": "Master DataFrame indexing, vectorization, groupby aggregations, window operations, and method chaining.",
        "project": "Clean and reshape an unformatted raw transactional dataset into tidy analytics format.",
    },
    "NumPy": {
        "action": "Understand n-dimensional array broadcasting, vectorization, linear algebra routines, and random sampling.",
        "project": "Implement matrix operations and similarity metrics (cosine similarity, euclidean distance) using vectorization.",
    },
    "Airflow": {
        "action": "Learn DAG design patterns, task dependencies, operators, sensors, and scheduling best practices.",
        "project": "Build an automated ETL DAG extracting API data, transforming with Pandas, and loading into a data warehouse.",
    },
    "PostgreSQL": {
        "action": "Learn relational schema design, indexing strategies (B-Tree, GIN), JSONB data types, and transactions.",
        "project": "Design and tune a normalized multi-table database with foreign key constraints and view optimizations.",
    },
    "MySQL": {
        "action": "Study relational database modeling, indexing, query optimization, and transaction isolation levels.",
        "project": "Design a relational transactional database and optimize slow queries using execution plans.",
    },
    "MongoDB": {
        "action": "Learn document schema design, aggregation pipelines, indexing, and MongoDB Atlas configuration.",
        "project": "Build a NoSQL data store with aggregation pipelines for high-throughput product analytics.",
    },
    "Redis": {
        "action": "Study in-memory key-value data structures, caching patterns, pub/sub messaging, and TTL expiration.",
        "project": "Implement an API caching layer and session store using Redis with automatic TTL invalidation.",
    },
    "Spark": {
        "action": "Master PySpark DataFrame transformations, lazy evaluation, partitioning, and Spark SQL.",
        "project": "Process and aggregate large-scale multi-gigabyte log datasets using PySpark and save to Parquet.",
    },
    "Hadoop": {
        "action": "Understand distributed storage (HDFS), MapReduce paradigm, and the Hadoop ecosystem architecture.",
        "project": "Configure a local Hadoop/HDFS environment and run a distributed word count and log processing job.",
    },
    "Kafka": {
        "action": "Learn event streaming architecture, topics, partitions, producer-consumer groups, and offset management.",
        "project": "Build a real-time event streaming pipeline producing and consuming simulated IoT or market events.",
    },
    "dbt": {
        "action": "Learn analytics engineering with dbt: models, ref functions, testing, documentation, and materializations.",
        "project": "Build a modular dbt transformation project converting raw staging tables into dimension and fact models.",
    },
    "Snowflake": {
        "action": "Study cloud data warehouse architecture, virtual warehouses, clustering keys, and zero-copy cloning.",
        "project": "Build an analytics data mart in Snowflake with time-travel queries and role-based access controls.",
    },
    "BigQuery": {
        "action": "Learn BigQuery SQL, partitioned and clustered tables, pricing optimization, and nested/repeated fields.",
        "project": "Query and analyze a public multi-million row dataset in BigQuery using window functions and CTEs.",
    },
    "Java": {
        "action": "Master core Java, object-oriented design patterns, collections framework, and JVM memory basics.",
        "project": "Build a backend service using Spring Boot with REST controllers, JPA repository, and unit tests.",
    },
    "JavaScript": {
        "action": "Master modern ES6+ syntax, closures, promises, async/await, and DOM manipulation.",
        "project": "Build an interactive web application consuming asynchronous third-party REST APIs.",
    },
    "TypeScript": {
        "action": "Learn static typing, interfaces, union types, generics, and tsconfig compiler options.",
        "project": "Refactor a JavaScript API client or frontend component library into strict, type-safe TypeScript.",
    },
    "C++": {
        "action": "Master pointers, memory management, STL containers, templates, and modern C++ (C++17/20) features.",
        "project": "Implement high-performance data structures and algorithms with benchmarked memory profiling.",
    },
    "HTML/CSS": {
        "action": "Study semantic HTML5 markup, modern CSS layouts (Flexbox, CSS Grid), and responsive design principles.",
        "project": "Build a responsive, accessible landing page with dark/light theme switching using pure CSS.",
    },
}


# ---------------------------------------------------------
# DATA ACCESS & NORMALIZATION HELPERS
# ---------------------------------------------------------

_CACHED_DF: Optional[pd.DataFrame] = None


def get_dataset(data_path: Optional[str] = None) -> pd.DataFrame:
    """
    Loads and caches the cleaned job market dataset, ensuring normalized job titles.
    """
    global _CACHED_DF
    if _CACHED_DF is not None and data_path is None:
        return _CACHED_DF

    path = data_path or DEFAULT_DATA_PATH
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
    # Ensure standardized canonical roles
    df["clean_role"] = (
        df["job_title"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(ROLE_NORMALIZATION_MAP)
        .fillna(df["job_title"].astype(str).str.strip().str.title())
    )

    if data_path is None:
        _CACHED_DF = df
    return df


def normalize_role_title(job_role: str) -> str:
    """
    Normalizes arbitrary job title strings to canonical job roles available in the dataset.
    """
    if not job_role or pd.isna(job_role):
        return "Software Engineer"

    clean_str = str(job_role).strip().lower()
    return ROLE_NORMALIZATION_MAP.get(clean_str, str(job_role).strip().title())


def normalize_candidate_skills(
    candidate_skills: Union[List[str], str, None]
) -> List[str]:
    """
    Standardizes candidate skill inputs from lists, comma-separated strings,
    or raw resume text.
    """
    if candidate_skills is None:
        return []

    if isinstance(candidate_skills, list):
        # Flatten and clean tokens
        tokens = set()
        for item in candidate_skills:
            if isinstance(item, str):
                for sub in item.split(","):
                    clean = sub.strip()
                    if clean:
                        tokens.add(clean)
        return sorted(list(tokens))

    if isinstance(candidate_skills, str):
        text = candidate_skills.strip()
        if not text:
            return []

        # If text looks like a free-form resume (sentences or length > 200), extract via NLP dictionary
        tokens = [s.strip() for s in text.split(",") if s.strip()]
        if any(len(t.split()) > 4 for t in tokens) or len(text) > 200:
            extracted = extract_skills_from_text(text)
            return extracted if extracted else sorted(list(set(tokens)))
        return sorted(list(set(tokens)))

    return []


# ---------------------------------------------------------
# CORE MARKET SKILL DEMAND ANALYSIS
# ---------------------------------------------------------

def get_available_job_roles(df: Optional[pd.DataFrame] = None) -> List[str]:
    """
    Dynamically retrieves sorted list of available canonical job roles from the dataset.
    """
    dataset = df if df is not None else get_dataset()
    roles = dataset["clean_role"].dropna().unique().tolist()
    return sorted(roles)


def analyze_market_skill_demand(
    df: Optional[pd.DataFrame] = None,
    by: Optional[str] = None,
    top_n: Optional[int] = None,
) -> pd.DataFrame:
    """
    Analyzes technical skill demand across the job market dataset.

    Prevents counting duplicate skills within the same posting.

    Args:
        df: Optional DataFrame. If None, loads cleaned_job_market_all.csv.
        by: Optional grouping column: 'job_title' / 'clean_role', 'experience_level', or 'city'.
        top_n: Optional limit to return Top N in-demand skills.

    Returns:
        DataFrame containing skill demand metrics (skill, job_count, demand_percentage).
    """
    dataset = df if df is not None else get_dataset()
    total_jobs = len(dataset)
    if total_jobs == 0:
        return pd.DataFrame(columns=["skill", "job_count", "demand_percentage"])

    # 1. Overall Skill Demand
    if by is None:
        skill_counts = Counter()
        for s_str in dataset["skills_required_clean"].dropna():
            # Avoid counting duplicate skills within the same posting
            unique_skills = set(s.strip() for s in str(s_str).split(",") if s.strip())
            for skill in unique_skills:
                skill_counts[skill] += 1

        records = []
        for skill, count in skill_counts.most_common():
            pct = round((count / total_jobs) * 100, 2)
            records.append({
                "skill": skill,
                "job_count": int(count),
                "demand_percentage": pct,
            })
        result_df = pd.DataFrame(records)
        if top_n is not None and top_n > 0:
            result_df = result_df.head(top_n)
        return result_df

    # 2. Grouped Skill Demand (by role, experience, city)
    group_col = "clean_role" if by in ["job_title", "clean_role", "role"] else by
    if group_col not in dataset.columns:
        raise ValueError(f"Grouping column '{by}' not found in dataset columns: {list(dataset.columns)}")

    records = []
    for group_val, sub_df in dataset.groupby(group_col):
        group_total = len(sub_df)
        if group_total == 0:
            continue
        counts = Counter()
        for s_str in sub_df["skills_required_clean"].dropna():
            unique_skills = set(s.strip() for s in str(s_str).split(",") if s.strip())
            for skill in unique_skills:
                counts[skill] += 1

        for skill, count in counts.most_common():
            pct = round((count / group_total) * 100, 2)
            records.append({
                group_col: group_val,
                "skill": skill,
                "job_count": int(count),
                "demand_percentage": pct,
            })

    result_df = pd.DataFrame(records)
    if top_n is not None and top_n > 0:
        result_df = result_df.groupby(group_col).head(top_n).reset_index(drop=True)
    return result_df


# ---------------------------------------------------------
# ROLE-SPECIFIC SKILL BENCHMARKING
# ---------------------------------------------------------

def get_role_required_skills(
    job_role: str,
    df: Optional[pd.DataFrame] = None,
    essential_threshold: float = DEFAULT_ESSENTIAL_THRESHOLD,
    important_threshold: float = DEFAULT_IMPORTANT_THRESHOLD,
    min_demand: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Calculates technical skill requirements, demand percentages, and priority
    categories for a specific job role.

    Categories:
    - Essential: demand >= essential_threshold (default 50%)
    - Important: demand >= important_threshold and < essential_threshold (default 25% to <50%)
    - Additional: demand < important_threshold (default < 25%)

    Args:
        job_role: Target job title.
        df: Optional dataset DataFrame.
        essential_threshold: Lower bound for Essential skills.
        important_threshold: Lower bound for Important skills.
        min_demand: Minimum demand percentage to include in output.

    Returns:
        List of dictionaries with skill details sorted by demand descending.
    """
    dataset = df if df is not None else get_dataset()
    canonical_role = normalize_role_title(job_role)
    sub = dataset[dataset["clean_role"] == canonical_role]

    total_role_postings = len(sub)
    if total_role_postings == 0:
        return []

    # Count skill frequency avoiding duplicate counts per posting
    counts = Counter()
    for s_str in sub["skills_required_clean"].dropna():
        unique_skills = set(s.strip() for s in str(s_str).split(",") if s.strip())
        for skill in unique_skills:
            counts[skill] += 1

    required_skills = []
    for skill, count in counts.most_common():
        pct = round((count / total_role_postings) * 100, 2)
        if pct < min_demand:
            continue

        if pct >= essential_threshold:
            category = "Essential"
        elif pct >= important_threshold:
            category = "Important"
        else:
            category = "Additional"

        required_skills.append({
            "skill": skill,
            "job_count": int(count),
            "demand_percentage": pct,
            "category": category,
        })

    return required_skills


# ---------------------------------------------------------
# CANDIDATE SKILL COMPARISON & MATCH SCORING
# ---------------------------------------------------------

def compare_candidate_skills(
    candidate_skills: Union[List[str], str, None],
    job_role: str,
    df: Optional[pd.DataFrame] = None,
    essential_threshold: float = DEFAULT_ESSENTIAL_THRESHOLD,
    important_threshold: float = DEFAULT_IMPORTANT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Compares candidate skills against required skills for a target job role.

    Classifies skills into:
    - Matched Skills
    - Missing Essential Skills
    - Missing Important Skills
    - Missing Additional Skills
    """
    cand_skills_clean = normalize_candidate_skills(candidate_skills)
    cand_skill_set = set(cand_skills_clean)

    role_skills = get_role_required_skills(
        job_role=job_role,
        df=df,
        essential_threshold=essential_threshold,
        important_threshold=important_threshold,
    )

    all_req_skills = [s["skill"] for s in role_skills]
    matched_skills = [s for s in all_req_skills if s in cand_skill_set]
    missing_skills = [s for s in all_req_skills if s not in cand_skill_set]

    missing_essential = [
        s["skill"]
        for s in role_skills
        if s["category"] == "Essential" and s["skill"] not in cand_skill_set
    ]
    missing_important = [
        s["skill"]
        for s in role_skills
        if s["category"] == "Important" and s["skill"] not in cand_skill_set
    ]
    missing_additional = [
        s["skill"]
        for s in role_skills
        if s["category"] == "Additional" and s["skill"] not in cand_skill_set
    ]

    essential_all = [s["skill"] for s in role_skills if s["category"] == "Essential"]
    essential_matched = [s for s in essential_all if s in cand_skill_set]

    return {
        "job_role": normalize_role_title(job_role),
        "total_required_skills": len(all_req_skills),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "missing_essential_skills": missing_essential,
        "missing_important_skills": missing_important,
        "missing_additional_skills": missing_additional,
        "essential_match_count": len(essential_matched),
        "essential_missing_count": len(missing_essential),
    }


def calculate_skill_match_score(
    candidate_skills: Union[List[str], str, None],
    job_role: str,
    df: Optional[pd.DataFrame] = None,
) -> float:
    """
    Calculates demand-weighted skill match score percentage:

    Skill Match Score = (Sum of weights for matched skills / Sum of weights for all required skills) * 100
    where weight = skill demand percentage in that job role.

    Returns:
        float: Match score between 0.0 and 100.0%.
    """
    cand_skills_clean = normalize_candidate_skills(candidate_skills)
    cand_skill_set = set(cand_skills_clean)

    role_skills = get_role_required_skills(job_role=job_role, df=df)
    if not role_skills or not cand_skill_set:
        return 0.0

    total_weight = sum(s["demand_percentage"] for s in role_skills)
    if total_weight <= 0.0:
        return 0.0

    matched_weight = sum(
        s["demand_percentage"] for s in role_skills if s["skill"] in cand_skill_set
    )
    score = round((matched_weight / total_weight) * 100, 2)
    return min(100.0, max(0.0, score))


# ---------------------------------------------------------
# PERSONALIZED LEARNING RECOMMENDATIONS
# ---------------------------------------------------------

def generate_learning_recommendations(
    candidate_skills: Union[List[str], str, None],
    job_role: str,
    df: Optional[pd.DataFrame] = None,
    essential_threshold: float = DEFAULT_ESSENTIAL_THRESHOLD,
    important_threshold: float = DEFAULT_IMPORTANT_THRESHOLD,
) -> List[Dict[str, Any]]:
    """
    Generates actionable learning recommendations prioritized by missing skill tier:
    1. Missing Essential skills (highest market demand)
    2. Missing Important skills
    3. Missing Additional skills

    For each missing skill, provides practical learning actions and project practice.
    """
    cand_skills_clean = normalize_candidate_skills(candidate_skills)
    cand_skill_set = set(cand_skills_clean)

    role_skills = get_role_required_skills(
        job_role=job_role,
        df=df,
        essential_threshold=essential_threshold,
        important_threshold=important_threshold,
    )

    recommendations = []
    # Sort: Essential first, then Important, then Additional, then by demand desc
    priority_order = {"Essential": 0, "Important": 1, "Additional": 2}

    missing_role_skills = [s for s in role_skills if s["skill"] not in cand_skill_set]
    missing_sorted = sorted(
        missing_role_skills,
        key=lambda x: (priority_order.get(x["category"], 3), -x["demand_percentage"]),
    )

    for item in missing_sorted:
        skill_name = item["skill"]
        guidance = SKILL_LEARNING_GUIDANCE.get(
            skill_name,
            {
                "action": f"Study official documentation, tutorials, and fundamental concepts of {skill_name}.",
                "project": f"Build a practical hands-on application incorporating {skill_name} into your portfolio.",
            },
        )
        recommendations.append({
            "skill": skill_name,
            "demand_percentage": item["demand_percentage"],
            "priority": item["category"],
            "suggested_learning_action": guidance["action"],
            "suggested_project_practice": guidance["project"],
        })

    return recommendations


# ---------------------------------------------------------
# UNIFIED STRUCTURED SKILL GAP REPORT
# ---------------------------------------------------------

def generate_skill_gap_report(
    candidate_skills: Union[List[str], str, None],
    job_role: str,
    df: Optional[pd.DataFrame] = None,
    essential_threshold: float = DEFAULT_ESSENTIAL_THRESHOLD,
    important_threshold: float = DEFAULT_IMPORTANT_THRESHOLD,
) -> Dict[str, Any]:
    """
    Main unified function returning complete structured skill gap diagnosis,
    match score, and prioritized learning recommendations.

    Returns:
        Structured dictionary matching prompt requirements:
        {
            "job_role": str,
            "total_required_skills": int,
            "matched_skills": List[str],
            "missing_skills": List[str],
            "missing_essential_skills": List[str],
            "missing_important_skills": List[str],
            "missing_additional_skills": List[str],
            "skill_match_score": float,
            "essential_match_count": int,
            "essential_missing_count": int,
            "learning_recommendations": List[Dict[str, Any]],
            "analysis_warnings": List[str],
        }
    """
    warnings: List[str] = []
    dataset = df if df is not None else get_dataset()

    canonical_role = normalize_role_title(job_role)
    available_roles = get_available_job_roles(dataset)

    if canonical_role not in available_roles:
        warnings.append(
            f"Target role '{job_role}' was not found in the market dataset. "
            f"Defaulting to 'Software Engineer'."
        )
        canonical_role = "Software Engineer"

    cand_skills_clean = normalize_candidate_skills(candidate_skills)
    if not cand_skills_clean:
        warnings.append(
            "No candidate skills were provided or extracted from the resume. "
            "Match score is evaluated at 0.0%."
        )

    # Comparison metrics
    comparison = compare_candidate_skills(
        candidate_skills=cand_skills_clean,
        job_role=canonical_role,
        df=dataset,
        essential_threshold=essential_threshold,
        important_threshold=important_threshold,
    )

    # Match score
    match_score = calculate_skill_match_score(
        candidate_skills=cand_skills_clean,
        job_role=canonical_role,
        df=dataset,
    )

    # Learning recommendations
    recommendations = generate_learning_recommendations(
        candidate_skills=cand_skills_clean,
        job_role=canonical_role,
        df=dataset,
        essential_threshold=essential_threshold,
        important_threshold=important_threshold,
    )

    return {
        "job_role": canonical_role,
        "total_required_skills": comparison["total_required_skills"],
        "matched_skills": comparison["matched_skills"],
        "missing_skills": comparison["missing_skills"],
        "missing_essential_skills": comparison["missing_essential_skills"],
        "missing_important_skills": comparison["missing_important_skills"],
        "missing_additional_skills": comparison["missing_additional_skills"],
        "skill_match_score": match_score,
        "essential_match_count": comparison["essential_match_count"],
        "essential_missing_count": comparison["essential_missing_count"],
        "learning_recommendations": recommendations,
        "analysis_warnings": warnings,
    }


# ---------------------------------------------------------
# OBJECT-ORIENTED SKILL GAP ANALYZER CLASS
# ---------------------------------------------------------

class SkillGapAnalyzer:
    """
    Unified analyzer class encapsulating dataset state, role benchmarks,
    match scoring, and recommendation generation.
    """

    def __init__(
        self,
        data_path: Optional[str] = None,
        essential_threshold: float = DEFAULT_ESSENTIAL_THRESHOLD,
        important_threshold: float = DEFAULT_IMPORTANT_THRESHOLD,
    ):
        self.df = get_dataset(data_path)
        self.essential_threshold = essential_threshold
        self.important_threshold = important_threshold

    def get_available_roles(self) -> List[str]:
        return get_available_job_roles(self.df)

    def analyze_demand(
        self, by: Optional[str] = None, top_n: Optional[int] = None
    ) -> pd.DataFrame:
        return analyze_market_skill_demand(self.df, by=by, top_n=top_n)

    def get_role_skills(self, job_role: str, min_demand: float = 0.0) -> List[Dict[str, Any]]:
        return get_role_required_skills(
            job_role=job_role,
            df=self.df,
            essential_threshold=self.essential_threshold,
            important_threshold=self.important_threshold,
            min_demand=min_demand,
        )

    def compare(
        self, candidate_skills: Union[List[str], str, None], job_role: str
    ) -> Dict[str, Any]:
        return compare_candidate_skills(
            candidate_skills=candidate_skills,
            job_role=job_role,
            df=self.df,
            essential_threshold=self.essential_threshold,
            important_threshold=self.important_threshold,
        )

    def match_score(
        self, candidate_skills: Union[List[str], str, None], job_role: str
    ) -> float:
        return calculate_skill_match_score(
            candidate_skills=candidate_skills,
            job_role=job_role,
            df=self.df,
        )

    def recommend(
        self, candidate_skills: Union[List[str], str, None], job_role: str
    ) -> List[Dict[str, Any]]:
        return generate_learning_recommendations(
            candidate_skills=candidate_skills,
            job_role=job_role,
            df=self.df,
            essential_threshold=self.essential_threshold,
            important_threshold=self.important_threshold,
        )

    def generate_report(
        self, candidate_skills: Union[List[str], str, None], job_role: str
    ) -> Dict[str, Any]:
        return generate_skill_gap_report(
            candidate_skills=candidate_skills,
            job_role=job_role,
            df=self.df,
            essential_threshold=self.essential_threshold,
            important_threshold=self.important_threshold,
        )
