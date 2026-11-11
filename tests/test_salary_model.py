"""
Unit tests for Module 2: Salary Prediction Model & Inference Service
Tests verify pipeline persistence, metadata schema, prediction mechanics,
uncertainty interval bounds, and robustness to edge-case inputs.
"""

import json
import os
import pytest
import pandas as pd
import numpy as np

from src.salary_model import SalaryPredictor, predict_salary, LIMITATIONS_DISCLAIMER


MODELS_DIR = "models"
FIGURES_DIR = os.path.join("reports", "figures", "model_evaluation")


def test_pipeline_artifacts_exist():
    """Verify that all required model and evaluation artifacts exist on disk."""
    required_files = [
        os.path.join(MODELS_DIR, "best_salary_model.joblib"),
        os.path.join(MODELS_DIR, "salary_prediction_pipeline.joblib"),
        os.path.join(MODELS_DIR, "model_comparison.csv"),
        os.path.join(MODELS_DIR, "feature_importance.csv"),
        os.path.join(MODELS_DIR, "model_metadata.json"),
    ]
    for file_path in required_files:
        assert os.path.exists(file_path), f"Artifact missing: {file_path}"
        assert os.path.getsize(file_path) > 0, f"Artifact is empty: {file_path}"


def test_model_metadata_schema_and_values():
    """Verify metadata json schema, performance metrics, and governance disclaimer."""
    meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    required_keys = [
        "model_version",
        "best_model_name",
        "target_variable",
        "test_mae_lpa",
        "test_rmse_lpa",
        "test_r2",
        "residual_std_lpa",
        "total_training_samples",
        "total_test_samples",
        "total_features",
        "best_hyperparameters",
        "disclaimer",
    ]
    for key in required_keys:
        assert key in meta, f"Metadata key missing: {key}"

    assert meta["test_mae_lpa"] <= 3.0, f"Test MAE too high: {meta['test_mae_lpa']}"
    assert meta["test_r2"] >= 0.55, f"Test R2 too low: {meta['test_r2']}"
    assert meta["total_features"] == 113, f"Unexpected feature count: {meta['total_features']}"
    assert "statistical estimates" in meta["disclaimer"].lower()


def test_model_comparison_table():
    """Verify model comparison table contains all algorithms and log1p comparisons."""
    comp_path = os.path.join(MODELS_DIR, "model_comparison.csv")
    df_comp = pd.read_csv(comp_path)
    assert len(df_comp) == 10, f"Expected 10 candidate evaluations, found {len(df_comp)}"
    assert "XGBoost (log1p)" in df_comp["Model"].values
    assert "Linear Regression" in df_comp["Model"].values
    assert "Test MAE (LPA)" in df_comp.columns
    assert "Test RMSE (LPA)" in df_comp.columns
    assert "Test R2" in df_comp.columns


def test_feature_importance_contents():
    """Verify feature importances are extracted and experience/roles feature prominently."""
    fi_path = os.path.join(MODELS_DIR, "feature_importance.csv")
    df_fi = pd.read_csv(fi_path)
    assert "Feature" in df_fi.columns
    assert "Importance" in df_fi.columns
    assert len(df_fi) == 113

    # Check top features
    top_features = df_fi.head(10)["Feature"].tolist()
    assert any("experience" in feat for feat in top_features), "Experience not in top 10 features"


def test_salary_predictor_initialization():
    """Verify SalaryPredictor initializes and loads the production pipeline."""
    predictor = SalaryPredictor()
    assert predictor.pipeline is not None
    assert predictor.residual_std > 0
    assert predictor.model_version == "1.0.0"


def test_predict_single_candidate():
    """Verify end-to-end inference for a typical candidate profile."""
    predictor = SalaryPredictor()
    res = predictor.predict(
        job_title="Data Scientist",
        experience_years=4.5,
        city="Bengaluru",
        skills=["Python", "SQL", "Machine Learning", "AWS"],
        education="Bachelor's",
        work_mode="Hybrid",
        company_size="501-1000",
        industry="IT Services",
        employment_type="Full-time",
    )

    expected_keys = [
        "predicted_salary_lpa",
        "predicted_salary_annual_inr",
        "lower_bound_lpa",
        "upper_bound_lpa",
        "lower_bound_annual_inr",
        "upper_bound_annual_inr",
        "residual_std_lpa",
        "model_version",
        "model_name",
        "limitations_disclaimer",
    ]
    for key in expected_keys:
        assert key in res, f"Result missing key: {key}"

    assert res["predicted_salary_lpa"] > 0
    assert res["lower_bound_lpa"] <= res["predicted_salary_lpa"] <= res["upper_bound_lpa"]
    assert res["lower_bound_annual_inr"] <= res["predicted_salary_annual_inr"] <= res["upper_bound_annual_inr"]
    assert res["predicted_salary_annual_inr"] == int(round(res["predicted_salary_lpa"] * 100000))


def test_monotonicity_experience_tiers():
    """Verify that seniority tiers exhibit monotonically higher predicted compensation."""
    predictor = SalaryPredictor()
    fresher = predictor.predict(
        job_title="Software Engineer",
        experience_years=0.5,
        city="Bengaluru",
        skills="Python, Git",
    )
    mid = predictor.predict(
        job_title="Software Engineer",
        experience_years=5.0,
        city="Bengaluru",
        skills="Python, Git, Docker, SQL",
    )
    lead = predictor.predict(
        job_title="Software Engineer",
        experience_years=13.0,
        city="Bengaluru",
        skills="Python, Git, Docker, SQL, Kubernetes, System Design",
    )

    assert fresher["predicted_salary_lpa"] < mid["predicted_salary_lpa"]
    assert mid["predicted_salary_lpa"] < lead["predicted_salary_lpa"]


def test_predict_salary_top_level_function():
    """Verify top-level predict_salary function with various input formats."""
    res_str = predict_salary(
        job_title="Machine Learning Engineer",
        experience_years=3.0,
        city="Hyderabad",
        skills="Python, PyTorch, Docker",
    )
    assert res_str["predicted_salary_lpa"] > 0

    res_list = predict_salary(
        job_title="Machine Learning Engineer",
        experience_years=3.0,
        city="Hyderabad",
        skills=["Python", "PyTorch", "Docker"],
    )
    assert res_list["predicted_salary_lpa"] > 0


def test_robustness_unseen_and_edge_inputs():
    """Verify pipeline handles unknown categories and extreme numerical inputs safely."""
    res_edge = predict_salary(
        job_title="Chief Quantum Computing Alchemist",  # completely unknown
        experience_years=-5.0,  # negative experience clamped to 0.0
        city="Atlantis",  # unknown city
        skills="",  # empty skills
    )
    assert res_edge["predicted_salary_lpa"] >= 1.0
    assert res_edge["lower_bound_lpa"] >= 0.5


def test_evaluation_figures_exist():
    """Verify all 8 required evaluation figures are saved and non-empty."""
    figures = [
        "actual_vs_predicted.png",
        "residual_distribution.png",
        "residuals_vs_predicted.png",
        "model_performance_comparison.png",
        "feature_importance.png",
        "cross_validation_performance.png",
        "prediction_errors_by_job_role.png",
        "prediction_errors_by_experience_level.png",
    ]
    for fig in figures:
        fig_path = os.path.join(FIGURES_DIR, fig)
        assert os.path.exists(fig_path), f"Figure missing: {fig_path}"
        assert os.path.getsize(fig_path) > 1000, f"Figure file too small/empty: {fig_path}"

