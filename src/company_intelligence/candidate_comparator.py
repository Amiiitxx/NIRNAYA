"""
Module: src.company_intelligence.candidate_comparator
Description: Evaluates candidate skills against specific company requirements.
Produces a detailed comparison matrix with explicit statuses (Matched, Missing,
Partially Matched, Needs Verification) and a transparent 70/30 demand-weighted match score.
"""

from typing import Any, Dict, List, Set, Tuple

# Related skill clusters for partial matching determination
RELATED_SKILL_CLUSTERS: List[Set[str]] = [
    {"FastAPI", "Flask", "Django"},
    {"PostgreSQL", "MySQL", "SQL"},
    {"PyTorch", "TensorFlow", "Deep Learning"},
    {"AWS", "GCP", "Azure"},
    {"React", "Next.js", "Vue.js", "Angular"},
    {"Docker", "Kubernetes", "Containerization"},
    {"Pandas", "NumPy", "Scikit-learn"},
    {"Spark", "PySpark", "Hadoop"},
]


def find_partial_match(required_skill: str, candidate_skills_set: Set[str]) -> bool:
    """
    Checks if the candidate possesses an alternative tool within the same technology cluster.
    """
    for cluster in RELATED_SKILL_CLUSTERS:
        if required_skill in cluster:
            # Check if candidate has any OTHER skill in the same cluster
            if any(cand_skill in cluster and cand_skill != required_skill for cand_skill in candidate_skills_set):
                return True
    return False


def calculate_company_match_score(
    mandatory_total: int,
    mandatory_matched: int,
    mandatory_partial: int,
    preferred_total: int,
    preferred_matched: int,
    preferred_partial: int,
) -> float:
    """
    Calculates a transparent, weighted match score:
    - 70% weight on Mandatory requirements
    - 30% weight on Preferred requirements
    - Partial matches receive 50% credit

    Returns:
        float between 0.0 and 100.0 rounded to 1 decimal place.
    """
    total_reqs = mandatory_total + preferred_total
    if total_reqs == 0:
        return 0.0

    # Effective score for mandatory
    mand_effective = mandatory_matched + (0.5 * mandatory_partial)
    mand_ratio = (mand_effective / mandatory_total) if mandatory_total > 0 else 1.0

    # Effective score for preferred
    pref_effective = preferred_matched + (0.5 * preferred_partial)
    pref_ratio = (pref_effective / preferred_total) if preferred_total > 0 else 1.0

    if mandatory_total > 0 and preferred_total > 0:
        score = (0.70 * mand_ratio + 0.30 * pref_ratio) * 100.0
    elif mandatory_total > 0:
        score = mand_ratio * 100.0
    else:
        score = pref_ratio * 100.0

    return max(0.0, min(100.0, round(score, 1)))


def compare_candidate_to_job(
    candidate_skills: List[str],
    job_requirements: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compares candidate skills against structured job requirements.

    Args:
        candidate_skills: List of technical skills confirmed or parsed from resume.
        job_requirements: Dict returned by `extract_job_requirements`.

    Returns:
        Structured evaluation dict:
            - comparison_matrix: List[Dict] with keys (skill, requirement_type, status, priority, reason)
            - match_score: float (0.0 to 100.0)
            - matched_skills: List[str]
            - missing_mandatory_skills: List[str]
            - missing_preferred_skills: List[str]
            - partially_matched_skills: List[str]
            - needs_verification_skills: List[str]
            - candidate_skill_count: int
            - job_skill_count: int
            - disclaimer: str
    """
    candidate_set = {s.strip() for s in (candidate_skills or []) if s.strip()}
    candidate_lower = {s.lower() for s in candidate_set}

    mandatory_skills = job_requirements.get("mandatory_skills", [])
    preferred_skills = job_requirements.get("preferred_skills", [])
    all_job_skills = job_requirements.get("all_skills", [])

    comparison_matrix: List[Dict[str, Any]] = []

    matched_skills: List[str] = []
    missing_mandatory_skills: List[str] = []
    missing_preferred_skills: List[str] = []
    partially_matched_skills: List[str] = []
    needs_verification_skills: List[str] = []

    # Track processed skills to avoid duplicate rows
    seen_skills: Set[str] = set()

    # 1. Process Mandatory Requirements
    mand_matched_count = 0
    mand_partial_count = 0
    for skill in mandatory_skills:
        if skill in seen_skills:
            continue
        seen_skills.add(skill)

        if skill.lower() in candidate_lower or skill in candidate_set:
            status = "Matched"
            priority = "High"
            reason = "Candidate has this mandatory requirement."
            matched_skills.append(skill)
            mand_matched_count += 1
        elif find_partial_match(skill, candidate_set):
            status = "Partially Matched"
            priority = "High"
            reason = "Candidate possesses an alternative tool in the same technology cluster."
            partially_matched_skills.append(skill)
            mand_partial_count += 1
        elif skill in {"System Design", "Agile/Scrum", "Statistics"}:
            status = "Needs Verification"
            priority = "Medium"
            reason = "Broad engineering discipline requiring portfolio/project evidence."
            needs_verification_skills.append(skill)
        else:
            status = "Missing"
            priority = "High"
            reason = "Mandatory requirement missing from candidate profile."
            missing_mandatory_skills.append(skill)

        comparison_matrix.append({
            "skill": skill,
            "requirement_type": "Mandatory",
            "status": status,
            "priority": priority,
            "reason": reason,
        })

    # 2. Process Preferred Requirements
    pref_matched_count = 0
    pref_partial_count = 0
    for skill in preferred_skills:
        if skill in seen_skills:
            continue
        seen_skills.add(skill)

        if skill.lower() in candidate_lower or skill in candidate_set:
            status = "Matched"
            priority = "Medium"
            reason = "Candidate possesses this preferred/bonus skill."
            matched_skills.append(skill)
            pref_matched_count += 1
        elif find_partial_match(skill, candidate_set):
            status = "Partially Matched"
            priority = "Medium"
            reason = "Candidate has related technology experience."
            partially_matched_skills.append(skill)
            pref_partial_count += 1
        else:
            status = "Missing"
            priority = "Medium"
            reason = "Preferred/bonus skill not found in candidate profile."
            missing_preferred_skills.append(skill)

        comparison_matrix.append({
            "skill": skill,
            "requirement_type": "Preferred",
            "status": status,
            "priority": priority,
            "reason": reason,
        })

    # 3. Process Any Remaining Ancillary Skills
    for skill in all_job_skills:
        if skill in seen_skills:
            continue
        seen_skills.add(skill)

        if skill.lower() in candidate_lower or skill in candidate_set:
            status = "Matched"
            priority = "Low"
            reason = "Candidate has this ancillary skill."
            matched_skills.append(skill)
        else:
            status = "Missing"
            priority = "Low"
            reason = "Ancillary tech skill mentioned in posting."

        comparison_matrix.append({
            "skill": skill,
            "requirement_type": "Optional",
            "status": status,
            "priority": priority,
            "reason": reason,
        })

    # 4. Calculate Weighted Match Score
    match_score = calculate_company_match_score(
        mandatory_total=len(mandatory_skills),
        mandatory_matched=mand_matched_count,
        mandatory_partial=mand_partial_count,
        preferred_total=len(preferred_skills),
        preferred_matched=pref_matched_count,
        preferred_partial=pref_partial_count,
    )

    disclaimer = (
        "NIRNAYA Evaluation Notice: The match score represents technical keyword and requirement "
        "alignment calculated from the provided job posting text (70% mandatory weight, 30% preferred weight). "
        "It is an educational self-assessment tool and does not represent official employer evaluation, "
        "hiring probability, or employment guarantees."
    )

    return {
        "comparison_matrix": comparison_matrix,
        "match_score": match_score,
        "matched_skills": sorted(matched_skills),
        "missing_mandatory_skills": sorted(missing_mandatory_skills),
        "missing_preferred_skills": sorted(missing_preferred_skills),
        "partially_matched_skills": sorted(partially_matched_skills),
        "needs_verification_skills": sorted(needs_verification_skills),
        "candidate_skill_count": len(candidate_set),
        "job_skill_count": len(seen_skills),
        "disclaimer": disclaimer,
    }
