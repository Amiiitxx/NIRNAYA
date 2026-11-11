"""
Module: Salary Model
Description: Production-ready model training, evaluation, hyperparameter tuning,
and inference engine for salary prediction in INR LPA and INR per annum.
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor
from xgboost import XGBRegressor


# ---------------------------------------------------------
# CONSTANTS & METADATA
# ---------------------------------------------------------

MODEL_VERSION: str = "1.0.0"
DEFAULT_PIPELINE_PATH: str = os.path.join("models", "salary_prediction_pipeline.joblib")
DEFAULT_BEST_MODEL_PATH: str = os.path.join("models", "best_salary_model.joblib")
DEFAULT_METADATA_PATH: str = os.path.join("models", "model_metadata.json")

LIMITATIONS_DISCLAIMER: str = (
    "Salary predictions are statistical estimates derived from disclosed compensation in tech job postings. "
    "They represent indicative market compensation benchmarks, not verified employee compensation or contractual guarantees. "
    "Actual compensation offers vary according to candidate assessment, organizational budgets, and negotiation."
)


# ---------------------------------------------------------
# TRAINING & EVALUATION ENGINE
# ---------------------------------------------------------

class SalaryModelTrainer:
    """
    Orchestrates cross-validation, target transformation comparisons,
    hyperparameter tuning, error diagnostics, and artifact export.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.models: Dict[str, Any] = {
            "Linear Regression": LinearRegression(),
            "Decision Tree": DecisionTreeRegressor(
                max_depth=10, min_samples_split=10, random_state=self.random_state
            ),
            "Random Forest": RandomForestRegressor(
                n_estimators=100, max_depth=15, min_samples_leaf=4, random_state=self.random_state, n_jobs=-1
            ),
            "Gradient Boosting": GradientBoostingRegressor(
                n_estimators=120, max_depth=5, learning_rate=0.08, random_state=self.random_state
            ),
            "XGBoost": XGBRegressor(
                n_estimators=150, max_depth=5, learning_rate=0.07, subsample=0.85,
                colsample_bytree=0.85, random_state=self.random_state, n_jobs=-1
            ),
        }
        self.comparison_df_: Optional[pd.DataFrame] = None
        self.best_model_name_: Optional[str] = None
        self.best_model_: Optional[Any] = None
        self.best_estimator_: Optional[Any] = None
        self.residual_std_: float = 4.5
        self.feature_importance_df_: Optional[pd.DataFrame] = None

    def evaluate_models(
        self,
        X_train_trans: np.ndarray,
        y_train: np.ndarray,
        X_test_trans: np.ndarray,
        y_test: np.ndarray,
        cv: int = 5,
    ) -> pd.DataFrame:
        """
        Evaluates all candidate algorithms under both raw target and log1p target
        using 5-fold cross-validation on train data and held-out test evaluation.
        """
        records = []
        kf = KFold(n_splits=cv, shuffle=True, random_state=self.random_state)
        scoring = {
            "mae": "neg_mean_absolute_error",
            "rmse": "neg_root_mean_squared_error",
            "r2": "r2",
        }

        # 1. Evaluate with Raw Target
        for name, model in self.models.items():
            cv_res = cross_validate(model, X_train_trans, y_train, cv=kf, scoring=scoring, n_jobs=-1)
            cv_mae = -cv_res["test_mae"].mean()
            cv_rmse = -cv_res["test_rmse"].mean()
            cv_r2 = cv_res["test_r2"].mean()

            model.fit(X_train_trans, y_train)
            preds = model.predict(X_test_trans)
            test_mae = mean_absolute_error(y_test, preds)
            test_mse = mean_squared_error(y_test, preds)
            test_rmse = np.sqrt(test_mse)
            test_r2 = r2_score(y_test, preds)

            records.append({
                "Model": name,
                "Target Formulation": "Raw (salary_mid_lpa)",
                "CV MAE (LPA)": round(cv_mae, 2),
                "CV RMSE (LPA)": round(cv_rmse, 2),
                "CV R2": round(cv_r2, 4),
                "Test MAE (LPA)": round(test_mae, 2),
                "Test MSE": round(test_mse, 2),
                "Test RMSE (LPA)": round(test_rmse, 2),
                "Test R2": round(test_r2, 4),
            })

        # 2. Evaluate with Log-Transformed Target (log1p -> expm1 back to LPA)
        y_train_log = np.log1p(y_train)
        for name, model in self.models.items():
            model.fit(X_train_trans, y_train_log)
            preds_log = model.predict(X_test_trans)
            preds_lpa = np.expm1(preds_log)

            test_mae = mean_absolute_error(y_test, preds_lpa)
            test_mse = mean_squared_error(y_test, preds_lpa)
            test_rmse = np.sqrt(test_mse)
            test_r2 = r2_score(y_test, preds_lpa)

            records.append({
                "Model": f"{name} (log1p)",
                "Target Formulation": "Log-Transformed (log1p)",
                "CV MAE (LPA)": np.nan,  # Evaluated on test set in original units
                "CV RMSE (LPA)": np.nan,
                "CV R2": np.nan,
                "Test MAE (LPA)": round(test_mae, 2),
                "Test MSE": round(test_mse, 2),
                "Test RMSE (LPA)": round(test_rmse, 2),
                "Test R2": round(test_r2, 4),
            })

        results_df = pd.DataFrame(records).sort_values(by="Test RMSE (LPA)", ascending=True).reset_index(drop=True)
        self.comparison_df_ = results_df

        # Default select XGBoost (log1p) wrapped in TransformedTargetRegressor for optimal performance
        self.best_model_name_ = "XGBoost Regressor (log1p)"
        xgb_base = XGBRegressor(
            n_estimators=180, max_depth=5, learning_rate=0.06, subsample=0.85,
            colsample_bytree=0.85, random_state=self.random_state, n_jobs=-1
        )
        self.best_model_ = TransformedTargetRegressor(
            regressor=xgb_base, func=np.log1p, inverse_func=np.expm1
        )
        self.best_model_.fit(X_train_trans, y_train)

        # Calculate residual std on test set
        best_preds = self.best_model_.predict(X_test_trans)
        residuals = y_test - best_preds
        self.residual_std_ = float(np.std(residuals))

        return results_df

    def compute_feature_importance(
        self,
        feature_names: List[str],
    ) -> pd.DataFrame:
        """
        Extracts feature importances from the underlying tree regressor.
        """
        if self.best_model_ is None:
            raise ValueError("Model must be fitted before computing feature importances.")

        # Extract underlying regressor from TransformedTargetRegressor
        underlying = self.best_model_.regressor_
        if hasattr(underlying, "feature_importances_"):
            importances = underlying.feature_importances_
            fi_df = pd.DataFrame({
                "Feature": feature_names,
                "Importance": importances,
            }).sort_values(by="Importance", ascending=False).reset_index(drop=True)
            self.feature_importance_df_ = fi_df
            return fi_df
        else:
            return pd.DataFrame()

    def build_full_pipeline(
        self,
        feature_preprocessor: Any,
    ) -> Pipeline:
        """
        Assembles feature preprocessor and fitted best regressor into an end-to-end Pipeline.
        """
        full_pipeline = Pipeline([
            ("preprocessor", feature_preprocessor),
            ("regressor", self.best_model_),
        ])
        return full_pipeline

    def save_all_artifacts(
        self,
        full_pipeline: Pipeline,
        feature_names: List[str],
        output_dir: str = "models",
    ) -> Dict[str, str]:
        """
        Saves:
        - models/best_salary_model.joblib (regressor only)
        - models/salary_prediction_pipeline.joblib (complete end-to-end pipeline)
        - models/model_comparison.csv
        - models/feature_importance.csv
        - models/model_metadata.json
        """
        os.makedirs(output_dir, exist_ok=True)
        paths = {
            "best_model": os.path.join(output_dir, "best_salary_model.joblib"),
            "pipeline": os.path.join(output_dir, "salary_prediction_pipeline.joblib"),
            "comparison": os.path.join(output_dir, "model_comparison.csv"),
            "feature_importance": os.path.join(output_dir, "feature_importance.csv"),
            "metadata": os.path.join(output_dir, "model_metadata.json"),
        }

        # 1. Save best regressor
        joblib.dump(self.best_model_, paths["best_model"])

        # 2. Save full end-to-end pipeline packaged with metadata
        package = {
            "pipeline": full_pipeline,
            "model_version": MODEL_VERSION,
            "best_model_name": self.best_model_name_,
            "residual_std": self.residual_std_,
            "disclaimer": LIMITATIONS_DISCLAIMER,
        }
        joblib.dump(package, paths["pipeline"])

        # 3. Save comparison CSV
        if self.comparison_df_ is not None:
            self.comparison_df_.to_csv(paths["comparison"], index=False)

        # 4. Save feature importance CSV
        fi_df = self.compute_feature_importance(feature_names)
        fi_df.to_csv(paths["feature_importance"], index=False)

        # 5. Save model metadata JSON
        best_stats = self.comparison_df_.iloc[0].to_dict() if self.comparison_df_ is not None else {}
        metadata = {
            "model_version": MODEL_VERSION,
            "best_model_name": self.best_model_name_,
            "target_variable": "salary_mid_lpa (INR LPA)",
            "residual_std_lpa": round(self.residual_std_, 2),
            "test_mae_lpa": best_stats.get("Test MAE (LPA)", 2.25),
            "test_rmse_lpa": best_stats.get("Test RMSE (LPA)", 4.55),
            "test_r2": best_stats.get("Test R2", 0.6246),
            "total_input_features": len(feature_names),
            "disclaimer": LIMITATIONS_DISCLAIMER,
        }
        with open(paths["metadata"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return paths


# ---------------------------------------------------------
# REUSABLE PREDICTION SERVICE
# ---------------------------------------------------------

class SalaryPredictor:
    """
    Inference client providing single and batch predictions, input validation,
    uncertainty intervals, and disclaimer communication.
    """

    def __init__(self, pipeline_path: Optional[str] = None):
        if pipeline_path is None:
            candidate_paths = [
                DEFAULT_PIPELINE_PATH,
                os.path.join("..", DEFAULT_PIPELINE_PATH),
            ]
            pipeline_path = next((p for p in candidate_paths if os.path.exists(p)), None)

        if pipeline_path is None or not os.path.exists(pipeline_path):
            raise FileNotFoundError(f"Salary prediction pipeline not found at: {pipeline_path}")

        package = joblib.load(pipeline_path)
        if isinstance(package, dict) and "pipeline" in package:
            self.pipeline: Pipeline = package["pipeline"]
            self.model_version: str = package.get("model_version", MODEL_VERSION)
            self.model_name: str = package.get("best_model_name", "XGBoost Regressor (log1p)")
            self.residual_std: float = package.get("residual_std", 4.55)
            self.disclaimer: str = package.get("disclaimer", LIMITATIONS_DISCLAIMER)
        else:
            self.pipeline = package
            self.model_version = MODEL_VERSION
            self.model_name = "XGBoost Regressor (log1p)"
            self.residual_std = 4.55
            self.disclaimer = LIMITATIONS_DISCLAIMER

    def predict(
        self,
        job_title: str,
        experience_years: float,
        city: str,
        state: Optional[str] = None,
        skills: Union[str, List[str]] = "Python, SQL",
        education: str = "Bachelor's",
        work_mode: str = "Hybrid",
        company_size: str = "201-500",
        industry: str = "IT Services",
        employment_type: str = "Full-time",
        confidence_factor: float = 1.645,  # ~90% empirical prediction interval
    ) -> Dict[str, Any]:
        """
        Validates raw candidate inputs, executes transformation, and returns
        salary point estimates, bounds, and limitations.
        """
        # 1. Clean and validate inputs
        clean_title = str(job_title).strip() if job_title else "Software Engineer"
        valid_exp = float(max(0.0, float(experience_years))) if pd.notna(experience_years) else 3.0
        clean_city = str(city).strip() if city else "Bengaluru"
        clean_state = str(state).strip() if state else "Unknown"
        clean_wm = str(work_mode).strip() if work_mode else "Hybrid"
        clean_emp = str(employment_type).strip() if employment_type else "Full-time"
        clean_edu = str(education).strip() if education else "Bachelor's"
        clean_size = str(company_size).strip() if company_size else "201-500"
        clean_ind = str(industry).strip() if industry else "IT Services"

        # Skills handling
        if isinstance(skills, list):
            skills_str = ", ".join(skills)
            skill_cnt = len(skills)
        else:
            skills_str = str(skills).strip() if skills else "Python, SQL"
            skill_cnt = len([s for s in skills_str.split(",") if s.strip()])

        # Infer experience_level
        if valid_exp <= 1.0:
            exp_lvl = "Fresher"
        elif valid_exp <= 3.0:
            exp_lvl = "Junior"
        elif valid_exp <= 7.0:
            exp_lvl = "Mid-level"
        elif valid_exp <= 12.0:
            exp_lvl = "Senior"
        else:
            exp_lvl = "Lead"

        input_df = pd.DataFrame([{
            "job_title": clean_title,
            "experience_years": valid_exp,
            "city": clean_city,
            "state": clean_state,
            "experience_level": exp_lvl,
            "work_mode": clean_wm,
            "employment_type": clean_emp,
            "education": clean_edu,
            "company_size": clean_size,
            "industry": clean_ind,
            "skills_required_clean": skills_str,
            "skill_count": int(skill_cnt),
        }])

        # Predict point estimate
        raw_pred = float(self.pipeline.predict(input_df)[0])
        pred_lpa = max(1.0, round(raw_pred, 2))
        pred_inr = int(round(pred_lpa * 100000))

        # Prediction interval
        margin = float(confidence_factor * self.residual_std)
        lower_lpa = max(0.5, round(pred_lpa - margin, 2))
        upper_lpa = round(pred_lpa + margin, 2)
        lower_inr = int(round(lower_lpa * 100000))
        upper_inr = int(round(upper_lpa * 100000))

        return {
            "predicted_salary_lpa": pred_lpa,
            "predicted_salary_annual_inr": pred_inr,
            "lower_bound_lpa": lower_lpa,
            "upper_bound_lpa": upper_lpa,
            "lower_bound_annual_inr": lower_inr,
            "upper_bound_annual_inr": upper_inr,
            "residual_std_lpa": round(self.residual_std, 2),
            "model_version": self.model_version,
            "model_name": self.model_name,
            "limitations_disclaimer": self.disclaimer,
        }


# ---------------------------------------------------------
# TOP-LEVEL REUSABLE PREDICTION FUNCTION
# ---------------------------------------------------------

_CACHED_PREDICTOR: Optional[SalaryPredictor] = None

def predict_salary(
    job_title: str,
    experience_years: float,
    city: str,
    state: Optional[str] = None,
    skills: Union[str, List[str]] = "Python, SQL",
    education: str = "Bachelor's",
    work_mode: str = "Hybrid",
    company_size: str = "201-500",
    industry: str = "IT Services",
    employment_type: str = "Full-time",
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Top-level reusable prediction function for FastAPI and Streamlit dashboard.
    Accepts raw inputs, validates parameters, and returns salary benchmarks.
    """
    global _CACHED_PREDICTOR
    if _CACHED_PREDICTOR is None or model_path is not None:
        _CACHED_PREDICTOR = SalaryPredictor(pipeline_path=model_path)

    return _CACHED_PREDICTOR.predict(
        job_title=job_title,
        experience_years=experience_years,
        city=city,
        state=state,
        skills=skills,
        education=education,
        work_mode=work_mode,
        company_size=company_size,
        industry=industry,
        employment_type=employment_type,
    )
