"""
Unit tests for Module 5: FastAPI Service Endpoints (api/main.py)
Tests verify HTTP status codes, Pydantic response structures, query parameter filtering,
and 404 handling using FastAPI's TestClient.
"""

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Provides a TestClient instance for testing the FastAPI application."""
    return TestClient(app)


def test_health_check_endpoint(client):
    """Verify /health returns 200, HEALTHY status, and version."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["version"] == "1.0.0"
    assert "database" in data
    assert data["dataset_status"] == "AVAILABLE"


def test_market_overview_endpoint(client):
    """Verify /api/market/overview returns macro metrics and valid distributions."""
    response = client.get("/api/market/overview")
    assert response.status_code == 200
    data = response.json()

    assert data["total_job_postings"] == 30250
    assert data["total_unique_companies"] == 16
    assert data["total_job_roles"] == 12
    assert data["total_cities"] == 16
    assert "Full-time" in data["employment_type_distribution"]
    assert "On-site" in data["work_mode_distribution"]


def test_job_roles_endpoint(client):
    """Verify /api/market/job-roles with query limit parameter."""
    response = client.get("/api/market/job-roles?limit=5")
    assert response.status_code == 200
    data = response.json()

    assert data["total_roles"] == 12
    assert len(data["top_roles"]) == 5
    assert data["top_roles"][0]["rank"] == 1
    assert data["top_roles"][0]["job_count"] > 0


def test_cities_endpoint(client):
    """Verify /api/market/cities with query limit parameter."""
    response = client.get("/api/market/cities?limit=8")
    assert response.status_code == 200
    data = response.json()

    assert data["total_cities"] == 16
    assert len(data["top_cities"]) == 8
    assert len(data["state_distribution"]) > 0


def test_skills_endpoint(client):
    """Verify /api/market/skills returns top skills and co-occurrences."""
    response = client.get("/api/market/skills?top_n=15")
    assert response.status_code == 200
    data = response.json()

    assert data["total_skills_returned"] == 15
    assert len(data["top_skills"]) == 15
    assert len(data["co_occurring_skills"]) > 0


def test_salary_endpoint(client):
    """Verify /api/market/salary returns verified compensation statistics."""
    response = client.get("/api/market/salary")
    assert response.status_code == 200
    data = response.json()

    assert data["target_metric"] == "salary_mid_lpa (INR LPA)"
    assert data["salary_range_analysis"]["total_salary_records"] == 17559
    assert len(data["median_salary_by_role"]) == 12
    assert len(data["top_paying_roles"]) == 12


def test_trends_endpoint(client):
    """Verify /api/market/trends returns monthly and quarterly buckets."""
    response = client.get("/api/market/trends")
    assert response.status_code == 200
    data = response.json()

    assert len(data["monthly_postings"]) > 0
    assert len(data["quarterly_postings"]) > 0
    assert "simulated" in data["data_limitation_note"].lower() or "synthetic" in data["data_limitation_note"].lower()


def test_single_role_dossier_valid_and_invalid(client):
    """Verify GET /api/market/role/{job_role} for valid role and 404 for invalid."""
    # Valid role
    res_valid = client.get("/api/market/role/Data Scientist")
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["job_role"] == "Data Scientist"
    assert data["total_postings"] > 0
    assert data["salary_stats"]["median_lpa"] > 0

    # Invalid role
    res_invalid = client.get("/api/market/role/Quantum Alchemist")
    assert res_invalid.status_code == 404
    assert "not found" in res_invalid.json()["detail"].lower()


def test_single_city_dossier_valid_and_invalid(client):
    """Verify GET /api/market/city/{city} for valid city and 404 for invalid."""
    # Valid city
    res_valid = client.get("/api/market/city/Bengaluru")
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["city"] == "Bengaluru"
    assert data["total_postings"] > 0

    # Invalid city
    res_invalid = client.get("/api/market/city/Atlantis")
    assert res_invalid.status_code == 404
    assert "not found" in res_invalid.json()["detail"].lower()

