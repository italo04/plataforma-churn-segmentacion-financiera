# Guía Maestra de Medidas DAX: Plataforma de Churn & Segmentación Financiera

Este documento contiene la definición técnica, el propósito de negocio y la sintaxis exacta de las **medidas DAX avanzadas** diseñadas para el modelo tabular de Power BI. Cumple con los requerimientos corporativos bancarios incorporando funciones como `CALCULATE`, `USERELATIONSHIP`, `DATESYTD`, `DATEADD`, `DIVIDE` y `AVERAGEX`.

---

## 1. Tabla de Medidas Principales

| # | Nombre de la Medida | Función Clave | Categoría |
|---|---------------------|----------------|-----------|
| 1 | `Total Clientes` | `DISTINCTCOUNT` | Volumen Base |
| 2 | `Clientes Churn` | `CALCULATE` | Deserción |
| 3 | `Clientes Activos` | `CALCULATE` | Retención |
| 4 | `Tasa de Churn (%)` | `DIVIDE` | KPI Estratégico |
| 5 | `Tasa de Retención (%)` | Aritmética | KPI Estratégico |
| 6 | `Volumen Total Transaccionado` | `CALCULATE` | Desempeño Financiero |
| 7 | `Ticket Promedio` | `DIVIDE` | Hábitos de Consumo |
| 8 | `Ingresos por Comisiones (Fees)` | `SUM` | Rentabilidad Banco |
| 9 | `Customer Lifetime Value (LTV)` | `AVERAGEX`, `CALCULATE` | Valor del Cliente |
| 10 | `Fugas en el Periodo (USERELATIONSHIP)` | `USERELATIONSHIP` | Time Intelligence Inactiva |
| 11 | `Altas Nuevas en el Periodo (USERELATIONSHIP)` | `USERELATIONSHIP` | Time Intelligence Inactiva |
| 12 | `Volumen Transaccional YTD` | `DATESYTD` | Time Intelligence Acumulada |
| 13 | `Fugas Acumuladas YTD` | `DATESYTD`, `USERELATIONSHIP` | Time Intelligence Acumulada |
| 14 | `Crecimiento MoM Volumen (%)` | `DATEADD` | Variación Mensual |
| 15 | `Ratio de Digitalización (%)` | `DIVIDE` | Omnicanalidad |

---

## 2. Detalle y Código DAX de Cada Medida

### 1. Total Clientes
* **Objetivo:** Contar la cantidad única de clientes en el contexto de filtro actual.
```dax
Total Clientes = 
DISTINCTCOUNT(Dim_Customer[customer_key])
```

---

### 2. Clientes Churn
* **Objetivo:** Cuantificar los clientes que han cancelado o abandonado sus productos (`is_churn = 1`).
* **Función Clave:** `CALCULATE` modifica el contexto de filtro agregando la condición booleana.
```dax
Clientes Churn = 
CALCULATE(
    DISTINCTCOUNT(Dim_Customer[customer_key]),
    Dim_Customer[is_churn] = 1
)
```

---

### 3. Clientes Activos
* **Objetivo:** Filtrar los clientes vigentes y operativos en la institución (`is_active = 1`).
```dax
Clientes Activos = 
CALCULATE(
    DISTINCTCOUNT(Dim_Customer[customer_key]),
    Dim_Customer[is_active] = 1
)
```

---

### 4. Tasa de Churn (%)
* **Objetivo:** Porcentaje de la base de clientes que ha desertado. Utiliza `DIVIDE` para prevenir errores de división entre cero.
```dax
Tasa de Churn = 
DIVIDE(
    [Clientes Churn],
    [Total Clientes],
    0
)
```
*(Formatear en Power BI como Porcentaje: `0.00%`)*

---

### 5. Tasa de Retención (%)
* **Objetivo:** Mide la capacidad del banco para retener su cartera activa (complemento de la tasa de churn).
```dax
Tasa de Retención = 
1 - [Tasa de Churn]
```
*(Formatear en Power BI como Porcentaje: `0.00%`)*

---

### 6. Volumen Total Transaccionado
* **Objetivo:** Suma monetaria de todas las operaciones aprobadas y completadas por los clientes.
```dax
Volumen Total Transaccionado = 
CALCULATE(
    SUM(Fact_Transactions[amount]),
    Fact_Transactions[status] = "Completed"
)
```
*(Formatear en Power BI como Moneda: `$#,##0.00`)*

---

### 7. Ticket Promedio
* **Objetivo:** Monto promedio transaccionado por cada operación completada.
```dax
Ticket Promedio = 
DIVIDE(
    [Volumen Total Transaccionado],
    CALCULATE(
        COUNT(Fact_Transactions[transaction_key]),
        Fact_Transactions[status] = "Completed"
    ),
    0
)
```
*(Formatear en Power BI como Moneda: `$#,##0.00`)*

---

### 8. Ingresos por Comisiones (Fees)
* **Objetivo:** Captura el margen neto generado directamente por tarifas, comisiones de retiro y mantenimiento.
```dax
Ingresos Comisiones Banco = 
SUM(Fact_Transactions[fee_amount])
```

---

### 9. Customer Lifetime Value (LTV)
* **Objetivo:** Valor presente esperado del flujo de beneficios que un cliente aporta a lo largo de su relación con el banco. Combina el margen por comisiones más un spread de intermediación financiera (1.2% del volumen total).
```dax
Customer Lifetime Value (LTV) = 
AVERAGEX(
    VALUES(Dim_Customer[customer_key]),
    [Ingresos Comisiones Banco] + ([Volumen Total Transaccionado] * 0.012)
)
```
*(Formatear en Power BI como Moneda: `$#,##0.00`)*

---

### 10. Fugas en el Periodo (USERELATIONSHIP)
* **Objetivo:** En el modelo de datos, la relación activa entre `Dim_Date` y los hechos es `Fact_Transactions[date_key]`. Sin embargo, para analizar cuántos clientes cancelaron **en un mes específico del calendario**, se debe activar la relación inactiva entre `Dim_Customer[churn_date]` y `Dim_Date[full_date]`.
* **Función Clave:** `USERELATIONSHIP` permite activar relaciones no activas dentro del cálculo.
```dax
Fugas en el Periodo = 
CALCULATE(
    DISTINCTCOUNT(Dim_Customer[customer_key]),
    USERELATIONSHIP(Dim_Customer[churn_date], Dim_Date[full_date]),
    Dim_Customer[is_churn] = 1,
    NOT(ISBLANK(Dim_Customer[churn_date]))
)
```

---

### 11. Altas Nuevas en el Periodo (USERELATIONSHIP)
* **Objetivo:** Contabilizar las altas comerciales de nuevos clientes según su fecha de adquisición, activando la relación secundaria con `Dim_Date`.
```dax
Altas Nuevas en el Periodo = 
CALCULATE(
    DISTINCTCOUNT(Dim_Customer[customer_key]),
    USERELATIONSHIP(Dim_Customer[acquisition_date], Dim_Date[full_date])
)
```

---

### 12. Volumen Transaccional YTD (DATESYTD)
* **Objetivo:** Acumulado anual hasta la fecha (Year-To-Date) del volumen operado.
* **Función Clave:** `DATESYTD` evalúa el rango de fechas desde el 1 de enero hasta la fecha máxima seleccionada.
```dax
Volumen Transaccional YTD = 
CALCULATE(
    [Volumen Total Transaccionado],
    DATESYTD(Dim_Date[full_date])
)
```

---

### 13. Fugas Acumuladas YTD (DATESYTD + USERELATIONSHIP)
* **Objetivo:** Suma acumulada anual de clientes fugados en el transcurso del año comercial.
```dax
Fugas Acumuladas YTD = 
CALCULATE(
    [Fugas en el Periodo],
    DATESYTD(Dim_Date[full_date])
)
```

---

### 14. Crecimiento MoM Volumen (%)
* **Objetivo:** Calcular la tasa de variación porcentual respecto al mes inmediatamente anterior.
* **Función Clave:** `DATEADD` desplaza el intervalo temporal un mes hacia atrás.
```dax
Crecimiento MoM Volumen = 
VAR MesActual = [Volumen Total Transaccionado]
VAR MesAnterior = 
    CALCULATE(
        [Volumen Total Transaccionado],
        DATEADD(Dim_Date[full_date], -1, MONTH)
    )
RETURN
DIVIDE(MesActual - MesAnterior, MesAnterior, 0)
```
*(Formatear en Power BI como Porcentaje: `+0.00%;-0.00%;0.00%`)*

---

### 15. Ratio de Digitalización (%)
* **Objetivo:** Medir el grado de autoservicio digital de los clientes evaluando transacciones efectuadas por Mobile App y Web Banking.
```dax
Ratio de Digitalización = 
VAR TransaccionesDigitales = 
    CALCULATE(
        COUNT(Fact_Transactions[transaction_key]),
        Fact_Transactions[channel] IN {"Mobile App", "Web Banking"},
        Fact_Transactions[status] = "Completed"
    )
VAR TotalTransacciones = 
    CALCULATE(
        COUNT(Fact_Transactions[transaction_key]),
        Fact_Transactions[status] = "Completed"
    )
RETURN
DIVIDE(TransaccionesDigitales, TotalTransacciones, 0)
```
*(Formatear en Power BI como Porcentaje: `0.00%`)*
