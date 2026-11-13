"""
Módulo de Extracción, Transformación y Carga (ETL) y Modelado Dimensional
------------------------------------------------------------------------
Transforma los datos transaccionales crudos en un Esquema Estrella (Star Schema):
- Dim_Customer (Dimensión Clientes con cohortes y segmentación sociodemográfica)
- Dim_Product (Dimensión Catálogo de Productos y Líneas de Negocio)
- Dim_Date (Dimensión Calendario completa para Time Intelligence en Power BI y SQL)
- Fact_Transactions (Tabla de Hechos Transaccionales con claves subrogadas y métricas)
- Customer_Features (Dataset analítico consolidado con métricas RFM y Churn para ML)
"""

import os
from datetime import datetime, date
import numpy as np
import pandas as pd

def build_dim_date(start_date="2022-01-01", end_date="2026-12-31"):
    """
    Construye una dimensión calendario exhaustiva para análisis temporal y Time Intelligence.
    """
    date_range = pd.date_range(start=start_date, end=end_date, freq="D")
    
    month_names_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    day_names_es = {
        0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado", 6: "Domingo"
    }
    
    dim_date = pd.DataFrame({
        "full_date": date_range,
        "date_key": date_range.strftime("%Y%m%d").astype(int),
        "year": date_range.year,
        "quarter": date_range.quarter,
        "quarter_name": "T" + date_range.quarter.astype(str),
        "month_number": date_range.month,
        "month_name": date_range.month.map(month_names_es),
        "year_month": date_range.strftime("%Y-%m"),
        "week_of_year": date_range.isocalendar().week.astype(int),
        "day_of_month": date_range.day,
        "day_of_week": date_range.dayofweek + 1,
        "day_name": date_range.dayofweek.map(day_names_es),
        "is_weekend": date_range.dayofweek.isin([5, 6]).astype(int)
    })
    
    dim_date["full_date"] = dim_date["full_date"].dt.strftime("%Y-%m-%d")
    return dim_date

def transform_dim_customer(df_raw_customers, ref_date=datetime(2026, 11, 1)):
    """
    Limpia, valida y enriquece la dimensión de clientes.
    """
    df = df_raw_customers.copy()
    
    # 1. Validación de tipos y formato
    df["annual_income"] = pd.to_numeric(df["annual_income"], errors="coerce").fillna(0.0)
    df["credit_score"] = pd.to_numeric(df["credit_score"], errors="coerce").astype(int)
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype(int)
    
    # 2. Clave subrogada de dimensión
    df = df.sort_values(by="customer_id").reset_index(drop=True)
    df["customer_key"] = range(1001, 1001 + len(df))
    
    # 3. Categorizaciones demográficas y de riesgo
    # Grupo de Edad
    bins_age = [0, 25, 35, 50, 65, 120]
    labels_age = ["< 25", "25-34", "35-49", "50-64", "65+"]
    df["age_group"] = pd.cut(df["age"], bins=bins_age, labels=labels_age, right=False)
    
    # Rango de Ingresos
    bins_income = [0, 28000, 65000, 120000, float("inf")]
    labels_income = ["Bajo (< 28k)", "Medio (28k-65k)", "Medio-Alto (65k-120k)", "Alto (> 120k)"]
    df["income_bracket"] = pd.cut(df["annual_income"], bins=bins_income, labels=labels_income)
    
    # Nivel de Score Crediticio (Estándar FICO)
    bins_score = [0, 580, 670, 740, 800, 900]
    labels_score = ["Pobre (< 580)", "Regular (580-669)", "Bueno (670-739)", "Muy Bueno (740-799)", "Excelente (800+)"]
    df["credit_tier"] = pd.cut(df["credit_score"], bins=bins_score, labels=labels_score)
    
    # 4. Cálculo de Antigüedad (Tenure) en meses
    acq_dt = pd.to_datetime(df["acquisition_date"])
    df["acquisition_year"] = acq_dt.dt.year
    df["tenure_months"] = ((ref_date - acq_dt).dt.days / 30.4375).round(1)
    
    # 5. Marcaje de Churn explícito
    df["is_churn"] = (df["is_active"] == 0).astype(int)
    df["churn_reason"] = df["churn_reason"].fillna("No Churn / Activo")
    
    # Reordenar columnas para esquema de almacenamiento óptimo
    cols = [
        "customer_key", "customer_id", "full_name", "gender", "age", "age_group",
        "annual_income", "income_bracket", "credit_score", "credit_tier",
        "customer_segment", "region", "acquisition_date", "acquisition_year",
        "tenure_months", "is_active", "is_churn", "churn_date", "churn_reason"
    ]
    return df[cols]

def transform_dim_product(df_raw_products):
    """
    Construye la dimensión de productos financieros con clave subrogada.
    """
    df = df_raw_products.copy()
    df = df.sort_values(by="product_id").reset_index(drop=True)
    df["product_key"] = range(201, 201 + len(df))
    
    cols = ["product_key", "product_id", "product_name", "product_category", "monthly_fee", "interest_rate"]
    return df[cols]

def transform_fact_transactions(df_raw_tx, df_dim_cust, df_dim_prod, df_dim_date):
    """
    Construye la tabla de hechos transaccionales vinculando claves foráneas con las dimensiones.
    """
    df = df_raw_tx.copy()
    
    # Mapeo de claves subrogadas
    cust_map = df_dim_cust.set_index("customer_id")["customer_key"].to_dict()
    prod_map = df_dim_prod.set_index("product_id")["product_key"].to_dict()
    
    df["customer_key"] = df["customer_id"].map(cust_map)
    df["product_key"] = df["product_id"].map(prod_map)
    
    # Extracción de date_key YYYYMMDD
    tx_dt = pd.to_datetime(df["transaction_date"])
    df["date_key"] = tx_dt.dt.strftime("%Y%m%d").astype(int)
    
    # Limpieza de montos y comisiones
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df["fee_amount"] = pd.to_numeric(df["fee_amount"], errors="coerce").fillna(0.0)
    df["net_bank_revenue"] = df["fee_amount"]
    
    # Clave primaria de la tabla de hechos
    df = df.sort_values(by=["transaction_date", "transaction_id"]).reset_index(drop=True)
    df["transaction_key"] = range(1, 1 + len(df))
    
    cols = [
        "transaction_key", "transaction_id", "customer_key", "product_key", "date_key",
        "transaction_date", "channel", "transaction_type", "amount", "fee_amount",
        "net_bank_revenue", "status"
    ]
    return df[cols]

def build_customer_churn_features(df_dim_cust, df_fact_tx, ref_date=datetime(2026, 11, 1)):
    """
    Construye el dataset consolidado de features para Machine Learning (Clustering K-Means y Clasificación)
    y para análisis RFM (Recency, Frequency, Monetary).
    """
    # Filtrar únicamente transacciones completadas
    completed_tx = df_fact_tx[df_fact_tx["status"] == "Completed"].copy()
    completed_tx["tx_dt"] = pd.to_datetime(completed_tx["transaction_date"])
    
    # Agrupación por cliente
    tx_summary = completed_tx.groupby("customer_key").agg(
        last_tx_date=("tx_dt", "max"),
        first_tx_date=("tx_dt", "min"),
        frequency=("transaction_key", "count"),
        monetary=("amount", "sum"),
        avg_ticket=("amount", "mean"),
        std_ticket=("amount", "std"),
        total_fees=("fee_amount", "sum"),
        # Métricas de canal digital
        digital_tx=("channel", lambda x: (x.isin(["Mobile App", "Web Banking"])).sum())
    ).reset_index()
    
    # Tratamiento de nulos en desviación estándar (clientes con 1 sola transacción)
    tx_summary["std_ticket"] = tx_summary["std_ticket"].fillna(0.0)
    
    # Recency en días respecto a la fecha de corte
    tx_summary["recency_days"] = (ref_date - tx_summary["last_tx_date"]).dt.days
    
    # Ratio de Adopción Digital (% transacciones digitales vs tradicionales)
    tx_summary["digital_ratio"] = (tx_summary["digital_tx"] / tx_summary["frequency"]).round(4)
    
    # Unir con la dimensión de clientes
    features = pd.merge(df_dim_cust, tx_summary, on="customer_key", how="left")
    
    # Rellenar clientes sin transacciones registradas
    features["frequency"] = features["frequency"].fillna(0).astype(int)
    features["monetary"] = features["monetary"].fillna(0.0).round(2)
    features["avg_ticket"] = features["avg_ticket"].fillna(0.0).round(2)
    features["std_ticket"] = features["std_ticket"].fillna(0.0).round(2)
    features["total_fees"] = features["total_fees"].fillna(0.0).round(2)
    features["recency_days"] = features["recency_days"].fillna(999).astype(int)
    features["digital_ratio"] = features["digital_ratio"].fillna(0.0).round(4)
    
    # Estimación de LTV Financiero (Margen generado + proyección de comisiones)
    # LTV = Total Fees + (0.012 * Monetary Volume)
    features["customer_ltv"] = (features["total_fees"] + (features["monetary"] * 0.012)).round(2)
    
    return features

def run_etl():
    print(">> Iniciando proceso ETL y construcción del Modelo Estrella...")
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    raw_dir = os.path.join(base_dir, "data", "raw")
    proc_dir = os.path.join(base_dir, "data", "processed")
    os.makedirs(proc_dir, exist_ok=True)
    
    # 1. Cargar fuentes crudas
    print("   [1/5] Leyendo archivos crudos...")
    df_raw_cust = pd.read_csv(os.path.join(raw_dir, "raw_customers.csv"))
    df_raw_prod = pd.read_csv(os.path.join(raw_dir, "raw_products.csv"))
    df_raw_tx = pd.read_csv(os.path.join(raw_dir, "raw_transactions.csv"))
    
    # 2. Construir dimensiones
    print("   [2/5] Creando Dim_Date (2022-2026)...")
    df_dim_date = build_dim_date()
    df_dim_date.to_csv(os.path.join(proc_dir, "dim_dates.csv"), index=False)
    
    print("   [3/5] Transformando Dim_Customer y Dim_Product...")
    df_dim_cust = transform_dim_customer(df_raw_cust)
    df_dim_cust.to_csv(os.path.join(proc_dir, "dim_customers.csv"), index=False)
    
    df_dim_prod = transform_dim_product(df_raw_prod)
    df_dim_prod.to_csv(os.path.join(proc_dir, "dim_products.csv"), index=False)
    
    # 3. Construir tabla de hechos
    print("   [4/5] Generando Fact_Transactions vinculada a dimensiones...")
    df_fact_tx = transform_fact_transactions(df_raw_tx, df_dim_cust, df_dim_prod, df_dim_date)
    df_fact_tx.to_csv(os.path.join(proc_dir, "fact_transactions.csv"), index=False)
    
    # 4. Construir dataset analítico y RFM
    print("   [5/5] Construyendo dataset enriquecido customer_churn_features...")
    df_features = build_customer_churn_features(df_dim_cust, df_fact_tx)
    df_features.to_csv(os.path.join(proc_dir, "customer_churn_features.csv"), index=False)
    
    print("\n>> Resumen del Esquema Estrella Procesado:")
    print(f"   - Dim_Date:           {len(df_dim_date):,} registros")
    print(f"   - Dim_Customer:       {len(df_dim_cust):,} clientes (Tasa Churn: {df_dim_cust['is_churn'].mean()*100:.2f}%)")
    print(f"   - Dim_Product:        {len(df_dim_prod):,} productos")
    print(f"   - Fact_Transactions:  {len(df_fact_tx):,} transacciones (Monto Total: ${df_fact_tx['amount'].sum():,.2f})")
    print(f"   - Features RFM:       {len(df_features):,} filas analíticas preparadas para IA y Power BI.")
    print(">> ETL finalizado con éxito.\n")

if __name__ == "__main__":
    run_etl()
