"""
Orquestador Principal del Proyecto: Plataforma End-to-End de Churn & Segmentación Financiera
------------------------------------------------------------------------------------------
Ejecuta la totalidad del ciclo de vida del pipeline de datos con un único comando:
1. Generación de datos sintéticos bancarios (Clientes, Productos, Transacciones).
2. Proceso ETL y modelado dimensional Esquema Estrella (Dim_Customer, Dim_Product, Dim_Date, Fact_Transactions).
3. Carga y verificación en base de datos relacional (SQLite / PostgreSQL).
4. Machine Learning No Supervisado: Clustering K-Means y análisis RFM con scikit-learn.
5. Machine Learning Supervisado: Modelo predictivo de riesgo de Churn con Random Forest.
"""

import sys
import subprocess
import time

def run_step(step_number, total_steps, title, script_path):
    print("=" * 80)
    print(f"[{step_number}/{total_steps}] {title.upper()}")
    print(f"Archivo: {script_path}")
    print("=" * 80)
    start_time = time.time()
    
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        print(f"\n[ERROR] Falló la ejecución del paso {step_number}: {title}")
        sys.exit(result.returncode)
        
    print(f">> Paso completado exitosamente en {elapsed:.2f} segundos.\n")

def main():
    print("""
    ========================================================================
     PLATAFORMA BANCARIA DE CHURN & SEGMENTACIÓN DE CLIENTES FINANCIEROS
     Pipeline Automatizado End-to-End (Data Engineering, SQL, ML & Power BI)
    ========================================================================
    """)
    total_steps = 5
    
    # 1. Generación
    run_step(1, total_steps, "Generación de Datos Transaccionales Crudos", "src/generator/generate_banking_data.py")
    
    # 2. ETL & Esquema Estrella
    run_step(2, total_steps, "ETL y Modelado Dimensional (Star Schema)", "src/etl/etl_pipeline.py")
    
    # 3. Base de Datos
    run_step(3, total_steps, "Carga y Validación en Base de Datos Relacional", "src/database/load_to_db.py")
    
    # 4. Clustering K-Means
    run_step(4, total_steps, "Machine Learning: Clustering K-Means & Segmentación RFM", "src/ml/kmeans_clustering.py")
    
    # 5. Modelo Predictivo Churn
    run_step(5, total_steps, "Machine Learning: Scoring Predictivo de Churn con Random Forest", "src/ml/churn_prediction.py")
    
    print("*" * 80)
    print(">> TODAS LAS ETAPAS DEL PROYECTO SE COMPLETARON EXITOSAMENTE.")
    print("   - Los archivos dimensionales para Power BI se encuentran en: data/processed/")
    print("   - La base de datos SQLite se encuentra en: data/banking_dw.db")
    print("   - Los scripts SQL analíticos avanzados se encuentran en: sql/")
    print("   - Las medidas DAX y la guía de diseño visual se encuentran en: power_bi/")
    print("   - Los reportes gráficos generados por IA se encuentran en: reports/")
    print("*" * 80)

if __name__ == "__main__":
    main()
