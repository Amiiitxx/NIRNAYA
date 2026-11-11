"""
Module: src.company_intelligence.company_analyzer
Description: Primary orchestrator for company-specific intelligence analysis.
Coordinates safe web fetching, structured requirement extraction, candidate comparison,
priority remediation recommendations, resume enhancement tips, and phased roadmaps.
"""

from typing import Any, Dict, List, Optional

from src.company_intelligence.candidate_comparator import compare_candidate_to_job
from src.company_intelligence.job_extractor import (
    classify_input_source,
    fetch_job_content,
)
from src.company_intelligence.recommendation_engine import (
    generate_company_skill_recommendations,
)
from src.company_intelligence.requirement_parser import extract_job_requirements
from src.company_intelligence.resume_improver import generate_resume_improvements
from src.company_intelligence.roadmap_generator import generate_actionable_roadmap


def analyze_company_target(
    input_content: str,
    candidate_skills: List[str],
    resume_text: Optional[str] = None,
    source_type: Optional[str] = None,
    source_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes end-to-end company intelligence and skill gap analysis.

    Args:
        input_content: Either a URL (Direct Job, Company, LinkedIn) or raw job description text.
        candidate_skills: List of technical skills confirmed or parsed from resume.
        resume_text: Optional raw text from uploaded resume PDF.
        source_type: Optional explicit classification ('direct_job_url', 'company_url', 'linkedin_url', 'manual_text').
        source_url: Optional source URL when input_content is raw text.
    """
    detected_source = source_type or classify_input_source(input_content)

    # 1. Obtain Job Text
    is_url_input = input_content.strip().startswith("http://") or input_content.strip().startswith("https://")
    if detected_source in {"direct_job_url", "company_url", "linkedin_url"} and is_url_input:
        fetch_result = fetch_job_content(input_content)
        if not fetch_result["success"]:
            return {
                "success": False,
                "source_type": detected_source,
                "job_requirements": {},
                "comparison_result": {},
                "recommendations": {},
                "resume_improvements": {},
                "roadmap": {},
                "error_message": fetch_result["error_message"],
                "is_login_walled": fetch_result.get("is_login_walled", False),
            }
        job_raw_text = fetch_result["raw_text"]
        target_source_url = input_content
    else:
        job_raw_text = input_content
        target_source_url = source_url

    if not job_raw_text or len(job_raw_text.strip()) < 20:
        return {
            "success": False,
            "source_type": detected_source,
            "job_requirements": {},
            "comparison_result": {},
            "recommendations": {},
            "resume_improvements": {},
            "roadmap": {},
            "error_message": "Job description is too short or empty. Please provide a detailed job specification.",
            "is_login_walled": False,
        }

    # 2. Extract Structured Job Requirements
    job_reqs = extract_job_requirements(job_raw_text, source_url=target_source_url)

    # Check if job requirements are insufficient or if it's a generic company homepage
    has_sufficient_requirements = bool(job_reqs.get("all_skills"))
    job_reqs["has_sufficient_requirements"] = has_sufficient_requirements
    is_company_homepage = bool(
        job_reqs.get("company_name", "Not specified") not in {"Not specified", ""}
        and not has_sufficient_requirements
    )
    job_reqs["is_company_homepage"] = is_company_homepage

    if not has_sufficient_requirements:
        insufficient_msg = (
            "Insufficient job requirement data. Please provide a specific job posting URL or paste the job description manually."
        )
        return {
            "success": True,
            "has_sufficient_requirements": False,
            "is_company_homepage": is_company_homepage,
            "source_type": detected_source,
            "job_requirements": job_reqs,
            "comparison_result": {
                "comparison_matrix": [],
                "match_score": 0.0,
                "matched_skills": [],
                "missing_mandatory_skills": [],
                "missing_preferred_skills": [],
                "partially_matched_skills": [],
                "needs_verification_skills": [],
                "candidate_skill_count": len(candidate_skills),
                "job_skill_count": 0,
                "disclaimer": insufficient_msg,
            },
            "recommendations": {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": [],
                "all_recommendations": [],
                "summary": insufficient_msg,
            },
            "resume_improvements": {
                "missing_keyword_suggestions": [],
                "bullet_improvements": [],
                "ats_formatting_tips": [],
                "summary": insufficient_msg,
            },
            "roadmap": {
                "plan_30_days": {},
                "plan_60_days": {},
                "plan_90_days": {},
                "has_roadmap": False,
                "summary": insufficient_msg,
            },
            "error_message": insufficient_msg,
            "is_login_walled": False,
        }

    # 3. Compare Candidate to Job Requirements
    comparison = compare_candidate_to_job(candidate_skills, job_reqs)

    # 4. Generate Targeted Skill Remediation Recommendations
    recommendations = generate_company_skill_recommendations(comparison)

    # 5. Generate Tailored Resume Improvement Guidance
    resume_improvements = generate_resume_improvements(candidate_skills, job_reqs, resume_text=resume_text)

    # 6. Generate Actionable 30-60-90 Day Career Roadmap
    roadmap = generate_actionable_roadmap(comparison, job_reqs)

    return {
        "success": True,
        "has_sufficient_requirements": True,
        "is_company_homepage": False,
        "source_type": detected_source,
        "job_requirements": job_reqs,
        "comparison_result": comparison,
        "recommendations": recommendations,
        "resume_improvements": resume_improvements,
        "roadmap": roadmap,
        "error_message": None,
        "is_login_walled": False,
    }
