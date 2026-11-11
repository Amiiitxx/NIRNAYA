"""
Training and Evaluation execution script.
Benchmarking models, tuning hyperparameters, generating 8 diagnostic figures,
and saving all models and metadata artifacts.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, RandomizedSearchCV, cross_val_score, cross_validate
from sklearn.pipeline import Pipeline
from xgboost import XGBRegressor

# Directories
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

DATA_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "reports", "figures", "model_evaluation")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

print("Starting Model Training & Evaluation Benchmark...")

# 1. Load Data
X_train = pd.read_csv(os.path.join(DATA_DIR, "X_train.csv"))
X_test = pd.read_csv(os.path.join(DATA_DIR, "X_test.csv"))
y_train = pd.read_csv(os.path.join(DATA_DIR, "y_train.csv"))["salary_mid_lpa"].values
y_test = pd.read_csv(os.path.join(DATA_DIR, "y_test.csv"))["salary_mid_lpa"].values

feature_pipeline = joblib.load(os.path.join(MODELS_DIR, "feature_pipeline.joblib"))

print(f"X_train shape: {X_train.shape}, X_test shape: {X_test.shape}")
print(f"y_train shape: {y_train.shape}, y_test shape: {y_test.shape}")

# Transform features
X_train_trans = feature_pipeline.transform(X_train)
X_test_trans = feature_pipeline.transform(X_test)
if hasattr(X_train_trans, "toarray"):
    X_train_trans = X_train_trans.toarray()
    X_test_trans = X_test_trans.toarray()

print(f"Transformed X_train shape: {X_train_trans.shape}")
print(f"Transformed X_test shape: {X_test_trans.shape}")

# Feature names
with open(os.path.join(MODELS_DIR, "feature_metadata.json"), "r") as f:
    feat_meta = json.load(f)
feature_names = feat_meta["feature_names"]
print(f"Total feature names: {len(feature_names)}")

# 2. Define Algorithms
base_models = {
    "Linear Regression": LinearRegression(),
    "Decision Tree": DecisionTreeRegressor(max_depth=10, min_samples_split=10, random_state=42),
    "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=15, min_samples_leaf=4, random_state=42, n_jobs=-1),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=120, max_depth=5, learning_rate=0.08, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=150, max_depth=5, learning_rate=0.07, subsample=0.85, colsample_bytree=0.85, random_state=42, n_jobs=-1),
}

# 3. Model Benchmark (Raw vs Log1p)
kf = KFold(n_splits=5, shuffle=True, random_state=42)
scoring = {
    "mae": "neg_mean_absolute_error",
    "rmse": "neg_root_mean_squared_error",
    "r2": "r2",
}

comparison_records = []
cv_scores_dict = {}

# Raw target evaluation
for name, model in base_models.items():
    print(f"Evaluating {name} (Raw target)...")
    cv_res = cross_validate(model, X_train_trans, y_train, cv=kf, scoring=scoring, n_jobs=-1)
    cv_mae = -cv_res["test_mae"].mean()
    cv_rmse = -cv_res["test_rmse"].mean()
    cv_r2 = cv_res["test_r2"].mean()
    cv_scores_dict[f"{name} (Raw)"] = -cv_res["test_mae"]

    model.fit(X_train_trans, y_train)
    preds = model.predict(X_test_trans)
    test_mae = mean_absolute_error(y_test, preds)
    test_mse = mean_squared_error(y_test, preds)
    test_rmse = np.sqrt(test_mse)
    test_r2 = r2_score(y_test, preds)

    comparison_records.append({
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

# Log-Transformed target evaluation (using TransformedTargetRegressor)
for name, model in base_models.items():
    print(f"Evaluating {name} (Log1p target)...")
    ttr = TransformedTargetRegressor(regressor=model, func=np.log1p, inverse_func=np.expm1)
    cv_res = cross_validate(ttr, X_train_trans, y_train, cv=kf, scoring=scoring, n_jobs=-1)
    cv_mae = -cv_res["test_mae"].mean()
    cv_rmse = -cv_res["test_rmse"].mean()
    cv_r2 = cv_res["test_r2"].mean()
    cv_scores_dict[f"{name} (log1p)"] = -cv_res["test_mae"]

    ttr.fit(X_train_trans, y_train)
    preds = ttr.predict(X_test_trans)
    test_mae = mean_absolute_error(y_test, preds)
    test_mse = mean_squared_error(y_test, preds)
    test_rmse = np.sqrt(test_mse)
    test_r2 = r2_score(y_test, preds)

    comparison_records.append({
        "Model": f"{name} (log1p)",
        "Target Formulation": "Log-Transformed (log1p)",
        "CV MAE (LPA)": round(cv_mae, 2),
        "CV RMSE (LPA)": round(cv_rmse, 2),
        "CV R2": round(cv_r2, 4),
        "Test MAE (LPA)": round(test_mae, 2),
        "Test MSE": round(test_mse, 2),
        "Test RMSE (LPA)": round(test_rmse, 2),
        "Test R2": round(test_r2, 4),
    })

comparison_df = pd.DataFrame(comparison_records).sort_values(by="Test RMSE (LPA)", ascending=True).reset_index(drop=True)
print("\n=== Model Comparison Table ===")
print(comparison_df.to_string())

# Save comparison table
comparison_df.to_csv(os.path.join(MODELS_DIR, "model_comparison.csv"), index=False)

# 4. Hyperparameter Tuning on XGBoost
print("\nStarting Hyperparameter Tuning on XGBoost (log1p)...")
param_distributions = {
    "regressor__n_estimators": [120, 160, 200, 250],
    "regressor__max_depth": [4, 5, 6, 7],
    "regressor__learning_rate": [0.03, 0.05, 0.08, 0.1],
    "regressor__subsample": [0.75, 0.85, 0.95],
    "regressor__colsample_bytree": [0.75, 0.85, 0.95],
    "regressor__min_child_weight": [1, 3, 5],
}

base_ttr_xgb = TransformedTargetRegressor(
    regressor=XGBRegressor(random_state=42, n_jobs=-1),
    func=np.log1p,
    inverse_func=np.expm1
)

random_search = RandomizedSearchCV(
    estimator=base_ttr_xgb,
    param_distributions=param_distributions,
    n_iter=15,
    scoring="neg_mean_absolute_error",
    cv=kf,
    random_state=42,
    n_jobs=-1,
    verbose=1
)

random_search.fit(X_train_trans, y_train)
best_tuned_model = random_search.best_estimator_
best_params = random_search.best_params_
print(f"Best Parameters: {best_params}")

# Test best tuned model
y_pred_tuned = best_tuned_model.predict(X_test_trans)
tuned_mae = mean_absolute_error(y_test, y_pred_tuned)
tuned_mse = mean_squared_error(y_test, y_pred_tuned)
tuned_rmse = np.sqrt(tuned_mse)
tuned_r2 = r2_score(y_test, y_pred_tuned)

print(f"\nTuned XGBoost Test Metrics:")
print(f"MAE: {tuned_mae:.2f} LPA | RMSE: {tuned_rmse:.2f} LPA | R2: {tuned_r2:.4f}")

# Residual std for uncertainty intervals
residuals = y_test - y_pred_tuned
residual_std = float(np.std(residuals))
print(f"Residual Std Dev: {residual_std:.2f} LPA")

# 5. Feature Importances
underlying_xgb = best_tuned_model.regressor_
importances = underlying_xgb.feature_importances_
fi_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importances
}).sort_values(by="Importance", ascending=False).reset_index(drop=True)

fi_df.to_csv(os.path.join(MODELS_DIR, "feature_importance.csv"), index=False)
print("\nTop 15 Most Important Features:")
print(fi_df.head(15).to_string())

# 6. Save Best Regressor and Full End-to-End Pipeline
joblib.dump(best_tuned_model, os.path.join(MODELS_DIR, "best_salary_model.joblib"))

full_pipeline = Pipeline([
    ("preprocessor", feature_pipeline),
    ("regressor", best_tuned_model)
])

package = {
    "pipeline": full_pipeline,
    "model_version": "1.0.0",
    "best_model_name": "Tuned XGBoost Regressor (log1p)",
    "residual_std": round(residual_std, 2),
    "best_params": {k.replace("regressor__", ""): v for k, v in best_params.items()},
    "disclaimer": (
        "Salary predictions are statistical estimates derived from disclosed compensation in tech job postings. "
        "They represent indicative market compensation benchmarks, not verified employee compensation or contractual guarantees. "
        "Actual compensation offers vary according to candidate assessment, organizational budgets, and negotiation."
    )
}
joblib.dump(package, os.path.join(MODELS_DIR, "salary_prediction_pipeline.joblib"))

# Save Model Metadata JSON
model_meta = {
    "model_version": "1.0.0",
    "best_model_name": "Tuned XGBoost Regressor (log1p)",
    "target_variable": "salary_mid_lpa (INR Lakhs Per Annum)",
    "test_mae_lpa": round(tuned_mae, 2),
    "test_mse": round(tuned_mse, 2),
    "test_rmse_lpa": round(tuned_rmse, 2),
    "test_r2": round(tuned_r2, 4),
    "residual_std_lpa": round(residual_std, 2),
    "empirical_confidence_multiplier_90pct": 1.645,
    "total_training_samples": len(y_train),
    "total_test_samples": len(y_test),
    "total_features": len(feature_names),
    "best_hyperparameters": {k.replace("regressor__", ""): v for k, v in best_params.items()},
    "disclaimer": package["disclaimer"]
}
with open(os.path.join(MODELS_DIR, "model_metadata.json"), "w") as f:
    json.dump(model_meta, f, indent=2)

print("\nAll model artifacts successfully serialized to models/.")

# 7. GENERATE ALL 8 REQUIRED FIGURES
print("\nGenerating 8 evaluation figures...")
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
palette = ["#1E3A8A", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD"]

# Figure 1: actual_vs_predicted.png
fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
ax.scatter(y_test, y_pred_tuned, alpha=0.35, color="#2563EB", edgecolors="none", s=25)
lims = [0, max(max(y_test), max(y_pred_tuned)) + 2]
ax.plot(lims, lims, color="#EF4444", linestyle="--", linewidth=2, label="Ideal Fit (y = x)")
ax.set_xlim(lims)
ax.set_ylim(lims)
ax.set_title("Actual vs. Predicted Salary (Test Set)", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Actual Salary (LPA)", fontsize=12)
ax.set_ylabel("Predicted Salary (LPA)", fontsize=12)
ax.legend(frameon=True, facecolor="white", loc="upper left")
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "actual_vs_predicted.png"))
plt.close(fig)

# Figure 2: residual_distribution.png
fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
sns.histplot(residuals, kde=True, color="#3B82F6", bins=45, ax=ax, edgecolor="white", alpha=0.6)
ax.axvline(0, color="#EF4444", linestyle="--", linewidth=1.5, label="Zero Error")
ax.axvline(np.mean(residuals), color="#10B981", linestyle=":", linewidth=2, label=f"Mean Residual ({np.mean(residuals):.2f})")
ax.set_title("Residual Error Distribution (Test Set)", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Residual (Actual - Predicted) [LPA]", fontsize=12)
ax.set_ylabel("Density / Frequency", fontsize=12)
ax.legend(frameon=True, facecolor="white")
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "residual_distribution.png"))
plt.close(fig)

# Figure 3: residuals_vs_predicted.png
fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
ax.scatter(y_pred_tuned, residuals, alpha=0.35, color="#8B5CF6", edgecolors="none", s=25)
ax.axhline(0, color="#EF4444", linestyle="--", linewidth=2, label="Zero Residual Line")
ax.axhline(1.645 * residual_std, color="#F59E0B", linestyle=":", linewidth=1.5, label=f"+1.645 Std (+{1.645*residual_std:.2f} LPA)")
ax.axhline(-1.645 * residual_std, color="#F59E0B", linestyle=":", linewidth=1.5, label=f"-1.645 Std (-{1.645*residual_std:.2f} LPA)")
ax.set_title("Residuals vs. Predicted Salary (Heteroscedasticity Analysis)", fontsize=14, fontweight="bold", pad=12)
ax.set_xlabel("Predicted Salary (LPA)", fontsize=12)
ax.set_ylabel("Residual (Actual - Predicted) [LPA]", fontsize=12)
ax.legend(frameon=True, facecolor="white", loc="upper right")
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "residuals_vs_predicted.png"))
plt.close(fig)

# Figure 4: model_performance_comparison.png
fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
comp_plot_df = comparison_df.sort_values(by="Test MAE (LPA)", ascending=True)
y_indices = np.arange(len(comp_plot_df))
bar_width = 0.38

ax.barh(y_indices - bar_width/2, comp_plot_df["Test MAE (LPA)"], height=bar_width, label="Test MAE (LPA)", color="#3B82F6", alpha=0.9)
ax.barh(y_indices + bar_width/2, comp_plot_df["Test RMSE (LPA)"], height=bar_width, label="Test RMSE (LPA)", color="#10B981", alpha=0.9)
ax.set_yticks(y_indices)
ax.set_yticklabels(comp_plot_df["Model"], fontsize=10)
ax.set_xlabel("Error in LPA (Lower is Better)", fontsize=12)
ax.set_title("Model Performance Benchmark: Test MAE & RMSE", fontsize=14, fontweight="bold", pad=12)
ax.legend(frameon=True, facecolor="white", loc="lower right")
for i, v in enumerate(comp_plot_df["Test MAE (LPA)"]):
    ax.text(v + 0.08, i - bar_width/2, f"{v:.2f}", va="center", fontsize=9, fontweight="bold", color="#1E3A8A")
for i, v in enumerate(comp_plot_df["Test RMSE (LPA)"]):
    ax.text(v + 0.08, i + bar_width/2, f"{v:.2f}", va="center", fontsize=9, fontweight="bold", color="#065F46")
ax.set_xlim(0, max(comp_plot_df["Test RMSE (LPA)"]) + 0.8)
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "model_performance_comparison.png"))
plt.close(fig)

# Figure 5: feature_importance.png
fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
top_20_fi = fi_df.head(20).sort_values(by="Importance", ascending=True)
colors = plt.cm.Blues(np.linspace(0.4, 0.95, len(top_20_fi)))
bars = ax.barh(top_20_fi["Feature"], top_20_fi["Importance"], color=colors, edgecolor="none", height=0.7)
ax.set_xlabel("Relative Importance Weight", fontsize=12)
ax.set_title("Top 20 Features Driving Salary Predictions (Tuned XGBoost)", fontsize=14, fontweight="bold", pad=12)
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.003, bar.get_y() + bar.get_height()/2, f"{w:.3f}", va="center", fontsize=9, fontweight="bold", color="#1E3A8A")
ax.set_xlim(0, max(top_20_fi["Importance"]) * 1.15)
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "feature_importance.png"))
plt.close(fig)

# Figure 6: cross_validation_performance.png
fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
cv_df_plot = pd.DataFrame(cv_scores_dict)
sns.boxplot(data=cv_df_plot, ax=ax, palette="Blues_r", showmeans=True, meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"red"})
ax.set_xticklabels(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
ax.set_ylabel("5-Fold CV MAE [LPA] (Lower is Better)", fontsize=12)
ax.set_title("5-Fold Cross-Validation Error Distribution Across Candidate Models", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "cross_validation_performance.png"))
plt.close(fig)

# Figure 7: prediction_errors_by_job_role.png
test_eval_df = X_test.copy()
test_eval_df["actual_salary"] = y_test
test_eval_df["predicted_salary"] = y_pred_tuned
test_eval_df["abs_error"] = np.abs(y_test - y_pred_tuned)

top_roles = test_eval_df["job_title"].value_counts().head(12).index
role_errors = test_eval_df[test_eval_df["job_title"].isin(top_roles)].groupby("job_title")["abs_error"].mean().sort_values(ascending=True)

fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
bars = ax.barh(role_errors.index, role_errors.values, color="#3B82F6", height=0.65)
ax.set_xlabel("Mean Absolute Error (LPA)", fontsize=12)
ax.set_title("Salary Prediction Error (MAE) Across Top Job Roles", fontsize=14, fontweight="bold", pad=12)
for bar in bars:
    w = bar.get_width()
    ax.text(w + 0.04, bar.get_y() + bar.get_height()/2, f"{w:.2f} LPA", va="center", fontsize=9, fontweight="bold", color="#1E3A8A")
ax.set_xlim(0, max(role_errors.values) + 0.5)
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "prediction_errors_by_job_role.png"))
plt.close(fig)

# Figure 8: prediction_errors_by_experience_level.png
exp_order = ["Fresher", "Junior", "Mid-level", "Senior", "Lead"]
exp_eval_df = test_eval_df[test_eval_df["experience_level"].isin(exp_order)]

fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
sns.boxplot(x="experience_level", y="abs_error", data=exp_eval_df, order=exp_order, ax=ax, palette="Blues", showfliers=False, showmeans=True, meanprops={"marker":"s", "markerfacecolor":"red", "markeredgecolor":"red"})
ax.set_xlabel("Experience Level", fontsize=12)
ax.set_ylabel("Absolute Error (LPA)", fontsize=12)
ax.set_title("Prediction Error Spread Across Candidate Seniority Tiers", fontsize=14, fontweight="bold", pad=12)
plt.tight_layout()
fig.savefig(os.path.join(FIGURES_DIR, "prediction_errors_by_experience_level.png"))
plt.close(fig)

print("All 8 figures successfully generated and saved to reports/figures/model_evaluation/!")
