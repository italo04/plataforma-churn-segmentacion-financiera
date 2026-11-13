-- ============================================================================
-- PROYECTO: Plataforma End-to-End de Churn & Segmentación de Clientes Financieros
-- ARCHIVO: 01_schema_star_ddl.sql
-- DESCRIPCIÓN: Definición del Esquema Estrella (Star Schema) para Data Warehouse
-- COMPATIBILIDAD: PostgreSQL 14+ / SQL Server / SQLite (ANSI SQL)
-- ============================================================================

-- Eliminar tablas previas si existen (en orden de dependencia)
DROP TABLE IF EXISTS fact_transactions CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_product CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- ----------------------------------------------------------------------------
-- 1. DIMENSIÓN FECHA / TIEMPO (Dim_Date)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,                       -- Clave subrogada: YYYYMMDD (Ej: 20240115)
    full_date DATE NOT NULL,                        -- Fecha completa YYYY-MM-DD
    year INT NOT NULL,                              -- Año (Ej: 2024)
    quarter INT NOT NULL,                           -- Trimestre numérico (1 a 4)
    quarter_name VARCHAR(10) NOT NULL,              -- Etiqueta trimestre (Ej: 'T1', 'T2')
    month_number INT NOT NULL,                      -- Mes numérico (1 a 12)
    month_name VARCHAR(20) NOT NULL,                -- Nombre del mes en español
    year_month VARCHAR(7) NOT NULL,                 -- Periodo YYYY-MM (Ej: '2024-01')
    week_of_year INT NOT NULL,                      -- Semana del año ISO
    day_of_month INT NOT NULL,                      -- Día del mes (1 a 31)
    day_of_week INT NOT NULL,                       -- Día de la semana (1=Lunes, 7=Domingo)
    day_name VARCHAR(20) NOT NULL,                  -- Nombre del día en español
    is_weekend SMALLINT NOT NULL DEFAULT 0          -- Flag fin de semana (1=Sí, 0=No)
);

CREATE INDEX idx_dim_date_full_date ON dim_date(full_date);
CREATE INDEX idx_dim_date_year_month ON dim_date(year_month);

-- ----------------------------------------------------------------------------
-- 2. DIMENSIÓN CLIENTES (Dim_Customer)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_customer (
    customer_key INT PRIMARY KEY,                   -- Clave subrogada de dimensión
    customer_id VARCHAR(20) NOT NULL UNIQUE,        -- Clave de negocio (Ej: 'CUST_0001')
    full_name VARCHAR(120) NOT NULL,                -- Nombre completo del cliente
    gender CHAR(1) NOT NULL,                        -- Género ('M', 'F')
    age INT NOT NULL,                               -- Edad
    age_group VARCHAR(20) NOT NULL,                 -- Grupo etario ('< 25', '25-34', '35-49', '50-64', '65+')
    annual_income NUMERIC(12, 2) NOT NULL,          -- Ingreso anual estimado
    income_bracket VARCHAR(30) NOT NULL,            -- Tramo de ingresos
    credit_score INT NOT NULL,                      -- Puntaje crediticio (300 - 850)
    credit_tier VARCHAR(30) NOT NULL,               -- Rango crediticio ('Excelente', 'Bueno', etc.)
    customer_segment VARCHAR(40) NOT NULL,          -- Segmento comercial ('Retail', 'Wealth', 'SME')
    region VARCHAR(40) NOT NULL,                    -- Región geográfica
    acquisition_date DATE NOT NULL,                 -- Fecha de alta del cliente
    acquisition_year INT NOT NULL,                  -- Año de alta
    tenure_months NUMERIC(6, 1) NOT NULL,           -- Antigüedad en meses
    is_active SMALLINT NOT NULL DEFAULT 1,          -- Estado de cuenta (1=Activo, 0=Inactivo)
    is_churn SMALLINT NOT NULL DEFAULT 0,           -- Indicador de fuga/cancelación (1=Churn, 0=Retenido)
    churn_date DATE,                                -- Fecha en la que canceló (NULL si sigue activo)
    churn_reason VARCHAR(100)                       -- Motivo declarado o inferido del abandono
);

CREATE INDEX idx_dim_cust_id ON dim_customer(customer_id);
CREATE INDEX idx_dim_cust_segment ON dim_customer(customer_segment);
CREATE INDEX idx_dim_cust_churn ON dim_customer(is_churn);
CREATE INDEX idx_dim_cust_region ON dim_customer(region);

-- ----------------------------------------------------------------------------
-- 3. DIMENSIÓN PRODUCTOS (Dim_Product)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_product (
    product_key INT PRIMARY KEY,                    -- Clave subrogada de dimensión
    product_id VARCHAR(20) NOT NULL UNIQUE,         -- Clave de negocio (Ej: 'PROD_01')
    product_name VARCHAR(100) NOT NULL,             -- Nombre comercial del producto
    product_category VARCHAR(50) NOT NULL,          -- Categoría ('Cuentas', 'Tarjetas', 'Préstamos', etc.)
    monthly_fee NUMERIC(8, 2) NOT NULL DEFAULT 0.0, -- Costo de mantenimiento mensual
    interest_rate NUMERIC(6, 4) NOT NULL DEFAULT 0.0 -- Tasa de interés efectiva anual / aplicada
);

CREATE INDEX idx_dim_product_cat ON dim_product(product_category);

-- ----------------------------------------------------------------------------
-- 4. TABLA DE HECHOS TRANSACCIONALES (Fact_Transactions)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_transactions (
    transaction_key BIGINT PRIMARY KEY,             -- Clave subrogada del hecho
    transaction_id VARCHAR(30) NOT NULL UNIQUE,     -- Clave de negocio transaccional
    customer_key INT NOT NULL,                      -- FK hacia Dim_Customer
    product_key INT NOT NULL,                       -- FK hacia Dim_Product
    date_key INT NOT NULL,                          -- FK hacia Dim_Date
    transaction_date TIMESTAMP NOT NULL,            -- Fecha y hora exacta del evento
    channel VARCHAR(30) NOT NULL,                   -- Canal ('Mobile App', 'POS', 'Web', 'ATM', 'Branch')
    transaction_type VARCHAR(50) NOT NULL,          -- Tipo ('Consumo', 'Transferencia', etc.)
    amount NUMERIC(14, 2) NOT NULL,                 -- Monto de la transacción en moneda local
    fee_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.0, -- Comisión bancaria retenida
    net_bank_revenue NUMERIC(10, 2) NOT NULL DEFAULT 0.0, -- Ingreso neto para la entidad
    status VARCHAR(20) NOT NULL,                    -- Estado ('Completed', 'Pending', 'Failed', 'Reversed')
    
    CONSTRAINT fk_fact_customer FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
    CONSTRAINT fk_fact_product FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    CONSTRAINT fk_fact_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

CREATE INDEX idx_fact_tx_customer ON fact_transactions(customer_key);
CREATE INDEX idx_fact_tx_product ON fact_transactions(product_key);
CREATE INDEX idx_fact_tx_date ON fact_transactions(date_key);
CREATE INDEX idx_fact_tx_channel ON fact_transactions(channel);
CREATE INDEX idx_fact_tx_status ON fact_transactions(status);
CREATE INDEX idx_fact_tx_timestamp ON fact_transactions(transaction_date);

-- Comentarios explicativos sobre el modelado
COMMENT ON TABLE dim_customer IS 'Dimensión de clientes bancarios con atributos sociodemográficos y estados de retención/churn';
COMMENT ON TABLE dim_product IS 'Catálogo de productos financieros ofrecidos por el banco';
COMMENT ON TABLE dim_date IS 'Dimensión calendario para análisis temporal y Time Intelligence';
COMMENT ON TABLE fact_transactions IS 'Tabla de hechos de transacciones bancarias normalizadas bajo esquema estrella';
