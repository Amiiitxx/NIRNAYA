"""
Package: src.company_intelligence
Description: NIRNAYA Company-Specific Skill Gap Analysis & Career Improvement Engine.
Provides isolated, additive intelligence for analyzing target job postings, comparing
candidate resumes, generating targeted recommendations, resume enhancements, and 30-60-90 day roadmaps.
"""

from src.company_intelligence.validators import (
    validate_url_security,
    is_safe_url,
    SSRFSecurityError,
)
from src.company_intelligence.job_extractor import (
    fetch_job_content,
    classify_input_source,
)
from src.company_intelligence.requirement_parser import (
    extract_job_requirements,
    classify_skills_by_importance,
)
from src.company_intelligence.company_analyzer import (
    analyze_company_target,
)
from src.company_intelligence.candidate_comparator import (
    compare_candidate_to_job,
    calculate_company_match_score,
)
from src.company_intelligence.recommendation_engine import (
    generate_company_skill_recommendations,
)
from src.company_intelligence.resume_improver import (
    generate_resume_improvements,
)
from src.company_intelligence.roadmap_generator import (
    generate_actionable_roadmap,
)

__all__ = [
    "validate_url_security",
    "is_safe_url",
    "SSRFSecurityError",
    "fetch_job_content",
    "classify_input_source",
    "extract_job_requirements",
    "classify_skills_by_importance",
    "analyze_company_target",
    "compare_candidate_to_job",
    "calculate_company_match_score",
    "generate_company_skill_recommendations",
    "generate_resume_improvements",
    "generate_actionable_roadmap",
]
