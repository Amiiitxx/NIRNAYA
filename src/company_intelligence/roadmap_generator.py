"""
Module: src.company_intelligence.roadmap_generator
Description: Dynamic, phased career roadmap generation (30-day, 60-day, 90-day).
Constructs actionable weekly milestones, hands-on assignments, and capstone project
deliverables tailored to the candidate's specific missing mandatory and preferred skills.
"""

from typing import Any, Dict, List, Optional


def generate_actionable_roadmap(
    comparison_result: Dict[str, Any],
    job_requirements: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates tailored 30, 60, and 90-day learning roadmaps addressing the candidate's skill gaps.

    Args:
        comparison_result: Output from `compare_candidate_to_job`.
        job_requirements: Output from `extract_job_requirements`.

    Returns:
        Structured roadmap dict with:
            - plan_30_days: Dict
            - plan_60_days: Dict
            - plan_90_days: Dict
            - summary: str
    """
    missing_mandatory = comparison_result.get("missing_mandatory_skills", [])
    missing_preferred = comparison_result.get("missing_preferred_skills", [])
    partial_skills = comparison_result.get("partially_matched_skills", [])
    job_title = job_requirements.get("job_title", "Target Role")
    company_name = job_requirements.get("company_name", "Target Company")

    # Combine prioritized learning targets
    priority_skills = missing_mandatory + partial_skills + missing_preferred
    if not priority_skills:
        return {
            "plan_30_days": {},
            "plan_60_days": {},
            "plan_90_days": {},
            "has_roadmap": False,
            "summary": "No unfulfilled skill requirements or skill gaps detected. No remediation roadmap is required.",
        }

    # 1. 30-Day Plan: Critical Foundations & High-Priority Mandatory Gaps
    skills_30 = priority_skills[: max(1, min(3, len(priority_skills)))]
    plan_30 = {
        "phase_name": "Phase 1: Critical Foundations & High-Priority Fillers",
        "timeframe": "Days 1 to 30",
        "focus_skills": skills_30,
        "weekly_milestones": [
            {
                "week": "Week 1",
                "title": f"Fundamentals & Syntax Setup: {', '.join(skills_30[:1])}",
                "deliverables": [
                    f"Set up local development environment and CLI tooling for {skills_30[0]}.",
                    "Study official documentation, core syntax, data structures, and lifecycle patterns.",
                    "Complete 5 fundamental hands-on coding exercises demonstrating core APIs.",
                ],
                "assignment": f"Implement a standalone script or service utilizing {skills_30[0]}.",
            },
            {
                "week": "Week 2",
                "title": f"Deep Dive & Hands-On Architecture: {', '.join(skills_30[:1])}",
                "deliverables": [
                    "Implement error handling, logging, and unit test suites.",
                    "Integrate with standard libraries and write automated tests.",
                    "Optimize execution performance and profile memory utilization.",
                ],
                "assignment": f"Build a modular library or service adhering to production standards in {skills_30[0]}.",
            },
            {
                "week": "Week 3",
                "title": f"Secondary Mandatory Skill: {', '.join(skills_30[1:2]) if len(skills_30) > 1 else 'Integration & Testing'}",
                "deliverables": [
                    f"Study core concepts and architectural best practices for {skills_30[1] if len(skills_30) > 1 else 'Integration'}.",
                    "Construct an integrated prototype connecting components together.",
                    "Configure automated linting, formatting, and type checks.",
                ],
                "assignment": "Deliver a tested prototype connecting the primary and secondary tools.",
            },
            {
                "week": "Week 4",
                "title": "Phase 1 Capstone & Code Review",
                "deliverables": [
                    "Publish a clean, documented GitHub repository featuring your Month 1 prototype.",
                    "Write an architectural README with installation steps and API documentation.",
                    "Complete self-evaluation checklist against target job mandatory requirements.",
                ],
                "assignment": f"Mini-project showcasing mastery of {', '.join(skills_30)}.",
            },
        ],
        "estimated_weekly_commitment": "8–10 hours/week",
    }

    # 2. 60-Day Plan: Pipeline Integration, Databases & Cloud
    skills_60 = priority_skills[len(skills_30): len(skills_30) + 3]
    if not skills_60:
        skills_60 = ["Docker & Containerization", "CI/CD Pipelines", "Database Performance Tuning"]

    plan_60 = {
        "phase_name": "Phase 2: Full-Stack Integration & Production Engineering",
        "timeframe": "Days 31 to 60",
        "focus_skills": skills_60,
        "weekly_milestones": [
            {
                "week": "Weeks 5–6",
                "title": f"Architecture & Data Storage: {', '.join(skills_60[:2])}",
                "deliverables": [
                    "Design relational or NoSQL schema supporting business use cases.",
                    "Write efficient indexing and transaction management queries.",
                    "Containerize application using multi-stage Dockerfiles.",
                ],
                "assignment": "Deploy containerized multi-service application with Docker Compose.",
            },
            {
                "week": "Weeks 7–8",
                "title": f"Production Automation: {', '.join(skills_60[2:]) if len(skills_60) > 2 else 'CI/CD & Cloud Hosting'}",
                "deliverables": [
                    "Set up GitHub Actions CI/CD pipeline for automated test execution on commit.",
                    "Deploy staging environment to public cloud (AWS / GCP / Cloud Run).",
                    "Implement health check endpoints and Prometheus/CloudWatch metrics.",
                ],
                "assignment": "Full end-to-end deployed web service with automated CI/CD and public URL.",
            },
        ],
        "estimated_weekly_commitment": "10–12 hours/week",
    }

    # 3. 90-Day Plan: System Design, Advanced Capstone & Technical Interview Readiness
    skills_90 = priority_skills[len(skills_30) + len(skills_60):]
    if not skills_90:
        skills_90 = ["Distributed System Design", "Mock Technical Interviews", "Portfolio Presentation"]

    plan_90 = {
        "phase_name": "Phase 3: Production Polish, System Design & Interview Mastery",
        "timeframe": "Days 61 to 90",
        "focus_skills": skills_90,
        "weekly_milestones": [
            {
                "week": "Weeks 9–10",
                "title": f"Large-Scale System Design & Scalability: {job_title}",
                "deliverables": [
                    "Study scalable system design architectures: caching, sharding, load balancing, queues.",
                    "Draft architectural whitepaper for target role problem statements.",
                    "Practice answering technical design questions with trade-off analysis.",
                ],
                "assignment": "Documented system architecture diagram and specification for enterprise scale.",
            },
            {
                "week": "Weeks 11–12",
                "title": f"Targeted Interview Readiness: {company_name}",
                "deliverables": [
                    "Update resume bullets using the Google XYZ formula with completed project metrics.",
                    "Practice live coding and behavioral STAR method scenarios.",
                    "Conduct 3 mock technical interviews targeting company interview formats.",
                ],
                "assignment": "Final portfolio submission and application launch ready for recruiters.",
            },
        ],
        "estimated_weekly_commitment": "8–10 hours/week",
    }

    summary = (
        f"This 90-day progressive learning pathway systematically remediates the {len(priority_skills)} identified "
        f"skill gaps for the '{job_title}' role at {company_name}. By dedicating 8–10 hours per week across 3 phases, "
        f"you transition from foundational syntax to deployed production capstones."
    )

    return {
        "target_role": job_title,
        "target_company": company_name,
        "summary": summary,
        "has_roadmap": True,
        "plan_30_days": plan_30,
        "plan_60_days": plan_60,
        "plan_90_days": plan_90,
    }
