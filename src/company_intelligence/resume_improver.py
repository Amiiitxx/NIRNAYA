"""
Module: src.company_intelligence.resume_improver
Description: Tailored resume enhancement recommendations aligned with specific job requirements.
Focuses on ATS keyword alignment, bullet impact restructuring (Google XYZ formula),
and formatting clarity without fabricating work history, metrics, or credentials.
"""

from typing import Any, Dict, List, Optional, Set


def generate_resume_improvements(
    candidate_skills: List[str],
    job_requirements: Dict[str, Any],
    resume_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates tailored, ethical resume improvement suggestions for a target job posting.

    Args:
        candidate_skills: Confirmed candidate skills.
        job_requirements: Extracted job requirements dict.
        resume_text: Optional raw text of the candidate's resume.

    Returns:
        Structured improvement suggestions dict:
            - keyword_suggestions: List[Dict]
            - bullet_rewrites: List[Dict]
            - structural_tips: List[str]
            - anti_hallucination_guarantee: str
    """
    candidate_set = {s.lower() for s in (candidate_skills or [])}
    mandatory_skills = job_requirements.get("mandatory_skills", [])
    preferred_skills = job_requirements.get("preferred_skills", [])
    job_title = job_requirements.get("job_title", "Target Role")
    company_name = job_requirements.get("company_name", "Target Company")

    # 1. Missing Keyword Suggestions
    keyword_suggestions = []
    for skill in mandatory_skills:
        if skill.lower() not in candidate_set:
            keyword_suggestions.append({
                "keyword": skill,
                "importance": "Critical (Mandatory)",
                "action": (
                    f"If you have hands-on academic, project, or professional exposure to {skill}, "
                    f"explicitly list '{skill}' in your Technical Skills summary and project bullet points."
                ),
            })

    for skill in preferred_skills[:5]:
        if skill.lower() not in candidate_set:
            keyword_suggestions.append({
                "keyword": skill,
                "importance": "Beneficial (Preferred)",
                "action": (
                    f"Adding verified exposure or coursework in '{skill}' will enhance your profile "
                    f"for {company_name}'s preferred qualifications."
                ),
            })

    # 2. Action-Oriented Bullet Restructuring (Google XYZ Formula with Placeholders)
    # Never invent real metrics; provide structured templates prompting candidate to supply genuine data.
    bullet_rewrites = []

    matched_skills = [s for s in mandatory_skills if s.lower() in candidate_set]
    sample_skills = matched_skills[:3] if matched_skills else candidate_skills[:3]

    for skill in sample_skills:
        bullet_rewrites.append({
            "skill_focus": skill,
            "weak_pattern_example": f"Worked on {skill} for building applications and pipelines.",
            "recommended_xyz_structure": (
                f"Architected [specific feature/pipeline] utilizing {skill}, resulting in "
                f"[quantify measured impact: e.g., X% latency reduction, Y hours saved weekly, or Z queries processed/sec] "
                f"by [specific architectural technique or optimization applied]."
            ),
            "rationale": f"Demonstrates technical ownership and business impact with {skill} rather than passive tool usage.",
        })

    # 3. Structural and ATS Readability Advice
    structural_tips = [
        f"Position your most relevant technical projects and experiences matching '{job_title}' in the upper half of page 1.",
        "Ensure standard section headings ('Technical Skills', 'Experience', 'Projects', 'Education') to maintain 100% ATS parser readability.",
        "Include active GitHub repository links or live demo URLs for portfolio projects that showcase target mandatory skills.",
        "Eliminate ambiguous subjective phrases (e.g., 'hard-working self-starter') in favor of concrete engineering deliverables.",
        "Verify that acronyms like CI/CD, REST APIs, or AWS are paired with their specific implementation tools (e.g., GitHub Actions, Docker, ECS).",
    ]

    anti_hallucination_guarantee = (
        "NIRNAYA Ethics & Accuracy Guarantee: These suggestions are designed to enhance the presentation "
        "of your genuine skills and experiences. Never insert false metrics, unearned certifications, or "
        "unverified job titles onto your resume. Recruiters verify technical claims through technical interviews "
        "and reference checks."
    )

    return {
        "target_role": job_title,
        "target_company": company_name,
        "keyword_suggestions": keyword_suggestions,
        "bullet_rewrites": bullet_rewrites,
        "structural_tips": structural_tips,
        "anti_hallucination_guarantee": anti_hallucination_guarantee,
    }
