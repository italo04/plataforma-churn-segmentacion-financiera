-- ============================================================================
-- PROYECTO: Plataforma End-to-End de Churn & Segmentación de Clientes Financieros
-- ARCHIVO: 02_analytical_queries.sql
-- DESCRIPCIÓN: Consultas Analíticas Avanzadas con CTEs y Window Functions
-- FUNCIONES CLAVE: RANK(), DENSE_RANK(), LAG(), LEAD(), SUM/AVG OVER()
-- ============================================================================

-- ----------------------------------------------------------------------------
-- CONSULTA 1: Detección Temprana de Fuga mediante Análisis Mes a Mes (MoM) con LAG()
-- OBJETIVO: Medir la contracción de gasto y transacciones de cada cliente respecto
-- al mes anterior. Si la caída de gasto supera el 50%, se genera una alerta temprana.
-- ----------------------------------------------------------------------------
WITH monthly_customer_activity AS (
    SELECT 
        c.customer_id,
        c.full_name,
        c.customer_segment,
        d.year_month,
        COUNT(f.transaction_key) AS total_transactions,
        SUM(f.amount) AS current_month_spend,
        AVG(f.amount) AS avg_monthly_ticket
    FROM fact_transactions f
    INNER JOIN dim_customer c ON f.customer_key = c.customer_key
    INNER JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.status = 'Completed'
    GROUP BY c.customer_id, c.full_name, c.customer_segment, d.year_month
),
monthly_variations AS (
    SELECT 
        customer_id,
        full_name,
        customer_segment,
        year_month,
        total_transactions,
        current_month_spend,
        -- Gasto del mes anterior para el mismo cliente mediante LAG
        LAG(current_month_spend, 1) OVER (
            PARTITION BY customer_id 
            ORDER BY year_month ASC
        ) AS previous_month_spend,
        -- Transacciones del mes anterior
        LAG(total_transactions, 1) OVER (
            PARTITION BY customer_id 
            ORDER BY year_month ASC
        ) AS previous_month_tx
    FROM monthly_customer_activity
)
SELECT 
    customer_id,
    full_name,
    customer_segment,
    year_month,
    current_month_spend,
    COALESCE(previous_month_spend, 0) AS previous_month_spend,
    ROUND(current_month_spend - COALESCE(previous_month_spend, 0), 2) AS spend_difference_mom,
    CASE 
        WHEN previous_month_spend IS NULL OR previous_month_spend = 0 THEN 0.0
        ELSE ROUND(((current_month_spend - previous_month_spend) / previous_month_spend) * 100, 2)
    END AS pct_growth_mom,
    -- Regla de negocio de Alerta Preventiva de Churn
    CASE 
        WHEN previous_month_spend > 0 
             AND ((current_month_spend - previous_month_spend) / previous_month_spend) < -0.50 
        THEN 'ALERTA: Caída Crítica > 50%'
        WHEN previous_month_spend > 0 
             AND ((current_month_spend - previous_month_spend) / previous_month_spend) < -0.20 
        THEN 'PRECAUCIÓN: Desaceleración'
        ELSE 'Estable / Crecimiento'
    END AS churn_early_warning_status
FROM monthly_variations
ORDER BY customer_id, year_month;


-- ----------------------------------------------------------------------------
-- CONSULTA 2: Ranking de Clientes Top por Categoría de Producto con RANK() y DENSE_RANK()
-- OBJETIVO: Identificar a los 5 clientes con mayor volumen transaccional en cada
-- categoría de producto y calcular su peso relativo (% del volumen total de la categoría).
-- ----------------------------------------------------------------------------
WITH customer_product_spend AS (
    SELECT 
        p.product_category,
        c.customer_id,
        c.full_name,
        c.customer_segment,
        COUNT(f.transaction_key) AS total_tx,
        SUM(f.amount) AS total_spent_category,
        -- Ventana para obtener el monto total de toda la categoría
        SUM(SUM(f.amount)) OVER (PARTITION BY p.product_category) AS total_category_volume
    FROM fact_transactions f
    INNER JOIN dim_customer c ON f.customer_key = c.customer_key
    INNER JOIN dim_product p ON f.product_key = p.product_key
    WHERE f.status = 'Completed'
    GROUP BY p.product_category, c.customer_id, c.full_name, c.customer_segment
),
ranked_customers AS (
    SELECT 
        product_category,
        customer_id,
        full_name,
        customer_segment,
        total_tx,
        total_spent_category,
        total_category_volume,
        ROUND((total_spent_category / total_category_volume) * 100, 3) AS pct_share_in_category,
        -- Asignación de ranking con RANK y DENSE_RANK
        RANK() OVER (
            PARTITION BY product_category 
            ORDER BY total_spent_category DESC
        ) AS rank_pos,
        DENSE_RANK() OVER (
            PARTITION BY product_category 
            ORDER BY total_spent_category DESC
        ) AS dense_rank_pos
    FROM customer_product_spend
)
SELECT 
    product_category,
    rank_pos,
    customer_id,
    full_name,
    customer_segment,
    total_tx,
    ROUND(total_spent_category, 2) AS total_spent_category,
    pct_share_in_category
FROM ranked_customers
WHERE rank_pos <= 5
ORDER BY product_category, rank_pos ASC;


-- ----------------------------------------------------------------------------
-- CONSULTA 3: Análisis de Trayectoria con Media Móvil (Rolling 3M) y Gasto Acumulado
-- OBJETIVO: Evaluar el comportamiento histórico suavizado (Moving Average de 3 meses)
-- y el LTV acumulativo (Running Total) de los clientes bancarios.
-- ----------------------------------------------------------------------------
WITH monthly_spend AS (
    SELECT 
        c.customer_id,
        c.full_name,
        d.year_month,
        SUM(f.amount) AS monthly_spend
    FROM fact_transactions f
    INNER JOIN dim_customer c ON f.customer_key = c.customer_key
    INNER JOIN dim_date d ON f.date_key = d.date_key
    WHERE f.status = 'Completed'
    GROUP BY c.customer_id, c.full_name, d.year_month
)
SELECT 
    customer_id,
    full_name,
    year_month,
    monthly_spend,
    -- Media Móvil de los últimos 3 meses (2 precedentes + actual)
    ROUND(AVG(monthly_spend) OVER (
        PARTITION BY customer_id 
        ORDER BY year_month ASC 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3m_avg_spend,
    -- Gasto acumulado de por vida (Running Total / LTV Dinámico)
    ROUND(SUM(monthly_spend) OVER (
        PARTITION BY customer_id 
        ORDER BY year_month ASC 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS cumulative_lifetime_spend
FROM monthly_spend
ORDER BY customer_id, year_month;


-- ----------------------------------------------------------------------------
-- CONSULTA 4: Análisis de Cohortes de Adquisición y Tasa de Churn Global
-- OBJETIVO: Medir la tasa de retención y volumen promedio según el año de alta.
-- ----------------------------------------------------------------------------
WITH cohort_summary AS (
    SELECT 
        c.acquisition_year,
        c.customer_segment,
        COUNT(DISTINCT c.customer_key) AS total_customers_acquired,
        SUM(c.is_churn) AS total_churned,
        SUM(CASE WHEN c.is_churn = 0 THEN 1 ELSE 0 END) AS total_active_retained,
        AVG(c.tenure_months) AS avg_tenure_months
    FROM dim_customer c
    GROUP BY c.acquisition_year, c.customer_segment
)
SELECT 
    acquisition_year,
    customer_segment,
    total_customers_acquired,
    total_active_retained,
    total_churned,
    ROUND((total_churned::NUMERIC / total_customers_acquired::NUMERIC) * 100, 2) AS churn_rate_pct,
    ROUND(((total_customers_acquired - total_churned)::NUMERIC / total_customers_acquired::NUMERIC) * 100, 2) AS retention_rate_pct,
    ROUND(avg_tenure_months, 1) AS avg_tenure_months
FROM cohort_summary
ORDER BY acquisition_year DESC, customer_segment;


-- ----------------------------------------------------------------------------
-- CONSULTA 5: Patrón de Deserción con LEAD() (Días hasta la siguiente transacción)
-- OBJETIVO: Utilizar LEAD para calcular la brecha en días entre una transacción
-- y la subsecuente, demostrando que los clientes que fugan aumentan su intervalo.
-- ----------------------------------------------------------------------------
WITH tx_with_lead AS (
    SELECT 
        f.customer_key,
        c.customer_id,
        c.is_churn,
        f.transaction_date,
        -- Siguiente fecha de transacción para el mismo cliente
        LEAD(f.transaction_date, 1) OVER (
            PARTITION BY f.customer_key 
            ORDER BY f.transaction_date ASC
        ) AS next_tx_date
    FROM fact_transactions f
    INNER JOIN dim_customer c ON f.customer_key = c.customer_key
    WHERE f.status = 'Completed'
),
gaps_calculated AS (
    SELECT 
        customer_id,
        is_churn,
        transaction_date,
        next_tx_date,
        EXTRACT(EPOCH FROM (next_tx_date - transaction_date)) / 86400 AS days_to_next_tx
    FROM tx_with_lead
    WHERE next_tx_date IS NOT NULL
)
SELECT 
    CASE WHEN is_churn = 1 THEN 'Cliente Churn / Cancelado' ELSE 'Cliente Fiel / Retenido' END AS customer_status,
    ROUND(AVG(days_to_next_tx), 1) AS avg_days_between_tx,
    ROUND(MAX(days_to_next_tx), 1) AS max_gap_days,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_to_next_tx), 1) AS median_gap_days
FROM gaps_calculated
GROUP BY is_churn;
