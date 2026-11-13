"""
Módulo de Machine Learning Supervisado: Modelo Predictivo de Riesgo de Churn
----------------------------------------------------------------------------
Entrena un clasificador para predecir la probabilidad individual de fuga
de cada cliente (Churn Probability Score) utilizando RandomForestClassifier.

Genera:
- Matriz de confusión y métricas ROC-AUC / F1-Score.
- Feature Importance (Factores determinantes de la fuga de clientes).
- Exportación de scores de riesgo para integración en Power BI y campañas comerciales.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, RocCurveDisplay

def train_churn_model():
    print(">> Iniciando entrenamiento del Modelo Predictivo Supervisado de Churn...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    proc_dir = os.path.join(base_dir, "data", "processed")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    csv_path = os.path.join(proc_dir, "customer_churn_features.csv")
    df = pd.read_csv(csv_path)
    
    features = [
        "age",
        "annual_income",
        "credit_score",
        "tenure_months",
        "recency_days",
        "frequency",
        "monetary",
        "avg_ticket",
        "digital_ratio",
        "total_fees"
    ]
    
    X = df[features].copy()
    y = df["is_churn"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )
    
    rf = RandomForestClassifier(
        n_estimators=150,
        max_depth=7,
        min_samples_split=10,
        random_state=42,
        class_weight="balanced"
    )
    rf.fit(X_train, y_train)
    
    y_pred = rf.predict(X_test)
    y_prob = rf.predict_proba(X_test)[:, 1]
    
    auc = roc_auc_score(y_test, y_prob)
    print(f"   [OK] Modelo entrenado. ROC-AUC en test: {auc:.4f}")
    print("\nReporte de Clasificación:")
    print(classification_report(y_test, y_pred, target_names=["Activo (0)", "Churn (1)"]))
    
    # Asignar probabilidades a toda la cartera para el dashboard
    df_scored = df.copy()
    all_probs = rf.predict_proba(X)[:, 1]
    df_scored["churn_probability"] = np.round(all_probs, 4)
    
    # Categorización de riesgo para el equipo comercial
    conditions = [
        df_scored["churn_probability"] < 0.25,
        (df_scored["churn_probability"] >= 0.25) & (df_scored["churn_probability"] < 0.50),
        (df_scored["churn_probability"] >= 0.50) & (df_scored["churn_probability"] < 0.75),
        df_scored["churn_probability"] >= 0.75
    ]
    tiers = ["1. Riesgo Bajo", "2. Riesgo Moderado", "3. Riesgo Alto", "4. Riesgo Crítico"]
    df_scored["churn_risk_tier"] = np.select(conditions, tiers, default="1. Riesgo Bajo")
    
    # Guardar dataset con scoring
    scored_path = os.path.join(proc_dir, "customer_churn_scored.csv")
    df_scored.to_csv(scored_path, index=False)
    print(f">> Dataset con probabilidades de churn guardado en: {scored_path}")
    
    # Graficar Importancia de Variables (Feature Importance)
    importances = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=True)
    
    plt.figure(figsize=(9, 5.5))
    importances.plot(kind="barh", color="#1f77b4")
    plt.title("Factores Clave Determinantes del Churn Bancario (Feature Importance)", pad=15, fontweight="bold")
    plt.xlabel("Importancia Relativa (Gini Importance)", fontweight="bold")
    plt.tight_layout()
    
    chart_path = os.path.join(reports_dir, "churn_feature_importance.png")
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f">> Gráfico de importancia de variables guardado en: {chart_path}\n")

if __name__ == "__main__":
    train_churn_model()
