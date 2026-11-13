"""
Módulo de Generación de Datos Transaccionales Bancarios Sintéticos
-----------------------------------------------------------------
Este script simula una base de datos core de una entidad financiera,
generando clientes, productos y un historial de transacciones con patrones
reales de retención, abandono (churn) y comportamiento de gasto.
"""

import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def set_seeds(seed=42):
    random.seed(seed)
    np.random.seed(seed)

def generate_products():
    """Genera el catálogo de productos financieros."""
    products = [
        {"product_id": "PROD_01", "product_name": "Cuenta de Ahorros Clásica", "product_category": "Cuentas", "monthly_fee": 5.0, "interest_rate": 0.015},
        {"product_id": "PROD_02", "product_name": "Cuenta Corriente Premium", "product_category": "Cuentas", "monthly_fee": 15.0, "interest_rate": 0.005},
        {"product_id": "PROD_03", "product_name": "Tarjeta de Crédito Oro", "product_category": "Tarjetas", "monthly_fee": 20.0, "interest_rate": 0.280},
        {"product_id": "PROD_04", "product_name": "Tarjeta de Crédito Black", "product_category": "Tarjetas", "monthly_fee": 45.0, "interest_rate": 0.240},
        {"product_id": "PROD_05", "product_name": "Préstamo Personal", "product_category": "Préstamos", "monthly_fee": 0.0, "interest_rate": 0.165},
        {"product_id": "PROD_06", "product_name": "Crédito Hipotecario", "product_category": "Préstamos", "monthly_fee": 0.0, "interest_rate": 0.089},
        {"product_id": "PROD_07", "product_name": "Fondo Mutuo Inversión", "product_category": "Inversiones", "monthly_fee": 10.0, "interest_rate": 0.075},
        {"product_id": "PROD_08", "product_name": "Seguro Protección Financiera", "product_category": "Seguros", "monthly_fee": 12.0, "interest_rate": 0.000},
    ]
    return pd.DataFrame(products)

def generate_customers(n_customers=2500, start_date="2022-01-01", end_date="2025-06-30", churn_rate=0.22):
    """
    Genera el padrón de clientes con atributos demográficos, segmentación
    y marcaje de churn realistas.
    """
    first_names_m = ["Carlos", "Luis", "Jorge", "Miguel", "Mateo", "Diego", "Alejandro", "Fernando", "Javier", "Ricardo", "Andrés", "Gabriel", "Sebastián", "Rodrigo", "Daniel"]
    first_names_f = ["Ana", "María", "Lucía", "Valeria", "Sofía", "Camila", "Elena", "Daniela", "Gabriela", "Paola", "Mariana", "Patricia", "Andrea", "Natalia", "Claudia"]
    last_names = ["González", "Rodríguez", "López", "García", "Pérez", "Martínez", "Sánchez", "Romero", "Flores", "Benítez", "Torres", "Ramírez", "Vargas", "Castro", "Morales", "Reyes", "Gutiérrez", "Mendoza", "Silva", "Navarro"]
    regions = ["Metropolitana", "Norte", "Sur", "Centro", "Oriente"]
    region_weights = [0.45, 0.20, 0.15, 0.12, 0.08]
    
    churn_reasons = [
        "Competitor Offer",
        "High Maintenance Fees",
        "Poor Customer Service",
        "Relocation / Change of Residence",
        "Product Dissatisfaction",
        "Digital App Usability Issues"
    ]
    churn_weights = [0.35, 0.25, 0.15, 0.10, 0.10, 0.05]
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days
    
    customers = []
    
    for i in range(1, n_customers + 1):
        cust_id = f"CUST_{i:04d}"
        gender = random.choice(["M", "F"])
        fname = random.choice(first_names_m if gender == "M" else first_names_f)
        lname1 = random.choice(last_names)
        lname2 = random.choice(last_names)
        full_name = f"{fname} {lname1} {lname2}"
        
        # Edad con distribución realista de clientes bancarizados
        age = int(np.clip(np.random.normal(41, 13), 19, 78))
        
        # Nivel socioeconómico / Ingresos
        income_tier = np.random.choice(["Bajo", "Medio", "Medio-Alto", "Alto"], p=[0.25, 0.45, 0.20, 0.10])
        if income_tier == "Bajo":
            income = round(np.random.uniform(12000, 28000), 2)
            credit_score = int(np.clip(np.random.normal(590, 60), 380, 720))
            segment = "Retail"
        elif income_tier == "Medio":
            income = round(np.random.uniform(28001, 65000), 2)
            credit_score = int(np.clip(np.random.normal(670, 50), 450, 780))
            segment = "Retail"
        elif income_tier == "Medio-Alto":
            income = round(np.random.uniform(65001, 120000), 2)
            credit_score = int(np.clip(np.random.normal(730, 45), 580, 820))
            segment = random.choice(["Retail", "SME / Negocios"])
        else:
            income = round(np.random.uniform(120001, 250000), 2)
            credit_score = int(np.clip(np.random.normal(780, 35), 650, 850))
            segment = "Wealth / Banca Privada"
            
        region = np.random.choice(regions, p=region_weights)
        acq_offset = random.randint(0, total_days)
        acq_date = start_dt + timedelta(days=acq_offset)
        
        # Probabilidad de Churn influenciada por Score y Segmento
        base_churn_prob = churn_rate
        if credit_score < 550:
            base_churn_prob += 0.12
        elif credit_score > 750:
            base_churn_prob -= 0.08
            
        if segment == "Wealth / Banca Privada":
            base_churn_prob -= 0.06
        elif income_tier == "Bajo":
            base_churn_prob += 0.05
            
        is_churn = np.random.random() < np.clip(base_churn_prob, 0.05, 0.70)
        
        if is_churn:
            is_active = 0
            # Fecha de Churn posterior a su adquisición
            days_since_acq = (datetime(2026, 10, 31) - acq_date).days
            if days_since_acq > 90:
                churn_offset = random.randint(90, days_since_acq)
                churn_date = acq_date + timedelta(days=churn_offset)
            else:
                churn_date = acq_date + timedelta(days=max(30, days_since_acq))
            churn_reason = np.random.choice(churn_reasons, p=churn_weights)
        else:
            is_active = 1
            churn_date = None
            churn_reason = None
            
        customers.append({
            "customer_id": cust_id,
            "full_name": full_name,
            "gender": gender,
            "age": age,
            "annual_income": income,
            "credit_score": credit_score,
            "customer_segment": segment,
            "region": region,
            "acquisition_date": acq_date.strftime("%Y-%m-%d"),
            "is_active": is_active,
            "churn_date": churn_date.strftime("%Y-%m-%d") if churn_date else None,
            "churn_reason": churn_reason
        })
        
    return pd.DataFrame(customers)

def generate_transactions(df_customers, df_products, n_transactions=45000, start_date="2024-01-01", end_date="2026-10-31"):
    """
    Genera el flujo transaccional financiero vinculando clientes y productos,
    reproduciendo patrones de contracción de actividad previa al churn.
    """
    channels = ["Mobile App", "POS", "Web Banking", "ATM", "Branch / Agencia"]
    channel_weights = [0.45, 0.30, 0.12, 0.08, 0.05]
    
    tx_types = [
        "Purchase / Consumo",
        "Transferencia Saliente",
        "Transferencia Entrante",
        "Pago de Tarjeta",
        "Retiro ATM",
        "Depósito en Efectivo",
        "Comisión / Fee"
    ]
    tx_type_weights = [0.40, 0.20, 0.15, 0.10, 0.08, 0.05, 0.02]
    
    statuses = ["Completed", "Pending", "Failed", "Reversed"]
    status_weights = [0.95, 0.02, 0.02, 0.01]
    
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_window_days = (end_dt - start_dt).days
    
    # Asignación de productos por cliente (cada cliente tiene de 1 a 4 productos)
    product_pool = df_products["product_id"].tolist()
    customer_products = {}
    for cust_id in df_customers["customer_id"]:
        num_prods = random.choices([1, 2, 3, 4], weights=[0.40, 0.35, 0.18, 0.07])[0]
        # Al menos siempre una cuenta o tarjeta
        chosen = random.sample(product_pool, k=min(num_prods, len(product_pool)))
        customer_products[cust_id] = chosen
        
    transactions = []
    cust_dict = df_customers.set_index("customer_id").to_dict(orient="index")
    
    # Generamos transacciones ponderadas por actividad
    # Clientes activos tienen mayor volumen; clientes churned tienen un stop después de churn_date
    tx_id_counter = 1
    
    for cust_id, cdata in cust_dict.items():
        acq_dt = datetime.strptime(cdata["acquisition_date"], "%Y-%m-%d")
        effective_start = max(start_dt, acq_dt)
        
        if cdata["is_active"] == 0 and cdata["churn_date"]:
            effective_end = min(end_dt, datetime.strptime(cdata["churn_date"], "%Y-%m-%d"))
        else:
            effective_end = end_dt
            
        if effective_start >= effective_end:
            continue
            
        available_days = (effective_end - effective_start).days
        if available_days <= 0:
            continue
            
        # Determinar número base de transacciones según segmento
        segment = cdata["customer_segment"]
        if segment == "Wealth / Banca Privada":
            base_count = int(np.random.normal(32, 10))
            avg_amount = 1450.0
        elif segment == "SME / Negocios":
            base_count = int(np.random.normal(40, 12))
            avg_amount = 950.0
        else:
            base_count = int(np.random.normal(18, 7))
            avg_amount = 220.0
            
        # Si el cliente hizo churn, simular decaimiento en los últimos 60 días
        n_tx = max(3, base_count)
        
        for _ in range(n_tx):
            # Fecha de transacción dentro del período de vida activo
            # Para clientes que cancelaron, sesgar las transacciones hacia los primeros meses
            if cdata["is_active"] == 0:
                # Más transacciones al inicio, decayendo cerca de churn_date
                offset_ratio = np.random.beta(1.5, 4.0) # sesgado hacia el inicio
                tx_offset = int(offset_ratio * available_days)
            else:
                # Distribución más uniforme a lo largo del tiempo
                tx_offset = random.randint(0, available_days)
                
            tx_dt = effective_start + timedelta(days=tx_offset)
            
            # Canal y Tipo de Transacción
            channel = np.random.choice(channels, p=channel_weights)
            tx_type = np.random.choice(tx_types, p=tx_type_weights)
            prod_id = random.choice(customer_products[cust_id])
            status = np.random.choice(statuses, p=status_weights)
            
            # Monto con distribución log-normal para emular compras bancarias
            monto_base = np.random.lognormal(mean=np.log(avg_amount), sigma=0.65)
            if tx_type == "Comisión / Fee":
                monto = round(random.choice([5.0, 10.0, 15.0, 25.0, 45.0]), 2)
            elif tx_type in ["Purchase / Consumo", "Pago de Tarjeta"]:
                monto = round(np.clip(monto_base, 10.0, 15000.0), 2)
            elif tx_type in ["Transferencia Saliente", "Transferencia Entrante"]:
                monto = round(np.clip(monto_base * 1.6, 20.0, 35000.0), 2)
            else:
                monto = round(np.clip(monto_base * 0.8, 20.0, 5000.0), 2)
                
            # Cálculo de comisiones generadas para el banco
            if tx_type == "Comisión / Fee":
                fee_amount = monto
            elif channel in ["Branch / Agencia", "ATM"] and monto > 1000:
                fee_amount = round(monto * 0.005, 2)
            elif tx_type == "Purchase / Consumo":
                # Intercambio financiero asumido por comercio
                fee_amount = round(monto * 0.015, 2)
            else:
                fee_amount = 0.0
                
            transactions.append({
                "transaction_id": f"TXN_{tx_id_counter:07d}",
                "customer_id": cust_id,
                "product_id": prod_id,
                "transaction_date": tx_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "channel": channel,
                "transaction_type": tx_type,
                "amount": monto,
                "fee_amount": fee_amount,
                "status": status
            })
            tx_id_counter += 1
            
    df_tx = pd.DataFrame(transactions)
    # Ordenar por fecha cronológica
    df_tx = df_tx.sort_values(by="transaction_date").reset_index(drop=True)
    return df_tx

def main():
    print(">> Iniciando generación de datos sintéticos bancarios...")
    set_seeds(42)
    
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    
    # 1. Catálogo de Productos
    df_products = generate_products()
    products_path = os.path.join(raw_dir, "raw_products.csv")
    df_products.to_csv(products_path, index=False)
    print(f"   [OK] Catálogo de productos creado: {len(df_products)} filas -> {products_path}")
    
    # 2. Padrón de Clientes
    df_customers = generate_customers(n_customers=3000, churn_rate=0.21)
    customers_path = os.path.join(raw_dir, "raw_customers.csv")
    df_customers.to_csv(customers_path, index=False)
    churn_cnt = (df_customers["is_active"] == 0).sum()
    print(f"   [OK] Clientes generados: {len(df_customers)} (Activos: {len(df_customers)-churn_cnt}, Churn: {churn_cnt} - {churn_cnt/len(df_customers)*100:.1f}%) -> {customers_path}")
    
    # 3. Transacciones
    df_transactions = generate_transactions(df_customers, df_products, start_date="2024-01-01", end_date="2026-10-31")
    transactions_path = os.path.join(raw_dir, "raw_transactions.csv")
    df_transactions.to_csv(transactions_path, index=False)
    print(f"   [OK] Transacciones generadas: {len(df_transactions)} registros -> {transactions_path}")
    print(">> Generación de datos crudos completada exitosamente.\n")

if __name__ == "__main__":
    main()
