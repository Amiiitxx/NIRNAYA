"""
Module: src.company_intelligence.recommendation_engine
Description: Targeted skill gap remediation for company-specific requirements.
Generates structured learning recommendations separated into High, Medium, and Low
priorities with actionable topics, exercises, and project ideas.
Reuses curated learning guidance from the core skill analyzer.
"""

from typing import Any, Dict, List, Optional

# Direct reuse of existing curated learning guidance from core skill analyzer
try:
    from src.skill_analyzer import SKILL_LEARNING_GUIDANCE
except ImportError:
    SKILL_LEARNING_GUIDANCE = {}

# Additional curated guidance for extended company tech stack
EXTENDED_SKILL_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "FastAPI": {
        "why_it_matters": "Modern standard for high-performance Python asynchronous REST microservices and ML model serving.",
        "topics": ["Pydantic V2 validation", "Async/await concurrency", "Dependency Injection", "OAuth2/JWT authentication", "OpenAPI schemas"],
        "resources": ["FastAPI Official Documentation (tiangolo.com)", "Full Stack FastAPI Template"],
        "exercise": "Build an asynchronous CRUD API with Pydantic validation, dependency injection, and automated OpenAPI documentation.",
        "project_idea": "High-throughput ML inference service with batch prediction endpoints and rate limiting.",
        "estimated_duration": "1–2 weeks",
    },
    "Docker": {
        "why_it_matters": "Universal deployment standard ensuring reproducible container environments across local development and production.",
        "topics": ["Dockerfile multi-stage builds", "Docker Compose orchestration", "Volume management", "Network isolation", "Image size optimization"],
        "resources": ["Docker Official Documentation & Guides", "Play with Docker Labs"],
        "exercise": "Write a multi-stage Dockerfile packaging a Python web service under 150MB with non-root security.",
        "project_idea": "Containerize a full-stack application (FastAPI + PostgreSQL + Redis) using Docker Compose with automated health checks.",
        "estimated_duration": "1–2 weeks",
    },
    "Kubernetes": {
        "why_it_matters": "Production container orchestration standard for auto-scaling, self-healing deployments, and ingress routing.",
        "topics": ["Pods, Deployments, and Services", "ConfigMaps & Secrets", "Ingress controllers", "Horizontal Pod Autoscalers (HPA)", "Helm charts"],
        "resources": ["Kubernetes.io Official Tutorials", "Minikube Local Cluster Guide"],
        "exercise": "Deploy a containerized API on Minikube with a Service, ConfigMap, and RollingUpdate deployment strategy.",
        "project_idea": "Production Kubernetes deployment with HPA scaling based on CPU/memory load and custom Ingress routing.",
        "estimated_duration": "3–4 weeks",
    },
    "AWS": {
        "why_it_matters": "Leading enterprise cloud infrastructure powering modern scalable data, web, and machine learning architectures.",
        "topics": ["EC2, S3, and IAM security policies", "Lambda serverless functions", "RDS managed databases", "ECS/EKS container hosting", "CloudWatch monitoring"],
        "resources": ["AWS Skill Builder Official Free Tier Courses", "AWS Well-Architected Framework"],
        "exercise": "Deploy a serverless REST endpoint using AWS Lambda, API Gateway, and S3 storage with least-privilege IAM roles.",
        "project_idea": "End-to-end cloud pipeline: S3 trigger -> Lambda data validation -> RDS PostgreSQL -> ECS hosted dashboard.",
        "estimated_duration": "3–4 weeks",
    },
    "PostgreSQL": {
        "why_it_matters": "The enterprise relational database of choice for ACID-compliant structured data, advanced indexing, and JSONB storage.",
        "topics": ["Complex SQL joins & window functions", "B-tree and GIN indexing", "EXPLAIN ANALYZE query planning", "Transactions and row-level locking", "JSONB semi-structured queries"],
        "resources": ["PostgreSQL Official Documentation", "Postgres Weekly Tutorials"],
        "exercise": "Write complex analytical SQL queries using CTEs, window functions (ROW_NUMBER, DENSE_RANK), and analyze performance with EXPLAIN.",
        "project_idea": "High-performance transactional schema with partitioned tables, automated audit logging, and full-text search.",
        "estimated_duration": "2 weeks",
    },
    "React": {
        "why_it_matters": "The preeminent front-end library for building interactive, component-driven user interfaces in modern web platforms.",
        "topics": ["Hooks (useState, useEffect, useMemo)", "State management (Zustand/Redux)", "Component lifecycle", "API integration with Axios/Fetch", "Tailwind CSS styling"],
        "resources": ["React.dev Official Documentation", "Scrimba React Course"],
        "exercise": "Build a responsive data dashboard with searchable tables, pagination, and dynamic dark mode toggles.",
        "project_idea": "Career analytics portal consuming REST endpoints with interactive charts and real-time state management.",
        "estimated_duration": "2–3 weeks",
    },
    "System Design": {
        "why_it_matters": "Essential for mid-to-senior engineering roles to design scalable, fault-tolerant, and maintainable distributed architectures.",
        "topics": ["Load balancing & reverse proxies", "Caching strategies (CDN, Redis)", "Database sharding & replication", "Asynchronous messaging (Kafka, RabbitMQ)", "CAP theorem"],
        "resources": ["System Design Primer (GitHub)", "Designing Data-Intensive Applications (M. Kleppmann)"],
        "exercise": "Design a URL shortener or real-time notification system calculating throughput, storage requirements, and bottleneck mitigations.",
        "project_idea": "Documented architectural blueprint and prototype for a distributed job application tracker handling 10,000 req/sec.",
        "estimated_duration": "3–4 weeks",
    },
}

# Merge guidance repositories
COMBINED_GUIDANCE = {**SKILL_LEARNING_GUIDANCE, **EXTENDED_SKILL_GUIDANCE}


def get_guidance_for_skill(skill: str, requirement_type: str, status: str) -> Dict[str, Any]:
    """
    Retrieves or generates structured learning guidance for a specific skill gap.
    """
    base_info = COMBINED_GUIDANCE.get(skill)

    if base_info:
        why = base_info.get("why_it_matters") or f"Key technical capability frequently required for {requirement_type.lower()} job functions."
        topics = base_info.get("topics") or [f"Core fundamentals of {skill}", f"Practical application in production", f"Integration and debugging"]
        resources = base_info.get("resources") or [f"{skill} Official Documentation & Guides"]
        exercise = base_info.get("exercise") or f"Implement a working hands-on module demonstrating core {skill} capabilities."
        project = base_info.get("project_idea") or f"Production portfolio project integrating {skill} into an end-to-end architecture."
        duration = base_info.get("estimated_duration") or "1–2 weeks"
    else:
        why = f"Directly requested as a {requirement_type.lower()} requirement in the target company job specification."
        topics = [f"Core concepts and syntax of {skill}", f"Best practices and design patterns", f"Testing and production deployment"]
        resources = [f"{skill} Official Documentation", f"Open-source GitHub examples for {skill}"]
        exercise = f"Complete guided practical exercises and build a working demo using {skill}."
        project = f"Build an end-to-end portfolio project featuring {skill} to showcase to recruiters."
        duration = "2 weeks"

    priority = "High" if requirement_type == "Mandatory" and status == "Missing" else (
        "Medium" if (requirement_type == "Preferred" and status == "Missing") or status == "Partially Matched" else "Low"
    )

    return {
        "skill": skill,
        "priority": priority,
        "requirement_type": requirement_type,
        "status": status,
        "why_it_matters": why,
        "topics": topics,
        "resources": resources,
        "exercise": exercise,
        "project_idea": project,
        "estimated_duration": duration,
    }


def generate_company_skill_recommendations(
    comparison_result: Dict[str, Any],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generates categorized skill recommendations for all missing or partially matched skills.

    Returns:
        Dict with keys:
            - 'high_priority': List[Dict]
            - 'medium_priority': List[Dict]
            - 'low_priority': List[Dict]
            - 'all_recommendations': List[Dict]
    """
    matrix = comparison_result.get("comparison_matrix", [])

    high_priority = []
    medium_priority = []
    low_priority = []
    all_recs = []

    for item in matrix:
        status = item.get("status")
        req_type = item.get("requirement_type", "Optional")
        skill = item.get("skill", "")

        # Only recommend for missing or partial skills
        if status in {"Missing", "Partially Matched", "Needs Verification"}:
            rec = get_guidance_for_skill(skill, req_type, status)
            all_recs.append(rec)

            if rec["priority"] == "High":
                high_priority.append(rec)
            elif rec["priority"] == "Medium":
                medium_priority.append(rec)
            else:
                low_priority.append(rec)

    return {
        "high_priority": high_priority,
        "medium_priority": medium_priority,
        "low_priority": low_priority,
        "all_recommendations": all_recs,
    }
