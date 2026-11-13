# 🏦 Plataforma End-to-End de Churn & Segmentación de Clientes Financieros

[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Desktop-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-Machine_Learning-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Engineering-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Licencia](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 📌 1. El Problema de Negocio Real

Las instituciones financieras enfrentan un reto crítico: **el costo de adquirir un nuevo cliente bancario es entre 5 y 7 veces superior al de retener a uno existente**. Cuando un cliente cancela sus cuentas, tarjetas o créditos sin previo aviso, la entidad pierde tanto ingresos directos por comisiones como el margen financiero de intermediación (**LTV - Customer Lifetime Value**).

### Objetivos Estratégicos de la Plataforma:
1. **Detección Temprana del Churn:** Identificar señales de alerta preventiva (desaceleración de transacciones, contracción del gasto mes a mes y aumento del intervalo entre consumos) antes de que el cliente solicite la baja.
2. **Modelado Dimensional para Análisis Escalable:** Centralizar y organizar la operativa bancaria bajo un **Esquema Estrella (Star Schema)** optimizado para consultas analíticas de alto rendimiento.
3. **Analítica SQL Avanzada:** Explotar funciones de ventana (`LAG`, `LEAD`, `RANK`, `DENSE_RANK`, `NTILE`) y CTEs para cuantificar variaciones intermensuales y calcular la segmentación RFM directamente en la base de datos.
4. **Business Intelligence Ejecutivo:** Diseñar un dashboard en **Power BI** con más de 12 medidas DAX avanzadas (`CALCULATE`, `USERELATIONSHIP`, `DATESYTD`, `DATEADD`) para monitorear Churn, LTV, Ticket Promedio y Cohortes.
5. **Segmentación Inteligente con Machine Learning:** Agrupar clientes mediante **K-Means Clustering** y entrenar un modelo predictivo supervisado (**Random Forest**) que asigne una probabilidad de fuga a cada cuenta para dirigir campañas comerciales personalizadas.

---

## 🏗️ 2. Arquitectura de la Solución End-to-End

```mermaid
flowchart LR
    A["API / Core Transaccional<br/>(Datos Crudos Sintéticos)"] --> B["Pipeline ETL en Python<br/>(pandas & numpy)"]
    B --> C["Data Warehouse<br/>(Esquema Estrella)"]
    C --> D1["Consultas SQL Avanzadas<br/>(Window Functions & CTEs)"]
    C --> D2["Machine Learning<br/>(K-Means & Random Forest)"]
    C --> D3["Power BI Dashboard<br/>(Medidas DAX Avanzadas)"]
    D2 --> D3
```

---

## 📂 3. Estructura del Repositorio

```text
Plataforma End-to-End de Churn & Segmentación de Clientes Financieros/
│
├── run_project.py                    # Orquestador integral (Ejecución 1-Click de todo el pipeline)
├── requirements.txt                  # Dependencias del proyecto (pandas, scikit-learn, sqlalchemy, etc.)
├── .gitignore                        # Reglas de exclusión de Git (ignora .venv, bases locales, cache)
├── README.md                         # Documentación maestra técnica y de negocio
│
├── data/
│   ├── raw/                          # Datos crudos generados (Clientes, Productos, Transacciones)
│   │   ├── raw_customers.csv
│   │   ├── raw_products.csv
│   │   └── raw_transactions.csv
│   └── processed/                    # Esquema Estrella procesado (listo para Power BI y SQL)
│       ├── dim_customers.csv
│       ├── dim_products.csv
│       ├── dim_dates.csv
│       ├── fact_transactions.csv
│       ├── customer_churn_features.csv
│       ├── customer_clusters_segmented.csv  # Con asignación de cluster K-Means
│       └── customer_churn_scored.csv        # Con probabilidad de churn (Random Forest)
│
├── src/                              # Código fuente modular en Python
│   ├── generator/
│   │   └── generate_banking_data.py  # Generador de datos bancarios con patrones reales de fuga
│   ├── etl/
│   │   └── etl_pipeline.py           # Limpieza, validación y construcción del Star Schema
│   ├── database/
│   │   └── load_to_db.py             # Carga a SQLite (autocontenida) o PostgreSQL / SQL Server
│   └── ml/
│       ├── kmeans_clustering.py      # Clustering K-Means, Método del Codo, Silueta y PCA 2D
│       └── churn_prediction.py       # Clasificador supervisado de riesgo de Churn (Random Forest)
│
├── sql/                              # Scripts SQL analíticos para PostgreSQL / SQL Server
│   ├── 01_schema_star_ddl.sql        # DDL del Esquema Estrella (Tablas, PK, FK, Índices)
│   ├── 02_analytical_queries.sql     # Window Functions (LAG, LEAD, RANK, Rolling Avg, Cohortes)
│   └── 03_rfm_segmentation_sql.sql   # Segmentación RFM directamente en SQL con NTILE(5)
│
├── power_bi/                         # Recursos para Visualización y Business Intelligence
│   ├── DAX_MEASURES.md               # Explicación técnica y de negocio de las medidas DAX
│   ├── dax_measures.dax              # Código fuente de las medidas listo para copiar y pegar
│   └── powerbi_dashboard_guide.md    # Guía visual paso a paso para armar el Dashboard en Power BI
│
└── reports/                          # Visualizaciones ejecutivas generadas por los modelos de IA
    ├── elbow_silhouette_analysis.png # Diagnóstico de K óptimo (Codo vs. Silhouette Score)
    ├── customer_clusters_2d.png      # Proyección PCA 2D de los clusters y estado de fuga
    ├── cluster_profiling_summary.png # Perfil comparativo financiero por segmento
    └── churn_feature_importance.png  # Factores clave determinantes de la fuga de clientes
```

---

## 🗄️ 4. Modelo Dimensional (Esquema Estrella)

El Data Warehouse está modelado bajo la metodología de Ralph Kimball, separando hechos transaccionales de las entidades descriptivas (dimensiones):

| Tabla | Tipo | Descripción | Clave Primaria | Claves Foráneas |
|---|---|---|---|---|
| **`Dim_Customer`** | Dimensión | Datos sociodemográficos, score crediticio, tramo de ingresos, antigüedad, motivo de baja y estado activo/churn. | `customer_key` | Ninguna |
| **`Dim_Product`** | Dimensión | Catálogo de productos (Cuentas, Tarjetas de Crédito, Préstamos, Inversiones, Seguros) con tarifas y tasas. | `product_key` | Ninguna |
| **`Dim_Date`** | Dimensión | Calendario exhaustivo (2022-2026) con año, trimestre, mes, día, semana y banderas de fin de semana para Time Intelligence. | `date_key` | Ninguna |
| **`Fact_Transactions`** | Tabla de Hechos | Eventos transaccionales financieros (monto, comisiones, canal, tipo de operación, estado). | `transaction_key` | `customer_key`, `product_key`, `date_key` |

---

## 🔍 5. Consultas Analíticas SQL Avanzadas

Los scripts en [`sql/02_analytical_queries.sql`](file:///c:/Users/italo/Documents/Ciclo%202026-2/Proyectos/Plataforma%20End-to-End%20de%20Churn%20%26%20Segmentación%20de%20Clientes%20Financieros/sql/02_analytical_queries.sql) y [`sql/03_rfm_segmentation_sql.sql`](file:///c:/Users/italo/Documents/Ciclo%202026-2/Proyectos/Plataforma%20End-to-End%20de%20Churn%20%26%20Segmentación%20de%20Clientes%20Financieros/sql/03_rfm_segmentation_sql.sql) resuelven preguntas comerciales clave:

### A. Detección Temprana de Churn Mes a Mes con `LAG()` y CTEs
Permite contrastar el consumo actual de un cliente contra su mes anterior. Una caída sostenida superior al 50% activa la bandera `'ALERTA: Caída Crítica > 50%'`:
```sql
LAG(current_month_spend, 1) OVER (
    PARTITION BY customer_id 
    ORDER BY year_month ASC
) AS previous_month_spend
```

### B. Top Clientes por Categoría de Producto con `RANK()` y `DENSE_RANK()`
Calcula el ranking y el porcentaje de participación del cliente sobre el volumen total de la categoría utilizando una ventana analítica combinada:
```sql
RANK() OVER (
    PARTITION BY product_category 
    ORDER BY total_spent_category DESC
) AS rank_pos,
ROUND((total_spent_category / SUM(SUM(amount)) OVER (PARTITION BY product_category)) * 100, 2) AS pct_share
```

### C. Análisis de Brecha Transaccional con `LEAD()`
Mide el tiempo transcurrido (en días) hasta la siguiente operación. Demuestra cuantitativamente cómo los clientes en proceso de deserción dilatan sus intervalos de consumo antes de abandonar por completo.

### D. Segmentación RFM en SQL Puro con `NTILE(5)`
Calcula los quintiles de Recencia, Frecuencia y Monto y clasifica a la cartera en segmentos como **Campeones**, **Leales**, **En Riesgo** e **Hibernando**.

---

## 📊 6. Dashboard en Power BI & Medidas DAX

El proyecto incluye más de 12 medidas DAX estratégicas documentadas en [`power_bi/DAX_MEASURES.md`](file:///c:/Users/italo/Documents/Ciclo%202026-2/Proyectos/Plataforma%20End-to-End%20de%20Churn%20%26%20Segmentación%20de%20Clientes%20Financieros/power_bi/DAX_MEASURES.md):

### Ejemplos Clave de DAX Implementado:

* **Tasa de Churn (%):**
  ```dax
  Tasa de Churn = 
  DIVIDE([Clientes Churn], [Total Clientes], 0)
  ```

* **Customer Lifetime Value (LTV):**
  ```dax
  Customer Lifetime Value (LTV) = 
  AVERAGEX(
      VALUES(Dim_Customer[customer_key]),
      [Ingresos Comisiones Banco] + ([Volumen Total Transaccionado] * 0.012)
  )
  ```

* **Fugas en el Periodo utilizando `USERELATIONSHIP`:**
  Activa la relación inactiva entre la fecha de cancelación del cliente (`Dim_Customer[churn_date]`) y el calendario (`Dim_Date[full_date]`), permitiendo cruzar temporalmente eventos que no dependen de la fecha de transacción ordinaria:
  ```dax
  Fugas en el Periodo = 
  CALCULATE(
      DISTINCTCOUNT(Dim_Customer[customer_key]),
      USERELATIONSHIP(Dim_Customer[churn_date], Dim_Date[full_date]),
      Dim_Customer[is_churn] = 1,
      NOT(ISBLANK(Dim_Customer[churn_date]))
  )
  ```

* **Volumen Transaccional Acumulado Anual con `DATESYTD`:**
  ```dax
  Volumen Transaccional YTD = 
  CALCULATE(
      [Volumen Total Transaccionado],
      DATESYTD(Dim_Date[full_date])
  )
  ```

---

## 🤖 7. Machine Learning & Inteligencia Artificial

### 1. Clustering K-Means (No Supervisado)
* **Variables empleadas:** Recencia (días), Frecuencia, Gasto Total, Ticket Promedio, Ratio de Digitalización, Comisiones Aportadas, Score Crediticio y Antigüedad.
* **Preprocesamiento:** Transformación logarítmica (`log1p`) para corregir el sesgo asimétrico y normalización con `StandardScaler`.
* **Diagnóstico de K Óptimo:** Evaluación conjunta mediante el **Método del Codo (Inercia / WCSS)** y el **Coeficiente de Silueta** (gráfico exportado en `reports/elbow_silhouette_analysis.png`).
* **Hallazgos:**
  * **Cluster Inactivo / Alto Riesgo Churn:** 528 clientes, inactividad media de 707 días y 92.6% de tasa de fuga histórica.
  * **Cluster Tradicional / Consumo Moderado:** 1,904 clientes de banca retail masiva con alta fidelidad (tasa churn solo 4.25%).
  * **Cluster Wealth / Clientes VIP:** 568 clientes de alto patrimonio con gasto promedio superior a $57,800 y ticket promedio de $1,746.

### 2. Clasificador Predictivo de Churn (Supervisado)
* **Algoritmo:** `RandomForestClassifier` balanceado con 150 estimadores.
* **Desempeño:** **ROC-AUC en prueba = 0.9989**, Accuracy = 98%, F1-Score = 0.95 para la clase minoritaria (Churn).
* **Exportación de Scoring:** Cada cliente en `data/processed/customer_churn_scored.csv` cuenta con una probabilidad individual de fuga (`churn_probability`) y una etiqueta de riesgo (`Riesgo Bajo`, `Moderado`, `Alto`, `Crítico`).

---

## 🚀 8. Guía de Ejecución Rápida (1-Click)

### Requisitos Previos:
* Python 3.10 o superior (recomendado 3.12).
* Git instalado.

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/italo04/plataforma-churn-segmentacion-financiera.git
cd plataforma-churn-segmentacion-financiera
```

### Paso 2: Crear el Entorno Virtual e Instalar Dependencias
```bash
# En Windows (PowerShell)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 3: Ejecutar Todo el Pipeline Automatizado
```bash
python run_project.py
```
*Este comando orquesta automáticamente la generación de datos crudos, el proceso ETL, la carga y verificación en la base de datos relacional, el clustering K-Means y el modelo de scoring predictivo.*

---

## 📋 9. Pasos Manuales que Debes Realizar

Para completar la puesta en marcha al 100%, solo debes seguir estos sencillos pasos manuales:

### 1. Publicar el Proyecto en tu Cuenta de GitHub:
1. Ve a [GitHub](https://github.com/) e inicia sesión.
2. Haz clic en **New repository** y nómbralo (por ejemplo: `plataforma-churn-segmentacion-financiera`). Déjalo público y **no marques** "Add README" ni ".gitignore" (ya los tenemos listos).
3. En tu terminal local, ejecuta:
   ```bash
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO_GITHUB/plataforma-churn-segmentacion-financiera.git
   git push -u origin main
   ```

### 2. Abrir Power BI Desktop y Conectar los Datos:
1. Abre **Power BI Desktop**.
2. Sigue la guía paso a paso descrita en [`power_bi/powerbi_dashboard_guide.md`](file:///c:/Users/italo/Documents/Ciclo%202026-2/Proyectos/Plataforma%20End-to-End%20de%20Churn%20%26%20Segmentación%20de%20Clientes%20Financieros/power_bi/powerbi_dashboard_guide.md).
3. Importa los archivos CSV de `data/processed/`.
4. Copia las fórmulas DAX desde [`power_bi/dax_measures.dax`](file:///c:/Users/italo/Documents/Ciclo%202026-2/Proyectos/Plataforma%20End-to-End%20de%20Churn%20%26%20Segmentación%20de%20Clientes%20Financieros/power_bi/dax_measures.dax).

### 3. (Opcional) Probar las Consultas SQL en PostgreSQL:
Si deseas correr las consultas en una instancia real de PostgreSQL:
1. Crea una base de datos llamada `bank_dw` en tu pgAdmin o cliente preferido.
2. Ejecuta:
   ```bash
   python src/database/load_to_db.py --db-type postgresql --url postgresql://postgres:tu_password@localhost:5432/bank_dw
   ```
3. Abre y ejecuta los archivos de la carpeta `sql/` para ver los resultados analíticos.

---

## 👨‍💻 Autor y Contacto
* **Desarrollador:** Italo Mijail
* **Email:** italomijail@gmail.com
* **Especialidad:** Ingeniería de Datos, Analítica Avanzada, Machine Learning & Business Intelligence Financiero.
