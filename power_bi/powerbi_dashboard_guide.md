# Manual de Implementación Visual en Power BI Desktop

Este manual detalla paso a paso cómo construir el Dashboard interactivo en **Power BI Desktop**, configurar el **Modelo Estrella (Star Schema)**, establecer las **relaciones activas e inactivas** para las medidas DAX con `USERELATIONSHIP`, y diseñar las **4 páginas analíticas**.

---

## Paso 1: Conexión e Importación de Datos

1. Abre **Power BI Desktop**.
2. En la pestaña **Inicio**, selecciona **Obtener datos** -> **Texto/CSV** (o Carpeta de datos).
3. Importa los siguientes archivos ubicados en la carpeta `data/processed/`:
   * `dim_dates.csv` -> Renombrar la tabla en Power BI a: `Dim_Date`
   * `dim_customers.csv` -> Renombrar a: `Dim_Customer`
   * `dim_products.csv` -> Renombrar a: `Dim_Product`
   * `fact_transactions.csv` -> Renombrar a: `Fact_Transactions`
   * `customer_clusters_segmented.csv` -> Renombrar a: `Dim_Customer_Clusters` (o usar como tabla analítica)

> **Verificación de Tipos de Datos:**
> * `Dim_Date[date_key]`, `Fact_Transactions[date_key]`: Tipo **Número entero**.
> * `Dim_Date[full_date]`, `Dim_Customer[churn_date]`, `Dim_Customer[acquisition_date]`: Tipo **Fecha**.
> * `Fact_Transactions[amount]`, `fee_amount`: Tipo **Número decimal fijo (Moneda)**.

---

## Paso 2: Configuración del Modelo Relacional (Vista de Modelo)

Navega a la **Vista de Modelo** en el panel izquierdo y configura las relaciones tal como se describe a continuación:

### Relaciones Activas (Filtro Dirección Única `1:*`):
1. `Dim_Date[date_key]` **(1)** ----> **(*)** `Fact_Transactions[date_key]` *(Activa)*
2. `Dim_Customer[customer_key]` **(1)** ----> **(*)** `Fact_Transactions[customer_key]` *(Activa)*
3. `Dim_Product[product_key]` **(1)** ----> **(*)** `Fact_Transactions[product_key]` *(Activa)*
4. `Dim_Customer[customer_key]` **(1)** ----> **(1)** `Dim_Customer_Clusters[customer_key]` *(Opcional si no se fusionaron)*

### Relaciones Inactivas (Para funciones `USERELATIONSHIP`):
5. `Dim_Date[full_date]` **(1)** ----> **(*)** `Dim_Customer[churn_date]` *(Desmarcar la casilla "Hacer activa esta relación")*
6. `Dim_Date[full_date]` **(1)** ----> **(*)** `Dim_Customer[acquisition_date]` *(Desmarcar la casilla "Hacer activa esta relación")*

```
       +-----------------------+
       |       Dim_Date        |
       +-----------------------+
          | (1)          : (1) Inactiva (churn_date / acq_date)
          |              :
          | (*)          v (*)
+-------------------+   +--------------------+
| Fact_Transactions |   |    Dim_Customer    |
+-------------------+   +--------------------+
   ^ (*)                   ^ (1)
   |                       |
   | (1)                   | (1)
+-------------------+   +--------------------+
|    Dim_Product    |   | Dim_Customer_Clust |
+-------------------+   +--------------------+
```

---

## Paso 3: Creación de la Tabla de Medidas DAX

1. En la pestaña **Inicio**, haz clic en **Especificar datos**.
2. Nombra la tabla como `_Medidas` y pulsa **Cargar**.
3. Haz clic derecho sobre `_Medidas` y selecciona **Nueva medida**.
4. Copia y pega las 15 medidas del archivo `power_bi/dax_measures.dax`.
5. Formatea cada medida:
   * Porcentajes: `Tasa de Churn`, `Tasa de Retención`, `Crecimiento MoM Volumen`, `Ratio de Digitalización` (`0.00%`).
   * Monedas: `Volumen Total Transaccionado`, `Ticket Promedio`, `Customer Lifetime Value (LTV)` (`$#,##0.00`).

---

## Paso 4: Arquitectura y Diseño de las 4 Páginas del Dashboard

### Página 1: Executive KPI Overview (Visión General Ejecutiva)
* **Objetivo:** Brindar a la dirección del banco un pulso inmediato del rendimiento, fuga y valor de cartera.
* **Encabezado / Filtros Superiores (Slicers):**
  * Segmento de Cliente (`Dim_Customer[customer_segment]`)
  * Región Geográfica (`Dim_Customer[region]`)
  * Año y Trimestre (`Dim_Date[year]`, `Dim_Date[quarter_name]`)
* **Fila de Tarjetas KPI (Cards visuales):**
  1. **Tasa de Churn:** `[Tasa de Churn]` (Formato condicional: Rojo si > 20%, Verde si <= 15%).
  2. **Customer Lifetime Value:** `[Customer Lifetime Value (LTV)]`.
  3. **Ticket Promedio:** `[Ticket Promedio]`.
  4. **Volumen Operado YTD:** `[Volumen Transaccional YTD]`.
  5. **Total Clientes Activos:** `[Clientes Activos]`.
* **Gráficos Principales:**
  * **Gráfico de Líneas y Columnas:** Evolución Mensual del Volumen (`[Volumen Total Transaccionado]`) vs. Variación MoM (`[Crecimiento MoM Volumen]`). Eje X: `Dim_Date[year_month]`.
  * **Gráfico de Anillos (Donut Chart):** Distribución de Clientes por Segmento (`Retail`, `Wealth`, `SME`).
  * **Gráfico de Barras Horizontales:** Volumen Operado por Categoría de Producto (`Dim_Product[product_category]`).

---

### Página 2: Customer Churn & Cohort Analysis (Diagnóstico de Fuga)
* **Objetivo:** Comprender por qué, quiénes y cuándo abandonan la entidad.
* **Gráficos Principales:**
  * **Gráfico de Barras Clúster:** Principales Motivos de Fuga (`Dim_Customer[churn_reason]`) ordenados de mayor a menor impacto.
  * **Gráfico de Columnas 100% Apiladas:** Tasa de Churn por Tramo de Score Crediticio (`Dim_Customer[credit_tier]`). Permite visualizar cómo clientes con score bajo tienen tasas de fuga hasta 3x superiores.
  * **Gráfico de Dispersión / Matriz de Cohortes:** Eje Y: Año de Alta (`acquisition_year`), Columnas: Antigüedad en meses (`tenure_months`), Valores: `[Tasa de Churn]`.
  * **Gráfico de Área Temporal con USERELATIONSHIP:** Fugas en el Tiempo utilizando `[Fugas en el Periodo]` contra `Dim_Date[year_month]`. Permite correlacionar picos de fuga con fechas reales del calendario.

---

### Página 3: RFM & AI Machine Learning Segmentation (Segmentación con K-Means)
* **Objetivo:** Explotar la agrupación inteligente para micro-segmentación y campañas de fidelización.
* **Filtros Laterales:**
  * Selector de Cluster K-Means (`Dim_Customer_Clusters[cluster_name]`).
* **Gráficos Principales:**
  * **Gráfico de Dispersión (Scatter Chart):**
    * Eje X: Recencia en días (`recency_days`).
    * Eje Y: Monto Total Transaccionado (`monetary`).
    * Tamaño de Burbuja: Ticket Promedio (`avg_ticket`).
    * Leyenda / Color: Segmento K-Means (`cluster_name`).
  * **Matriz Comparativa de Segmentos:**
    * Filas: `cluster_name`.
    * Columnas de Valores: Clientes, Gasto Promedio, Frecuencia Media, Tasa de Churn, Adopción Digital (%).
  * **Tabla de Detalle Comercial para Activación de Campañas:**
    * Columnas: `customer_id`, `full_name`, `customer_segment`, `cluster_name`, `recency_days`, `LTV`.
    * Permite exportar a Excel para que el equipo comercial contacte a los clientes en riesgo.

---

### Página 4: Omnichannel & Transactional Analytics (Canales y Operaciones)
* **Objetivo:** Evaluar la eficiencia operativa de los canales de atención y cobro de comisiones.
* **Gráficos Principales:**
  * **Gráfico de Treemap:** Transacciones por Canal (`Mobile App`, `POS`, `Web Banking`, `ATM`, `Branch`).
  * **Medidor (Gauge Chart):** `[Ratio de Digitalización]` con meta corporativa del 60%.
  * **Gráfico de Barras Apiladas:** Ingresos por Comisiones (`[Ingresos Comisiones Banco]`) desglosados por Tipo de Transacción (`Compra`, `Transferencia`, `Retiro`).
  * **Tabla Resumen de Comisiones por Producto:** Muestra cuáles productos generan mayor retorno neto para la entidad.

---

## Paso 5: Guía de Estilo y Paleta de Colores Corporativa

Para lograr una apariencia profesional bancaria de nivel internacional, se recomienda:
* **Fondo del Lienzo:** `#F4F6F9` (Gris claro corporativo suave).
* **Color Primario (Tarjetas y Encabezados):** `#0A2540` (Azul marino banco).
* **Color Secundario / Acento:** `#0066F5` (Azul eléctrico fintech).
* **Alertas de Churn / Riesgo:** `#D9383A` (Rojo alerta carmesí).
* **Retención / Salud Financiera:** `#00875A` (Verde esmeralda).
* **Tipografía:** Segoe UI o DIN Pro, tamaño consistente en títulos (18pt negrita) y etiquetas (10pt).
