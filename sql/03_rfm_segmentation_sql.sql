-- ============================================================================
-- PROYECTO: Plataforma End-to-End de Churn & Segmentación de Clientes Financieros
-- ARCHIVO: 03_rfm_segmentation_sql.sql
-- DESCRIPCIÓN: Segmentación RFM (Recencia, Frecuencia, Monto) directamente en SQL
-- TÉCNICAS: CTEs, Window Functions con NTILE(5), y reglas de negocio bancarias
-- ============================================================================

WITH rfm_base_metrics AS (
    SELECT 
        c.customer_key,
        c.customer_id,
        c.full_name,
        c.customer_segment,
        c.is_churn,
        -- Recencia: Días desde la última transacción hasta la fecha de corte ('2026-11-01')
        ('2026-11-01'::DATE - MAX(f.transaction_date)::DATE) AS recency_days,
        -- Frecuencia: Cantidad total de transacciones completadas
        COUNT(f.transaction_key) AS frequency,
        -- Monto: Suma monetaria total transaccionada
        SUM(f.amount) AS monetary_value,
        -- Ticket Promedio
        AVG(f.amount) AS avg_ticket
    FROM dim_customer c
    INNER JOIN fact_transactions f ON c.customer_key = f.customer_key
    WHERE f.status = 'Completed'
    GROUP BY c.customer_key, c.customer_id, c.full_name, c.customer_segment, c.is_churn
),
rfm_quintiles AS (
    SELECT 
        customer_key,
        customer_id,
        full_name,
        customer_segment,
        is_churn,
        recency_days,
        frequency,
        monetary_value,
        avg_ticket,
        -- NTILE(5) asigna valores de 1 a 5 distribuidos equitativamente
        -- Para Recencia: Menor número de días es MEJOR (ORDER BY recency_days DESC para dar 5 al más reciente)
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        -- Para Frecuencia: Mayor número de transacciones es MEJOR (ORDER BY frequency ASC)
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        -- Para Monto: Mayor valor monetario es MEJOR (ORDER BY monetary_value ASC)
        NTILE(5) OVER (ORDER BY monetary_value ASC) AS m_score
    FROM rfm_base_metrics
),
rfm_scored AS (
    SELECT 
        customer_key,
        customer_id,
        full_name,
        customer_segment,
        is_churn,
        recency_days,
        frequency,
        monetary_value,
        avg_ticket,
        r_score,
        f_score,
        m_score,
        -- Concatenación de puntuación RFM (Ej: '555', '124')
        (r_score::TEXT || f_score::TEXT || m_score::TEXT) AS rfm_code,
        ROUND((r_score + f_score + m_score)::NUMERIC / 3, 2) AS rfm_composite_score
    FROM rfm_quintiles
)
SELECT 
    customer_id,
    full_name,
    customer_segment,
    is_churn,
    recency_days,
    frequency,
    ROUND(monetary_value, 2) AS monetary_value,
    ROUND(avg_ticket, 2) AS avg_ticket,
    r_score,
    f_score,
    m_score,
    rfm_code,
    rfm_composite_score,
    -- Clasificación en Segmentos Comerciales de RFM
    CASE 
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN '1. Campeones (Champions)'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN '2. Clientes Leales (Loyal)'
        WHEN r_score >= 4 AND f_score BETWEEN 1 AND 3 THEN '3. Potenciales Fieles (Potential)'
        WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN '4. Clientes en Riesgo (At Risk)'
        WHEN r_score <= 2 AND f_score <= 2 AND m_score >= 3 THEN '5. Clientes Dormidos de Alto Valor'
        WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN '6. Hibernando / Desconectados'
        WHEN r_score = 1 AND f_score = 1 THEN '7. Perdidos / Inactivos'
        ELSE '8. Clientes Promedio / Necesitan Impulso'
    END AS rfm_customer_segment
FROM rfm_scored
ORDER BY monetary_value DESC;
