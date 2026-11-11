"""
Module: Feature Engineering
Description: Modular feature transformation, encoding pipelines, skills binarization,
and reproducible dataset splitting for salary regression modeling.
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------
# CONSTANTS & COLUMN SPECIFICATIONS
# ---------------------------------------------------------

LEAKAGE_COLUMNS: List[str] = [
    "salary_min_lpa",
    "salary_max_lpa",
    "salary_annual_inr",
    "is_salary_valid",
    "salary_mid_lpa",
]

UNINFORMATIVE_COLUMNS: List[str] = [
    "job_id",
    "job_url",
    "data_source",
    "salary_currency",
    "job_description",
    "skills_required",
    "posted_date",
    "posted_date_dt",
]

NUMERICAL_FEATURES: List[str] = [
    "experience_years",
    "skill_count",
]

CATEGORICAL_FEATURES: List[str] = [
    "job_title",
    "city",
    "state",
    "experience_level",
    "work_mode",
    "employment_type",
    "education",
    "company_size",
    "industry",
]

SKILL_COLUMN: str = "skills_required_clean"
DEFAULT_TARGET_COLUMN: str = "salary_mid_lpa"


# ---------------------------------------------------------
# CUSTOM TRANSFORMERS
# ---------------------------------------------------------

class SkillsBinarizer(BaseEstimator, TransformerMixin):
    """
    Learns the top N most frequent technical skills from the training data
    and transforms comma-separated skills strings into multi-hot binary indicator features.
    Prevents data leakage by fitting exclusively on training samples.
    """

    def __init__(self, top_n: int = 25):
        self.top_n = top_n
        self.top_skills_: List[str] = []

    def fit(self, X: Union[pd.DataFrame, pd.Series, np.ndarray], y=None):
        if isinstance(X, pd.DataFrame):
            series = X.iloc[:, 0]
        elif isinstance(X, pd.Series):
            series = X
        else:
            series = pd.Series(np.array(X).ravel())

        all_skills: List[str] = []
        for val in series.dropna():
            toks = [t.strip() for t in str(val).split(",") if t.strip()]
            all_skills.extend(toks)

        counts = pd.Series(all_skills).value_counts()
        self.top_skills_ = counts.head(self.top_n).index.tolist()
        return self

    def transform(self, X: Union[pd.DataFrame, pd.Series, np.ndarray]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            series = X.iloc[:, 0]
        elif isinstance(X, pd.Series):
            series = X
        else:
            series = pd.Series(np.array(X).ravel())

        output_matrix = np.zeros((len(series), len(self.top_skills_)), dtype=np.float64)
        for i, val in enumerate(series):
            if pd.isna(val):
                continue
            skills_in_posting = set(t.strip() for t in str(val).split(",") if t.strip())
            for j, target_skill in enumerate(self.top_skills_):
                if target_skill in skills_in_posting:
                    output_matrix[i, j] = 1.0

        return output_matrix

    def get_feature_names_out(self, input_features=None) -> np.ndarray:
        clean_names = [f"skill_{s.lower().replace(' ', '_').replace('-', '_')}" for s in self.top_skills_]
        return np.array(clean_names)


# ---------------------------------------------------------
# PIPELINE BUILDER
# ---------------------------------------------------------

def build_feature_pipeline(
    numerical_cols: Optional[List[str]] = None,
    categorical_cols: Optional[List[str]] = None,
    skill_col: str = SKILL_COLUMN,
    top_n_skills: int = 25,
) -> ColumnTransformer:
    """
    Constructs a ColumnTransformer assembling:
    - Numerical Pipeline: Median imputation + StandardScaler
    - Categorical Pipeline: Constant imputation ('Unknown') + OneHotEncoder (handle_unknown='ignore')
    - Skills Pipeline: Custom SkillsBinarizer (learning top N skills from training set)
    """
    num_cols = numerical_cols if numerical_cols is not None else NUMERICAL_FEATURES
    cat_cols = categorical_cols if categorical_cols is not None else CATEGORICAL_FEATURES

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    skills_pipeline = Pipeline([
        ("binarizer", SkillsBinarizer(top_n=top_n_skills)),
    ])

    transformer = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, num_cols),
            ("cat", cat_pipeline, cat_cols),
            ("skills", skills_pipeline, [skill_col]),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )

    return transformer


# ---------------------------------------------------------
# DATA SPLITTING & PREPARATION ROUTINES
# ---------------------------------------------------------

def prepare_features_and_target(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COLUMN,
    use_log_target: bool = False,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extracts predictor features X and target y, strictly excluding all target-leakage
    and uninformative identifier fields.
    """
    if target_col not in df.columns:
        raise KeyError(f"Target column '{target_col}' not found in dataframe.")

    # Target variable
    y = df[target_col].copy()
    if use_log_target:
        y = np.log1p(y)

    # Exclude all leakage and uninformative columns
    cols_to_exclude = set(LEAKAGE_COLUMNS + UNINFORMATIVE_COLUMNS)
    feature_cols = [c for c in df.columns if c not in cols_to_exclude]

    X = df[feature_cols].copy()
    return X, y


def split_dataset(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Performs reproducible random train/test split.
    """
    return train_test_split(X, y, test_size=test_size, random_state=random_state)


def temporal_split_dataset(
    df: pd.DataFrame,
    date_col: str = "posted_date_dt",
    cutoff_date: str = "2026-01-01",
    target_col: str = DEFAULT_TARGET_COLUMN,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Performs out-of-time evaluation split (train on listings before cutoff, test on or after).
    """
    dates = pd.to_datetime(df[date_col], errors="coerce")
    train_mask = dates < pd.to_datetime(cutoff_date)
    test_mask = dates >= pd.to_datetime(cutoff_date)

    X, y = prepare_features_and_target(df, target_col=target_col)
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    return X_train, X_test, y_train, y_test


# ---------------------------------------------------------
# SERIALIZATION & EXPORT
# ---------------------------------------------------------

def fit_and_save_pipeline(
    pipeline: ColumnTransformer,
    X_train: pd.DataFrame,
    output_dir: str = "models",
) -> Tuple[ColumnTransformer, str, str]:
    """
    Fits the preprocessing pipeline ONLY on training data, extracts learned feature names,
    and serializes the pipeline and metadata to disk.
    """
    os.makedirs(output_dir, exist_ok=True)
    pipeline.fit(X_train)

    feature_names = pipeline.get_feature_names_out().tolist()

    # Extract learned skills from the skills binarizer
    skills_step = pipeline.named_transformers_["skills"]
    learned_skills = skills_step.named_steps["binarizer"].top_skills_

    metadata = {
        "total_transformed_features": len(feature_names),
        "numerical_features": NUMERICAL_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "top_skills_learned": learned_skills,
        "feature_names": feature_names,
    }

    pipeline_path = os.path.join(output_dir, "feature_pipeline.joblib")
    metadata_path = os.path.join(output_dir, "feature_metadata.json")

    joblib.dump(pipeline, pipeline_path)
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return pipeline, pipeline_path, metadata_path


def save_train_test_data(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
    output_dir: str = "data/processed",
) -> Dict[str, str]:
    """Save train and test splits to disk."""
    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "X_train": os.path.join(output_dir, "X_train.csv"),
        "X_test": os.path.join(output_dir, "X_test.csv"),
        "y_train": os.path.join(output_dir, "y_train.csv"),
        "y_test": os.path.join(output_dir, "y_test.csv"),
    }

    X_train.to_csv(paths["X_train"], index=False)
    X_test.to_csv(paths["X_test"], index=False)
    y_train.to_csv(paths["y_train"], index=False)
    y_test.to_csv(paths["y_test"], index=False)

    return paths


if __name__ == "__main__":
    df_sal = pd.read_csv("data/processed/cleaned_salary_model_data.csv")
    X, y = prepare_features_and_target(df_sal)
    X_train, X_test, y_train, y_test = split_dataset(X, y)
    pipe = build_feature_pipeline()
    fit_and_save_pipeline(pipe, X_train)
    save_train_test_data(X_train, X_test, y_train, y_test)
    print(f"Feature engineering pipeline executed. X_train: {X_train.shape}, X_test: {X_test.shape}")
