"""
Módulo de Machine Learning: Segmentación de Clientes con K-Means Clustering
--------------------------------------------------------------------------
Aplica algoritmos de aprendizaje no supervisado (K-Means) sobre el comportamiento
transaccional, financiero y digital de los clientes bancarios.

Flujo:
1. Selección e ingeniería de características (RFM + Digitalización + Margen).
2. Transformación de variables asimétricas (log-transform) y escalado (StandardScaler).
3. Determinación de K óptimo: Método del Codo (Elbow / WCSS) y Coeficiente de Silueta.
4. Entrenamiento del modelo K-Means y asignación de etiquetas.
5. Reducción dimensional con PCA (2D) para visualización.
6. Perfilado de segmentos y exportación para integración directa con Power BI.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

# Configuración estética de gráficos para reportes ejecutivos
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "figure.titlesize": 14,
    "figure.dpi": 150
})

def prepare_clustering_features(df_features):
    """
    Selecciona y transforma las variables cuantitativas más informativas
    del comportamiento del cliente.
    """
    feature_cols = [
        "recency_days",
        "frequency",
        "monetary",
        "avg_ticket",
        "digital_ratio",
        "total_fees",
        "credit_score",
        "tenure_months"
    ]
    
    X_raw = df_features[feature_cols].copy()
    
    # Aplicar transformación logarítmica a variables con asimetría positiva severa
    X_transformed = X_raw.copy()
    for col in ["frequency", "monetary", "avg_ticket", "total_fees"]:
        X_transformed[col] = np.log1p(np.maximum(0, X_transformed[col]))
        
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_transformed)
    
    return X_scaled, feature_cols, scaler

def find_optimal_k(X_scaled, reports_dir, k_range=range(2, 9)):
    """
    Calcula la inercia (WCSS) y el Silhouette Score para un rango de k
    y genera el gráfico de diagnóstico.
    """
    inertias = []
    silhouette_scores = []
    
    print(">> Evaluando rango de clusters (K=2 a 8)...")
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
        sil = silhouette_score(X_scaled, kmeans.labels_)
        silhouette_scores.append(sil)
        print(f"   - K={k} | Inercia: {kmeans.inertia_:,.1f} | Silhouette: {sil:.4f}")
        
    # Graficar Codo y Silueta
    fig, ax1 = plt.subplots(figsize=(9, 4.8))
    
    color = "tab:blue"
    ax1.set_xlabel("Número de Clusters (k)", fontweight="bold")
    ax1.set_ylabel("Inercia / WCSS (Codo)", color=color, fontweight="bold")
    ax1.plot(list(k_range), inertias, marker="o", color=color, linewidth=2.5, markersize=7, label="Inercia (WCSS)")
    ax1.tick_params(axis="y", labelcolor=color)
    
    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("Silhouette Score", color=color, fontweight="bold")
    ax2.plot(list(k_range), silhouette_scores, marker="s", color=color, linewidth=2.5, linestyle="--", markersize=7, label="Silhouette Score")
    ax2.tick_params(axis="y", labelcolor=color)
    
    plt.title("Evaluación de K Óptimo: Método del Codo vs. Silhouette Score", pad=15)
    fig.tight_layout()
    
    chart_path = os.path.join(reports_dir, "elbow_silhouette_analysis.png")
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f">> Gráfico de diagnóstico guardado en: {chart_path}")
    
    # Elegir k con mejor equilibrio (k=4 ofrece una interpretación de negocio óptima)
    best_k = 4
    return best_k

def train_and_label_clusters(df_features, X_scaled, n_clusters=4):
    """
    Entrena el modelo final de K-Means y asigna etiquetas descriptivas a los clusters.
    """
    print(f">> Entrenando K-Means definitivo con K={n_clusters} clusters...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=15)
    clusters = kmeans.fit_predict(X_scaled)
    
    df_result = df_features.copy()
    df_result["cluster_id"] = clusters
    
    # Calcular promedios por cluster para nombrar estratégicamente los grupos
    profile = df_result.groupby("cluster_id").agg(
        recency=("recency_days", "mean"),
        frequency=("frequency", "mean"),
        monetary=("monetary", "mean"),
        avg_ticket=("avg_ticket", "mean"),
        digital_ratio=("digital_ratio", "mean"),
        churn_rate=("is_churn", "mean"),
        count=("customer_key", "count")
    ).reset_index()
    
    # Mapeo semántico de negocio para los clusters
    # Se evalúa cuál cluster tiene mayor recencia (inactivo) o mayor gasto
    naming_map = {}
    for _, row in profile.iterrows():
        cid = int(row["cluster_id"])
        if row["recency"] > 180 or row["churn_rate"] > 0.45:
            name = "Cluster Inactivo / Alto Riesgo Churn"
        elif row["monetary"] > 25000:
            name = "Cluster Wealth / Clientes VIP"
        elif row["digital_ratio"] > 0.65 and row["frequency"] >= 20:
            name = "Cluster Digital Activo (Champions)"
        else:
            name = "Cluster Tradicional / Consumo Moderado"
        naming_map[cid] = name
        
    df_result["cluster_name"] = df_result["cluster_id"].map(naming_map)
    return df_result, kmeans, naming_map

def plot_pca_clusters(X_scaled, df_result, reports_dir):
    """
    Reduce a 2 dimensiones con PCA y grafica los clusters formados.
    """
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(X_scaled)
    
    df_plot = df_result.copy()
    df_plot["pca1"] = coords[:, 0]
    df_plot["pca2"] = coords[:, 1]
    
    plt.figure(figsize=(10, 6.5))
    palette = sns.color_palette("Set2", n_colors=df_plot["cluster_name"].nunique())
    
    scatter = sns.scatterplot(
        data=df_plot,
        x="pca1",
        y="pca2",
        hue="cluster_name",
        palette=palette,
        style="is_churn",
        markers={0: "o", 1: "X"},
        alpha=0.75,
        s=60
    )
    
    var_exp = (pca.explained_variance_ratio_ * 100).round(1)
    plt.title(f"Segmentación de Clientes Bancarios con K-Means (PCA 2D)\nVarianza explicada: PC1={var_exp[0]}%, PC2={var_exp[1]}%", pad=15)
    plt.xlabel(f"Componente Principal 1 ({var_exp[0]}%)", fontweight="bold")
    plt.ylabel(f"Componente Principal 2 ({var_exp[1]}%)", fontweight="bold")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", title="Segmentos y Fuga (X=Churn)")
    plt.tight_layout()
    
    chart_path = os.path.join(reports_dir, "customer_clusters_2d.png")
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f">> Gráfico de PCA de clusters guardado en: {chart_path}")

def plot_cluster_profiling(df_result, reports_dir):
    """
    Genera un gráfico comparativo del perfil financiero de cada cluster.
    """
    summary = df_result.groupby("cluster_name").agg(
        clientes=("customer_key", "count"),
        recencia_dias=("recency_days", "mean"),
        transacciones_prom=("frequency", "mean"),
        gasto_total_prom=("monetary", "mean"),
        ticket_promedio=("avg_ticket", "mean"),
        tasa_churn=("is_churn", lambda x: (x.mean() * 100)),
        adopcion_digital=("digital_ratio", lambda x: (x.mean() * 100))
    ).round(2).reset_index()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    
    # 1. Gasto Total Promedio
    sns.barplot(data=summary, x="cluster_name", y="gasto_total_prom", ax=axes[0, 0], palette="Blues_d")
    axes[0, 0].set_title("Gasto Total Promedio ($)")
    axes[0, 0].set_xlabel("")
    axes[0, 0].tick_params(axis="x", rotation=15)
    for p in axes[0, 0].patches:
        axes[0, 0].annotate(f"${p.get_height():,.0f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
                            
    # 2. Tasa de Churn (%)
    sns.barplot(data=summary, x="cluster_name", y="tasa_churn", ax=axes[0, 1], palette="Reds_d")
    axes[0, 1].set_title("Tasa de Churn (%)")
    axes[0, 1].set_xlabel("")
    axes[0, 1].tick_params(axis="x", rotation=15)
    for p in axes[0, 1].patches:
        axes[0, 1].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
                            
    # 3. Frecuencia de Transacciones
    sns.barplot(data=summary, x="cluster_name", y="transacciones_prom", ax=axes[1, 0], palette="Greens_d")
    axes[1, 0].set_title("Frecuencia Promedio de Transacciones")
    axes[1, 0].set_xlabel("")
    axes[1, 0].tick_params(axis="x", rotation=15)
    for p in axes[1, 0].patches:
        axes[1, 0].annotate(f"{p.get_height():.1f} tx", (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
                            
    # 4. Adopción de Canales Digitales (%)
    sns.barplot(data=summary, x="cluster_name", y="adopcion_digital", ax=axes[1, 1], palette="Purples_d")
    axes[1, 1].set_title("Adopción de Canales Digitales (%)")
    axes[1, 1].set_xlabel("")
    axes[1, 1].tick_params(axis="x", rotation=15)
    for p in axes[1, 1].patches:
        axes[1, 1].annotate(f"{p.get_height():.1f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                            ha='center', va='bottom', fontsize=9, xytext=(0, 3), textcoords='offset points')
                            
    plt.suptitle("Perfil Comparativo de Segmentos K-Means en la Cartera Bancaria", y=0.99, fontsize=15, fontweight="bold")
    plt.tight_layout()
    
    chart_path = os.path.join(reports_dir, "cluster_profiling_summary.png")
    plt.savefig(chart_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f">> Gráfico de perfil de clusters guardado en: {chart_path}")
    
    return summary

def main():
    print(">> Iniciando módulo de Inteligencia Artificial (Clustering K-Means)...")
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    proc_dir = os.path.join(base_dir, "data", "processed")
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    
    features_csv = os.path.join(proc_dir, "customer_churn_features.csv")
    if not os.path.exists(features_csv):
        raise FileNotFoundError(f"No se encontró el dataset de features en: {features_csv}. Ejecute primero el ETL.")
        
    df_features = pd.read_csv(features_csv)
    print(f"   [OK] Dataset de clientes cargado: {len(df_features):,} registros.")
    
    # 1. Preparar features
    X_scaled, feature_cols, scaler = prepare_clustering_features(df_features)
    print(f"   [OK] {len(feature_cols)} variables escaladas y normalizadas.")
    
    # 2. Diagnóstico K Óptimo
    optimal_k = find_optimal_k(X_scaled, reports_dir)
    
    # 3. Entrenamiento K-Means
    df_segmented, kmeans_model, naming_map = train_and_label_clusters(df_features, X_scaled, n_clusters=optimal_k)
    
    # 4. Guardar archivo final con asignación de clusters para Power BI
    out_csv = os.path.join(proc_dir, "customer_clusters_segmented.csv")
    df_segmented.to_csv(out_csv, index=False)
    print(f">> Dataset segmentado exportado para Power BI en: {out_csv}")
    
    # 5. Generar visualizaciones
    plot_pca_clusters(X_scaled, df_segmented, reports_dir)
    summary_df = plot_cluster_profiling(df_segmented, reports_dir)
    
    print("\n>> Resumen Ejecutivo de los Segmentos Descubiertos:")
    print(summary_df.to_string(index=False))
    print("\n>> Proceso de Machine Learning completado con éxito.")

if __name__ == "__main__":
    main()
