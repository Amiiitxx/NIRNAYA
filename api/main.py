"""
Module: FastAPI Job Market Intelligence & Analytics API
Description: High-performance REST API exposing macro market intelligence,
role-level diagnostics, geographic distributions, salary analytics, and health status.
"""

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from database.db import check_db_connection
from src.job_market_intelligence import (
    get_city_analytics,
    get_city_dossier,
    get_job_role_analytics,
    get_market_overview,
    get_role_dossier,
    get_salary_analytics,
    get_skill_intelligence,
    get_temporal_trends,
)

# ---------------------------------------------------------
# FASTAPI APPLICATION INSTANTIATION
# ---------------------------------------------------------

app = FastAPI(
    title="AI-Powered Job Market Intelligence API",
    description=(
        "Production-grade RESTful API delivering comprehensive Indian technology job market "
        "intelligence, role requirements, salary analytics, and geographic insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ---------------------------------------------------------
# PYDANTIC RESPONSE SCHEMAS
# ---------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = Field(..., json_schema_extra={"example": "HEALTHY"})
    version: str = Field(..., json_schema_extra={"example": "1.0.0"})
    database: Dict[str, Any] = Field(...)
    dataset_status: str = Field(..., json_schema_extra={"example": "AVAILABLE"})


class MarketOverviewResponse(BaseModel):
    total_job_postings: int
    total_unique_companies: int
    total_job_roles: int
    total_cities: int
    employment_type_distribution: Dict[str, int]
    work_mode_distribution: Dict[str, int]
    experience_level_distribution: Dict[str, int]


class RoleRankItem(BaseModel):
    rank: int
    role: str
    job_count: int
    share_percentage: float


class JobRolesResponse(BaseModel):
    total_roles: int
    top_roles: List[RoleRankItem]
    all_role_counts: Dict[str, int]


class CityRankItem(BaseModel):
    rank: int
    city: str
    job_count: int
    share_percentage: float


class CitiesResponse(BaseModel):
    total_cities: int
    top_cities: List[CityRankItem]
    state_distribution: Dict[str, int]


class SkillRankItem(BaseModel):
    rank: int
    skill: str
    job_count: int
    demand_percentage: float


class SkillCoOccurrenceItem(BaseModel):
    skill_pair: str
    skill_1: str
    skill_2: str
    co_occurrence_count: int
    co_occurrence_percentage: float


class SkillsResponse(BaseModel):
    total_skills_returned: int
    top_skills: List[SkillRankItem]
    co_occurring_skills: List[SkillCoOccurrenceItem]


class SalarySummary(BaseModel):
    mean_lpa: Optional[float]
    median_lpa: Optional[float]
    min_lpa: Optional[float] = None
    max_lpa: Optional[float] = None


class SalaryAnalyticsResponse(BaseModel):
    target_metric: str = "salary_mid_lpa (INR LPA)"
    salary_range_analysis: Dict[str, Any]
    median_salary_by_role: Dict[str, float]
    salary_by_experience: Dict[str, Dict[str, float]]
    salary_by_work_mode: Dict[str, Dict[str, float]]
    top_paying_roles: List[Dict[str, Any]]


class TrendsResponse(BaseModel):
    monthly_postings: List[Dict[str, Any]]
    quarterly_postings: List[Dict[str, Any]]
    data_limitation_note: str


# ---------------------------------------------------------
# API ENDPOINTS
# ---------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="API & Database Health Check",
)
def get_health_status() -> HealthResponse:
    """Returns application status, database connectivity, and version."""
    db_ok, db_msg = check_db_connection()
    return HealthResponse(
        status="HEALTHY",
        version="1.0.0",
        database={
            "connected": db_ok,
            "status_message": db_msg,
        },
        dataset_status="AVAILABLE",
    )


@app.get(
    "/api/market/overview",
    response_model=MarketOverviewResponse,
    tags=["Market Intelligence"],
    summary="Get High-Level Market KPIs & Distributions",
)
def get_overview() -> MarketOverviewResponse:
    """Returns macro market metrics: total jobs, unique companies, cities, work modes, and experience levels."""
    try:
        overview = get_market_overview()
        return MarketOverviewResponse(**overview)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing market overview: {str(e)}",
        )


@app.get(
    "/api/market/job-roles",
    response_model=JobRolesResponse,
    tags=["Job Roles"],
    summary="List In-Demand Tech Job Roles",
)
def get_job_roles(
    limit: int = Query(default=12, ge=1, le=50, description="Max roles to return in ranking"),
) -> JobRolesResponse:
    """Returns ranked list of tech job roles with posting counts and market shares."""
    try:
        data = get_job_role_analytics(top_n=limit)
        return JobRolesResponse(
            total_roles=len(data["postings_by_role"]),
            top_roles=[RoleRankItem(**item) for item in data["top_roles"]],
            all_role_counts=data["postings_by_role"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job roles: {str(e)}",
        )


@app.get(
    "/api/market/cities",
    response_model=CitiesResponse,
    tags=["Geographic Analytics"],
    summary="Get Hiring Concentration Across Tech Hubs",
)
def get_cities(
    limit: int = Query(default=10, ge=1, le=50, description="Max cities in ranking"),
) -> CitiesResponse:
    """Returns top hiring cities and state distributions."""
    try:
        data = get_city_analytics(top_n=limit)
        return CitiesResponse(
            total_cities=len(data["postings_by_city"]),
            top_cities=[CityRankItem(**item) for item in data["top_cities"]],
            state_distribution=data["state_distribution"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving cities: {str(e)}",
        )


@app.get(
    "/api/market/skills",
    response_model=SkillsResponse,
    tags=["Technical Skills"],
    summary="Get In-Demand Technical Skills & Co-occurrence",
)
def get_skills(
    top_n: int = Query(default=20, ge=5, le=50, description="Top N skills to return"),
) -> SkillsResponse:
    """Returns top in-demand skills and top co-occurring skill pairs."""
    try:
        data = get_skill_intelligence(top_n=top_n)
        return SkillsResponse(
            total_skills_returned=len(data["top_skills"]),
            top_skills=[SkillRankItem(**s) for s in data["top_skills"]],
            co_occurring_skills=[SkillCoOccurrenceItem(**p) for p in data["co_occurring_skills"]],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving skills: {str(e)}",
        )


@app.get(
    "/api/market/salary",
    response_model=SalaryAnalyticsResponse,
    tags=["Compensation Analytics"],
    summary="Get Verified Salary Analytics by Role, Experience, and City",
)
def get_salaries() -> SalaryAnalyticsResponse:
    """Returns verified compensation benchmarks computed exclusively on cleaned salary records."""
    try:
        data = get_salary_analytics()
        return SalaryAnalyticsResponse(
            salary_range_analysis=data["salary_range_analysis"],
            median_salary_by_role=data["median_salary_by_role"],
            salary_by_experience=data["salary_by_experience"],
            salary_by_work_mode=data["salary_by_work_mode"],
            top_paying_roles=data["top_paying_roles"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing salary analytics: {str(e)}",
        )


@app.get(
    "/api/market/trends",
    response_model=TrendsResponse,
    tags=["Temporal Analytics"],
    summary="Get Monthly & Quarterly Posting Volumes",
)
def get_trends() -> TrendsResponse:
    """Returns historical monthly and quarterly posting trends from dataset dates."""
    try:
        trends = get_temporal_trends()
        return TrendsResponse(**trends)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error computing trends: {str(e)}",
        )


@app.get(
    "/api/market/role/{job_role}",
    tags=["Job Roles"],
    summary="Get Comprehensive Role Dossier",
)
def get_single_role(job_role: str) -> Dict[str, Any]:
    """Returns 360-degree analytics for a specific role (skills, salary, cities, work mode)."""
    dossier = get_role_dossier(job_role)
    if dossier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job role '{job_role}' was not found in the market dataset.",
        )
    return dossier


@app.get(
    "/api/market/city/{city}",
    tags=["Geographic Analytics"],
    summary="Get Comprehensive City Dossier",
)
def get_single_city(city: str) -> Dict[str, Any]:
    """Returns 360-degree analytics for a specific city (postings, top roles, skills, salaries)."""
    dossier = get_city_dossier(city)
    if dossier is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"City '{city}' was not found in the market dataset.",
        )
    return dossier
