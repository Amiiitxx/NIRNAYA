"""
Module: src.company_intelligence.requirement_parser
Description: Deterministic NLP and regex boundary parsing of job descriptions.
Extracts company name, job title, location, experience requirements, education,
mandatory vs preferred technical skills, and taxonomy categorization.
Reuses canonical skill patterns from the core resume parser.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Direct reuse of existing canonical skill patterns from core NIRNAYA resume parser
from src.resume_parser import CANONICAL_SKILL_PATTERNS

# Extended tech skills & methodologies for company job descriptions
ADDITIONAL_SKILL_PATTERNS: Dict[str, str] = {
    "Go": r"\b(?:golang|go)\b",
    "Rust": r"\brust\b",
    "C#": r"\bc#|\bc-sharp\b",
    "Ruby": r"\bruby\b",
    "PHP": r"\bphp\b",
    "Spring Boot": r"\b(?:spring\s+boot|spring\s+framework)\b",
    "Angular": r"\bangular(?:\s*js)?\b",
    "Vue.js": r"\b(?:vue|vue[\s._-]*js)\b",
    "Next.js": r"\bnext[\s._-]*js\b",
    "GraphQL": r"\bgraphql\b",
    "Redis": r"\bredis\b",
    "Elasticsearch": r"\belasticsearch\b",
    "Terraform": r"\bterraform\b",
    "CI/CD": r"\b(?:ci[\s/_-]*cd|continuous\s+integration)\b",
    "Snowflake": r"\bsnowflake\b",
    "BigQuery": r"\bbigquery\b",
    "PySpark": r"\bpyspark\b",
    "MLflow": r"\bmlflow\b",
    "LLMs": r"\b(?:llm|llms|large\s+language\s+models|genai|generative\s+ai)\b",
    "Agile/Scrum": r"\b(?:agile|scrum|kanban)\b",
    "System Design": r"\bsystem\s+design\b",
    "REST APIs": r"\b(?:rest\s*apis?|restful)\b",
    "Microservices": r"\bmicroservices\b",
}

# Unified Skill Taxonomy: combines existing 42 patterns with additional company patterns
UNIFIED_SKILL_PATTERNS: Dict[str, str] = {
    **CANONICAL_SKILL_PATTERNS,
    **ADDITIONAL_SKILL_PATTERNS,
}

# Domain Category Mapping for clear visualization
SKILL_DOMAINS: Dict[str, str] = {
    "Python": "Programming Languages",
    "Java": "Programming Languages",
    "JavaScript": "Programming Languages",
    "TypeScript": "Programming Languages",
    "C++": "Programming Languages",
    "C#": "Programming Languages",
    "Go": "Programming Languages",
    "Rust": "Programming Languages",
    "Ruby": "Programming Languages",
    "PHP": "Programming Languages",
    "HTML/CSS": "Programming Languages",
    "SQL": "Databases",
    "PostgreSQL": "Databases",
    "MySQL": "Databases",
    "MongoDB": "Databases",
    "Redis": "Databases",
    "Elasticsearch": "Databases",
    "Snowflake": "Databases",
    "BigQuery": "Databases",
    "FastAPI": "Frameworks & Libraries",
    "Flask": "Frameworks & Libraries",
    "Django": "Frameworks & Libraries",
    "React": "Frameworks & Libraries",
    "Node.js": "Frameworks & Libraries",
    "Angular": "Frameworks & Libraries",
    "Vue.js": "Frameworks & Libraries",
    "Next.js": "Frameworks & Libraries",
    "Spring Boot": "Frameworks & Libraries",
    "REST APIs": "Frameworks & Libraries",
    "GraphQL": "Frameworks & Libraries",
    "AWS": "Cloud & DevOps",
    "Azure": "Cloud & DevOps",
    "GCP": "Cloud & DevOps",
    "Docker": "Cloud & DevOps",
    "Kubernetes": "Cloud & DevOps",
    "Terraform": "Cloud & DevOps",
    "CI/CD": "Cloud & DevOps",
    "Git": "Cloud & DevOps",
    "Linux": "Cloud & DevOps",
    "Microservices": "Cloud & DevOps",
    "Machine Learning": "Data Science & AI",
    "Deep Learning": "Data Science & AI",
    "NLP": "Data Science & AI",
    "Computer Vision": "Data Science & AI",
    "PyTorch": "Data Science & AI",
    "TensorFlow": "Data Science & AI",
    "Scikit-learn": "Data Science & AI",
    "Pandas": "Data Science & AI",
    "NumPy": "Data Science & AI",
    "Statistics": "Data Science & AI",
    "LLMs": "Data Science & AI",
    "MLflow": "Data Science & AI",
    "Spark": "Big Data & Data Eng",
    "PySpark": "Big Data & Data Eng",
    "Hadoop": "Big Data & Data Eng",
    "Airflow": "Big Data & Data Eng",
    "Kafka": "Big Data & Data Eng",
    "dbt": "Big Data & Data Eng",
    "Agile/Scrum": "Engineering Practices & Soft Skills",
    "System Design": "Engineering Practices & Soft Skills",
    "Problem Solving": "Engineering Practices & Soft Skills",
    "Communication": "Engineering Practices & Soft Skills",
}

# Section patterns for partitioning mandatory vs preferred requirements
MANDATORY_HEADINGS = re.compile(
    r"(?:requirements|must\s+have|basic\s+qualifications|minimum\s+qualifications|"
    r"what\s+you(?:'ll)?\s+need|what\s+we(?:'re)?\s+looking\s+for|essential\s+skills|"
    r"key\s+responsibilities|core\s+competencies|qualifications)",
    re.IGNORECASE,
)

PREFERRED_HEADINGS = re.compile(
    r"(?:preferred\s+qualifications|nice\s+to\s+have|good\s+to\s+have|bonus\s+points|"
    r"plus(?:es)?|preferred\s+skills|what\s+gives\s+you\s+an\s+edge|desired\s+skills)",
    re.IGNORECASE,
)


def extract_skills_from_segment(text: str) -> List[str]:
    """
    Extracts canonical skill names from a specific text segment using unified patterns.
    """
    found_skills = []
    if not text:
        return found_skills

    for skill_name, pattern in UNIFIED_SKILL_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill_name)

    return sorted(list(set(found_skills)))


def classify_skills_by_importance(full_text: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Partitions detected skills into:
    1. Mandatory (Must-Have)
    2. Preferred (Good-to-Have)
    3. Optional / Contextual

    Returns:
        Tuple of (mandatory_skills, preferred_skills, all_skills).
    """
    if not full_text:
        return [], [], []

    all_skills = extract_skills_from_segment(full_text)

    # Split text into paragraphs/sections
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n|\n(?=[A-Z][A-Za-z\s]{3,30}:)", full_text) if p.strip()]

    mandatory_text_blocks = []
    preferred_text_blocks = []
    current_mode = "neutral"

    for p in paragraphs:
        first_line = p.splitlines()[0] if p.splitlines() else ""
        if PREFERRED_HEADINGS.search(first_line):
            current_mode = "preferred"
            preferred_text_blocks.append(p)
        elif MANDATORY_HEADINGS.search(first_line):
            current_mode = "mandatory"
            mandatory_text_blocks.append(p)
        else:
            if current_mode == "mandatory":
                mandatory_text_blocks.append(p)
            elif current_mode == "preferred":
                preferred_text_blocks.append(p)

    mand_text = "\n".join(mandatory_text_blocks)
    pref_text = "\n".join(preferred_text_blocks)

    mandatory_skills = extract_skills_from_segment(mand_text)
    preferred_skills = [s for s in extract_skills_from_segment(pref_text) if s not in mandatory_skills]

    # If section headers were absent, designate top skills as mandatory
    if not mandatory_skills and not preferred_skills:
        mandatory_skills = all_skills[: max(1, int(len(all_skills) * 0.65))]
        preferred_skills = all_skills[len(mandatory_skills):]

    return mandatory_skills, preferred_skills, all_skills


def extract_job_requirements(raw_text: str, source_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts structured company intelligence and job requirements from raw text.
    Never hallucinates ungrounded details.

    Returns:
        Dict of extracted fields:
            - company_name: str
            - job_title: str
            - location: str
            - experience_required: str
            - education_required: str
            - mandatory_skills: List[str]
            - preferred_skills: List[str]
            - all_skills: List[str]
            - categorized_skills: Dict[str, List[str]]
            - summary: str
    """
    text = (raw_text or "").strip()
    if not text:
        return {
            "company_name": "Not specified",
            "job_title": "Not specified",
            "location": "Not specified",
            "experience_required": "Not specified",
            "education_required": "Not specified",
            "mandatory_skills": [],
            "preferred_skills": [],
            "all_skills": [],
            "categorized_skills": {},
            "summary": "No job description text provided.",
        }

    # 1. Company Name Extraction
    company_name = "Not specified"
    if source_url:
        parsed_url = re.search(r"https?://(?:www\.)?([^/]+)", source_url)
        if parsed_url:
            domain = parsed_url.group(1).lower()
            # Clean common suffixes
            domain_core = re.sub(r"\.(?:com|org|io|in|co|net|ai)$", "", domain)
            domain_core = domain_core.split(".")[-1]
            if domain_core not in {"greenhouse", "lever", "workday", "smartrecruiters", "linkedin", "naukri", "indeed"}:
                company_name = domain_core.title()

    # Look for "Company: XYZ" or "About XYZ" patterns
    comp_match = re.search(r"(?:company|organization|employer|about)\s*:\s*([^\r\n]{2,60})", text, re.IGNORECASE)
    if comp_match and company_name in {"Not specified", ""}:
        company_name = comp_match.group(1).strip()

    # 2. Job Title Extraction
    job_title = "Not specified"
    # Match common title patterns in the first 600 characters
    header_snippet = text[:600]
    title_match = re.search(
        r"(?:role|title|position|job\s+title)\s*:\s*([^\r\n]{3,60})",
        header_snippet,
        re.IGNORECASE,
    )
    if title_match:
        job_title = title_match.group(1).strip()
    else:
        # Match standard canonical role titles
        canonical_roles = [
            "Data Scientist", "Machine Learning Engineer", "Data Engineer",
            "AI Engineer", "Software Engineer", "Backend Developer",
            "Full Stack Developer", "Cloud Engineer", "DevOps Engineer",
            "MLOps Engineer", "Business Analyst", "Data Analyst",
            "Python Developer", "Frontend Developer",
        ]
        for role in canonical_roles:
            if re.search(r"\b" + re.escape(role) + r"\b", header_snippet, re.IGNORECASE):
                job_title = role
                break

    # 3. Location Extraction
    location = "Not specified"
    loc_match = re.search(
        r"(?:location|city|workplace|based\s+in)\s*:\s*([A-Za-z0-9\s,/-]{2,50})",
        header_snippet,
        re.IGNORECASE,
    )
    if loc_match:
        location = loc_match.group(1).strip()
    else:
        # Check standard tech hubs
        cities = ["Bengaluru", "Bangalore", "Delhi NCR", "Hyderabad", "Mumbai", "Pune", "Chennai", "Kolkata", "Remote", "Hybrid"]
        for c in cities:
            if re.search(r"\b" + re.escape(c) + r"\b", text, re.IGNORECASE):
                location = "Bengaluru" if c.lower() == "bangalore" else c
                break

    # 4. Experience Requirement Extraction
    experience_required = "Not specified"
    explicit_exp_match = re.search(r"(?:experience|work\s+experience|min\s+experience)\s*:\s*([^\r\n]{2,60})", text, re.IGNORECASE)
    if explicit_exp_match:
        experience_required = explicit_exp_match.group(1).strip()
    else:
        exp_patterns = [
            r"(\d+\s*[-–to]+\s*\d+\s*(?:\+)?\s*years?(?:\s+of)?\s+(?:relevant\s+)?experience)",
            r"(\d+\s*\+\s*years?(?:\s+of)?\s+(?:relevant\s+)?experience)",
            r"(fresher|entry[\s_-]*level|junior|mid[\s_-]*level|senior|lead)",
        ]
        for pat in exp_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                experience_required = m.group(1).strip().capitalize()
                break

    # 5. Education Requirement Extraction
    education_required = "Not specified"
    edu_match = re.search(
        r"\b(B\.?Tech|B\.?E\.?|B\.?Sc|M\.?Tech|M\.?S\.?|MCA|MBA|Ph\.?D\.?|Bachelor'?s|Master'?s)\b"
        r"(?:\s+(?:in|of)\s+[A-Za-z\s,/&-]{3,40})?",
        text,
        re.IGNORECASE,
    )
    if edu_match:
        education_required = edu_match.group(0).strip()

    # 6. Skills Partitioning & Categorization
    mandatory_skills, preferred_skills, all_skills = classify_skills_by_importance(text)

    categorized_skills: Dict[str, List[str]] = {}
    for skill in all_skills:
        domain = SKILL_DOMAINS.get(skill, "Other Technical Tools")
        if domain not in categorized_skills:
            categorized_skills[domain] = []
        categorized_skills[domain].append(skill)

    # 7. Role Overview / Summary
    summary_lines = [l for l in text.splitlines() if len(l.strip()) > 30][:3]
    summary = " ".join(summary_lines)[:350] + ("..." if len(summary_lines) > 0 else "")

    has_sufficient_requirements = bool(all_skills)
    is_company_homepage = bool(company_name not in {"Not specified", ""} and not has_sufficient_requirements)

    return {
        "company_name": company_name,
        "job_title": job_title,
        "location": location,
        "experience_required": experience_required,
        "education_required": education_required,
        "mandatory_skills": mandatory_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
        "categorized_skills": categorized_skills,
        "summary": summary,
        "has_sufficient_requirements": has_sufficient_requirements,
        "is_company_homepage": is_company_homepage,
    }
