"""
Módulo de Carga a Base de Datos Relacional / Data Warehouse
----------------------------------------------------------
Este script permite cargar las tablas dimensionales y de hechos generadas
en un motor de base de datos relacional.
Soporta:
1. SQLite (Base de datos local ligera y autocontenida por defecto: data/banking_dw.db)
2. PostgreSQL (Data Warehouse empresarial usando psycopg2 y SQLAlchemy)
3. SQL Server (mediante cadena de conexión SQLAlchemy)
"""

import os
import sys
import argparse
import pandas as pd
from sqlalchemy import create_engine, text

def get_engine(db_type="sqlite", connection_url=None, db_path=None):
    """Inicializa la conexión de SQLAlchemy según el motor seleccionado."""
    if db_type == "sqlite":
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_path = os.path.join(base_dir, "data", "banking_dw.db")
        print(f">> Conectando a base de datos SQLite local en: {db_path}")
        engine = create_engine(f"sqlite:///{db_path}")
    elif db_type in ["postgresql", "postgres"]:
        if not connection_url:
            connection_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bank_dw")
        print(f">> Conectando a PostgreSQL: {connection_url.split('@')[-1]}")
        engine = create_engine(connection_url)
    elif db_type == "sqlserver":
        if not connection_url:
            connection_url = os.environ.get("DATABASE_URL", "mssql+pyodbc://localhost/bank_dw?driver=ODBC+Driver+17+for+SQL+Server")
        print(f">> Conectando a SQL Server...")
        engine = create_engine(connection_url)
    else:
        raise ValueError(f"Motor no soportado: {db_type}")
        
    return engine

def load_tables(engine, proc_dir):
    """Carga los DataFrames en las tablas correspondientes."""
    print(">> Cargando tablas procesadas en el Data Warehouse...")
    
    tables_to_load = [
        ("dim_date", "dim_dates.csv"),
        ("dim_customer", "dim_customers.csv"),
        ("dim_product", "dim_products.csv"),
        ("fact_transactions", "fact_transactions.csv")
    ]
    
    with engine.begin() as conn:
        for table_name, csv_file in tables_to_load:
            csv_path = os.path.join(proc_dir, csv_file)
            if not os.path.exists(csv_path):
                print(f"   [ERROR] Archivo no encontrado: {csv_path}")
                continue
                
            df = pd.read_csv(csv_path)
            # Reemplazar tabla si existe
            df.to_sql(table_name, conn, if_exists="replace", index=False, chunksize=5000)
            print(f"   [OK] Tabla '{table_name}' cargada exitosamente: {len(df):,} filas.")
            
def run_verification_query(engine):
    """Ejecuta una consulta de verificación de integridad referencial y métricas clave."""
    print("\n>> Ejecutando consulta de verificación analítica en la base de datos...")
    query = """
    SELECT 
        c.customer_segment,
        COUNT(DISTINCT c.customer_key) AS total_clientes,
        SUM(c.is_churn) AS clientes_churn,
        ROUND(AVG(c.is_churn) * 100, 2) AS tasa_churn_pct,
        COUNT(f.transaction_key) AS total_transacciones,
        ROUND(SUM(f.amount), 2) AS monto_total,
        ROUND(AVG(f.amount), 2) AS ticket_promedio
    FROM dim_customer c
    LEFT JOIN fact_transactions f ON c.customer_key = f.customer_key
    GROUP BY c.customer_segment
    ORDER BY total_clientes DESC;
    """
    with engine.connect() as conn:
        res = pd.read_sql_query(text(query), conn)
        print(res.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description="Cargador de Esquema Estrella a Base de Datos Relacional")
    parser.add_argument("--db-type", choices=["sqlite", "postgresql", "sqlserver"], default="sqlite", help="Motor de base de datos objetivo")
    parser.add_argument("--url", default=None, help="Cadena de conexión completa para PostgreSQL o SQL Server")
    
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    proc_dir = os.path.join(base_dir, "data", "processed")
    
    engine = get_engine(db_type=args.db_type, connection_url=args.url)
    load_tables(engine, proc_dir)
    run_verification_query(engine)
    print("\n>> Proceso de base de datos finalizado con éxito.")

if __name__ == "__main__":
    main()
