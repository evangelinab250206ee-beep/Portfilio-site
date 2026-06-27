"""
train.py
----------
Complete training pipeline for the weather prediction system.

Trains:
  - Random Forest (+ XGBoost if installed) regressors for:
      temperature_2m, shortwave_radiation, wind_speed_10m
  - Random Forest (+ XGBoost if installed) classifier for:
      rain_flag (rain probability / yes-no)

Evaluates with MAE / RMSE / R2 (regression) and Accuracy / Precision /
Recall / F1 / ROC-AUC (classification), saves the best model per target,
and generates diagnostic plots in Results/.

Run:
    python train.py
"""

import os
import json
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix,
)

try:
    from xgboost import XGBRegressor, XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print(
        "[WARN] xgboost is not installed. Run `pip install xgboost` to enable "
        "XGBoost models. Continuing with Random Forest only."
    )

from data_loader import build_dataset
from feature_engineering import (
    build_features, build_regression_targets, build_classification_target,
    REGRESSION_TARGETS, CLASSIFICATION_TARGET,
)

warnings.filterwarnings("ignore", category=FutureWarning)

WEATHER_DATA_DIR = "WeatherData"
MODELS_DIR = "Models"
RESULTS_DIR = "Results"
RANDOM_STATE = 42
RAIN_THRESHOLD_MM = 0.1  # rain (mm) above this counts as "rain" for classification

sns.set_theme(style="whitegrid")


# --------------------------------------------------------------------------
# Model factories
# --------------------------------------------------------------------------

def get_regressors():
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=80,
            max_depth=11,
            min_samples_leaf=10,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbosity=0,
        )
    return models


def get_classifiers():
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            max_depth=11,
            min_samples_leaf=10,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
    }
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=-1,
            random_state=RANDOM_STATE,
            eval_metric="logloss",
            verbosity=0,
        )
    return models


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------

def evaluate_regression(y_true, y_pred) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    return {"MAE": mae, "RMSE": rmse, "R2": r2}


def evaluate_classification(y_true, y_pred, y_proba) -> dict:
    return {
        "Accuracy": accuracy_score(y_true, y_pred),
        "Precision": precision_score(y_true, y_pred, zero_division=0),
        "Recall": recall_score(y_true, y_pred, zero_division=0),
        "F1": f1_score(y_true, y_pred, zero_division=0),
        "ROC_AUC": roc_auc_score(y_true, y_proba),
    }


# --------------------------------------------------------------------------
# Plotting
# --------------------------------------------------------------------------

def plot_actual_vs_predicted(y_true, y_pred, target_name: str, model_name: str, path: str):
    plt.figure(figsize=(7, 6))
    sample_idx = np.random.RandomState(RANDOM_STATE).choice(
        len(y_true), size=min(2000, len(y_true)), replace=False
    )
    y_true_s = np.array(y_true)[sample_idx]
    y_pred_s = np.array(y_pred)[sample_idx]

    plt.scatter(y_true_s, y_pred_s, alpha=0.3, s=12, color="#2563eb")
    lims = [min(y_true_s.min(), y_pred_s.min()), max(y_true_s.max(), y_pred_s.max())]
    plt.plot(lims, lims, "r--", linewidth=1.5, label="Perfect prediction")
    plt.xlabel(f"Actual {target_name}")
    plt.ylabel(f"Predicted {target_name}")
    plt.title(f"Actual vs Predicted: {target_name} ({model_name})")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_rain_results(y_true, y_pred, y_proba, model_name: str, path: str):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

    cm = confusion_matrix(y_true, y_pred)
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=False, ax=axes[0],
        xticklabels=["No Rain", "Rain"], yticklabels=["No Rain", "Rain"],
    )
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")
    axes[0].set_title(f"Rain Prediction Confusion Matrix ({model_name})")

    axes[1].hist(
        [np.array(y_proba)[np.array(y_true) == 0], np.array(y_proba)[np.array(y_true) == 1]],
        bins=30, label=["No Rain (actual)", "Rain (actual)"],
        color=["#94a3b8", "#2563eb"], alpha=0.8,
    )
    axes[1].set_xlabel("Predicted rain probability")
    axes[1].set_ylabel("Count")
    axes[1].set_title("Predicted Probability Distribution")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_feature_importance(model, feature_names, target_name: str, model_name: str, path: str):
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        return  # model type doesn't expose feature importances

    order = np.argsort(importances)[::-1][:15]  # top 15
    top_features = [feature_names[i] for i in order]
    top_importances = importances[order]

    plt.figure(figsize=(8, 6))
    plt.barh(top_features[::-1], top_importances[::-1], color="#16a34a")
    plt.xlabel("Importance")
    plt.title(f"Feature Importance: {target_name} ({model_name})")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


# --------------------------------------------------------------------------
# Main training routine
# --------------------------------------------------------------------------

def train_all(folder_path: str = WEATHER_DATA_DIR, test_size: float = 0.2):
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print("=" * 70)
    print("STEP 1-3: Loading, cleaning, merging WeatherData/*.csv")
    print("=" * 70)
    df = build_dataset(folder_path, rain_threshold=RAIN_THRESHOLD_MM)

    print("\n" + "=" * 70)
    print("STEP 4: Building features (hour, day, month, day_of_week, lat/lon, city)")
    print("=" * 70)
    X, feature_cols, city_cols = build_features(df)
    y_reg_all = build_regression_targets(df)
    y_rain = build_classification_target(df)

    X_train, X_test, y_reg_train, y_reg_test, y_rain_train, y_rain_test = train_test_split(
        X, y_reg_all, y_rain, test_size=test_size, random_state=RANDOM_STATE,
        stratify=y_rain,
    )

    # ----------------------------------------------------------------
    # Regression targets: temperature_2m, shortwave_radiation, wind_speed_10m
    # ----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 5: Training regression models")
    print("=" * 70)

    reg_results = {}
    best_reg_models = {}

    for target in REGRESSION_TARGETS:
        print(f"\n--- Target: {target} ---")
        y_train = y_reg_train[target]
        y_test = y_reg_test[target]

        reg_results[target] = {}
        best_score, best_name, best_model = -np.inf, None, None

        for model_name, model in get_regressors().items():
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            metrics = evaluate_regression(y_test, preds)
            reg_results[target][model_name] = metrics

            print(
                f"  {model_name:<14} MAE={metrics['MAE']:.4f}  "
                f"RMSE={metrics['RMSE']:.4f}  R2={metrics['R2']:.4f}"
            )

            if metrics["R2"] > best_score:
                best_score, best_name, best_model = metrics["R2"], model_name, model

            # Save predictions for the plot for THIS model too (only best gets saved as final)
            if model_name == best_name or best_name is None:
                pass

        best_reg_models[target] = (best_name, best_model)
        print(f"  -> Best model for {target}: {best_name} (R2={best_score:.4f})")

        # Plots use the best model's predictions
        best_preds = best_model.predict(X_test)
        if target in ("temperature_2m", "shortwave_radiation"):
            plot_actual_vs_predicted(
                y_test, best_preds, target, best_name,
                os.path.join(RESULTS_DIR, f"actual_vs_predicted_{target}.png"),
            )
        plot_feature_importance(
            best_model, feature_cols, target, best_name,
            os.path.join(RESULTS_DIR, f"feature_importance_{target}.png"),
        )

    # ----------------------------------------------------------------
    # Classification target: rain_flag
    # ----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 6: Training rain classification models")
    print("=" * 70)

    clf_results = {}
    best_clf_name, best_clf_model, best_clf_score = None, None, -np.inf

    for model_name, model in get_classifiers().items():
        model.fit(X_train, y_rain_train)
        preds = model.predict(X_test)
        proba = model.predict_proba(X_test)[:, 1]
        metrics = evaluate_classification(y_rain_test, preds, proba)
        clf_results[model_name] = metrics

        print(
            f"  {model_name:<14} Accuracy={metrics['Accuracy']:.4f}  "
            f"Precision={metrics['Precision']:.4f}  Recall={metrics['Recall']:.4f}  "
            f"F1={metrics['F1']:.4f}  ROC_AUC={metrics['ROC_AUC']:.4f}"
        )

        if metrics["F1"] > best_clf_score:
            best_clf_score, best_clf_name, best_clf_model = metrics["F1"], model_name, model

    print(f"  -> Best model for rain_flag: {best_clf_name} (F1={best_clf_score:.4f})")

    best_clf_preds = best_clf_model.predict(X_test)
    best_clf_proba = best_clf_model.predict_proba(X_test)[:, 1]
    plot_rain_results(
        y_rain_test, best_clf_preds, best_clf_proba, best_clf_name,
        os.path.join(RESULTS_DIR, "rain_prediction_results.png"),
    )
    plot_feature_importance(
        best_clf_model, feature_cols, "rain_flag", best_clf_name,
        os.path.join(RESULTS_DIR, "feature_importance_rain_flag.png"),
    )

    # ----------------------------------------------------------------
    # Save models + schema
    # ----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 7: Saving trained models")
    print("=" * 70)

    for target, (model_name, model_obj) in best_reg_models.items():
        path = os.path.join(MODELS_DIR, f"{target}_{model_name}.joblib")
        joblib.dump(model_obj, path)
        print(f"  Saved {path}")

    clf_path = os.path.join(MODELS_DIR, f"rain_flag_{best_clf_name}.joblib")
    joblib.dump(best_clf_model, clf_path)
    print(f"  Saved {clf_path}")

    schema = {
        "base_feature_columns": [
            "hour", "day", "month", "day_of_week",
            "latitude", "longitude",
            "hour_sin", "hour_cos", "month_sin", "month_cos", "dow_sin", "dow_cos",
        ],
        "city_columns": city_cols,
        "regression_targets": REGRESSION_TARGETS,
        "classification_target": CLASSIFICATION_TARGET,
        "best_model_per_regression_target": {t: m[0] for t, m in best_reg_models.items()},
        "best_classifier": best_clf_name,
        "rain_threshold_mm": RAIN_THRESHOLD_MM,
    }
    schema_path = os.path.join(MODELS_DIR, "feature_schema.json")
    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)
    print(f"  Saved {schema_path}")

    # ----------------------------------------------------------------
    # Comparison tables
    # ----------------------------------------------------------------
    print("\n" + "=" * 70)
    print("STEP 8: Model comparison")
    print("=" * 70)

    reg_rows = []
    for target, model_results in reg_results.items():
        for model_name, metrics in model_results.items():
            reg_rows.append({"target": target, "model": model_name, **metrics})
    reg_comparison_df = pd.DataFrame(reg_rows)
    print("\nRegression models:")
    print(reg_comparison_df.to_string(index=False))
    reg_comparison_df.to_csv(os.path.join(RESULTS_DIR, "regression_model_comparison.csv"), index=False)

    clf_rows = []
    for model_name, metrics in clf_results.items():
        clf_rows.append({"model": model_name, **metrics})
    clf_comparison_df = pd.DataFrame(clf_rows)
    print("\nRain classification models:")
    print(clf_comparison_df.to_string(index=False))
    clf_comparison_df.to_csv(os.path.join(RESULTS_DIR, "rain_model_comparison.csv"), index=False)

    print(f"\nSaved comparison tables and plots to {RESULTS_DIR}/")

    return reg_results, clf_results, best_reg_models, (best_clf_name, best_clf_model), schema


if __name__ == "__main__":
    train_all()
