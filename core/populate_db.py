import pandas as pd
import sys
import os
from sqlalchemy import text
import random
from datetime import datetime, timedelta

# Configurar path para importar base de datos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from propuesta.frontend.database import get_engine, execute_statement

def clean_db():
    print("Limpiando base de datos para datos sintéticos mejorados...")
    execute_statement(text("SET FOREIGN_KEY_CHECKS = 0"))
    tablas = ["Consumo", "Transacciones", "Vivienda", "Periodo", "Lote", "Fraccionamiento", 
              "Usuario", "TipoLote", "TipoPeriodo", "TipoServicio", "Conceptos", "CCostos"]
    for t in tablas:
        execute_statement(text(f"TRUNCATE TABLE {t}"))
    execute_statement(text("SET FOREIGN_KEY_CHECKS = 1"))

def populate():
    engine = get_engine()
    clean_db()
    
    print("Generando maestros y categorías...")
    
    # 1. Catálogos Base
    for t in ['Habitacional', 'Comercial', 'Baldío', 'Área Verde']:
        execute_statement(text("INSERT INTO TipoLote (TipoLote) VALUES (:t)"), {"t": t})
        
    tipos_servicio = [
        'CONSUMO < 30', 
        'CONSUMO >= 30 < 50', 
        'CONSUMO > 50',
        'SUMINISTRO POR PIPA',
        'CUOTA FIJA'
    ]
    for t in tipos_servicio:
        execute_statement(text("INSERT INTO TipoServicio (TipoServicio) VALUES (:t)"), {"t": t})
        
    # TipoPeriodo IDs: 1: SEMANAL, 2: QUINCENAL, 3: MENSUAL, 4: ANUAL
    for t in ['SEMANAL', 'QUINCENAL', 'MENSUAL', 'ANUAL']:
        execute_statement(text("INSERT INTO TipoPeriodo (Tipo) VALUES (:t)"), {"t": t})

    # 2. Centros de Costos y Conceptos
    for cc in ['OPERACIÓN AGUA', 'ADMINISTRACIÓN', 'MANTENIMIENTO', 'BANCOS']:
        execute_statement(text("INSERT INTO CCostos (descripcion) VALUES (:d)"), {"d": cc})
    
    conceptos_iniciales = [
        ('PAGO CUOTA AGUA', 'Ingresos por Suministro'),
        ('RECARGOS POR MORA', 'Ingresos Extraordinarios'),
        ('COMPRA DE PIPAS', 'Gastos de Operación'),
        ('NÓMINA PERSONAL', 'Gastos Administrativos'),
        ('REPARACIÓN DE FUGAS', 'Mantenimiento y Reparaciones'),
        ('PAGO IMSS', 'Impuestos y Cuotas'),
        ('COMISIÓN BANCARIA', 'Gastos Bancarios')
    ]
    for con, clas in conceptos_iniciales:
        execute_statement(text("INSERT INTO Conceptos (concepto, clasificacion) VALUES (:n, :c)"), {"n": con, "c": clas})

    # 3. Fraccionamientos
    df_frac = pd.read_csv('data/processed/fraccionamientos.csv', encoding='latin-1')
    for _, row in df_frac.iterrows():
        execute_statement(text("INSERT INTO Fraccionamiento (ID, Clave, Nombre, No_lotes) VALUES (:id, :c, :n, :l)"),
                         {"id": int(row['Id_fraccionamiento']), "c": str(row['Clave']), "n": str(row['Fraccionamiento']), "l": int(row['NoLotes'])})

    # 4. Usuarios con Teléfono
    print("Generando 100 usuarios con teléfono...")
    nombres = ['Alejandro', 'Beatriz', 'Carlos', 'Diana', 'Eduardo', 'Fernanda', 'Gerardo', 'Hilda']
    apellidos = ['García', 'López', 'Pérez', 'Rodríguez', 'Sánchez', 'Martínez']
    for i in range(1, 101):
        nom = f"{random.choice(nombres)} {random.choice(apellidos)}"
        tel = f"55{random.randint(10000000, 99999999)}"
        execute_statement(text("INSERT INTO Usuario (ID, Nombre, Telefono, Email) VALUES (:id, :n, :t, :e)"), 
                         {"id": i, "n": nom, "t": tel, "e": f"user{i}@hackathon.com"})

    # 5. Lotes y Viviendas (Saldos +/-)
    print("Generando 150 viviendas con saldos mixtos...")
    frac_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Fraccionamiento")).fetchall()]
    for i in range(1, 151):
        execute_statement(text("INSERT INTO Lote (ID, id_fraccionamiento, id_tipo, Clave, manzana) VALUES (:id, :f, :t, :c, :m)"),
                         {"id": i, "f": random.choice(frac_ids), "t": random.randint(1, 3), "c": f"L-{i}", "m": str(random.randint(1, 15))})
        
        # Saldo: Puede ser positivo (deuda) o negativo (a favor)
        saldo = random.uniform(-1500, 4000)
        execute_statement(text("INSERT INTO Vivienda (ID, id_lote, id_user, Clave, saldo) VALUES (:id, :l, :u, :c, :s)"),
                         {"id": i, "l": i, "u": random.randint(1, 100), "c": f"V-{i}", "s": saldo})

    # 6. PERIODOS (Multi-escala: Semanal, Quincenal, Mensual, Anual)
    print("Generando multi-periodos para 2025 y 2026...")
    p_id = 1
    for anio in [2025, 2026]:
        # Semanales (52)
        for sem in range(1, 53):
            f_ini = datetime.strptime(f'{anio}-W{sem}-1', "%Y-W%W-%w")
            f_fin = f_ini + timedelta(days=6)
            execute_statement(text("INSERT INTO Periodo (ID, Anio, id_tipo_periodo, semana, fecha_inicio, fecha_fin) VALUES (:id, :a, 1, :s, :fi, :ff)"), 
                             {"id": p_id, "a": anio, "s": sem, "fi": f_ini, "ff": f_fin})
            p_id += 1
        # Quincenales (24)
        for quin in range(1, 25):
            f_ini = datetime(anio, ((quin-1)//2)+1, 1 if quin%2!=0 else 16)
            f_fin = f_ini + timedelta(days=14)
            execute_statement(text("INSERT INTO Periodo (ID, Anio, id_tipo_periodo, semana, fecha_inicio, fecha_fin) VALUES (:id, :a, 2, :s, :fi, :ff)"), 
                             {"id": p_id, "a": anio, "s": quin, "fi": f_ini, "ff": f_fin})
            p_id += 1
        # Mensuales (12)
        for mes in range(1, 13):
            f_ini = datetime(anio, mes, 1)
            f_fin = (f_ini + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            execute_statement(text("INSERT INTO Periodo (ID, Anio, id_tipo_periodo, semana, fecha_inicio, fecha_fin) VALUES (:id, :a, 3, :s, :fi, :ff)"), 
                             {"id": p_id, "a": anio, "s": mes, "fi": f_ini, "ff": f_fin})
            p_id += 1
        # Anual (1)
        f_ini, f_fin = datetime(anio, 1, 1), datetime(anio, 12, 31)
        execute_statement(text("INSERT INTO Periodo (ID, Anio, id_tipo_periodo, semana, fecha_inicio, fecha_fin) VALUES (:id, :a, 4, 1, :fi, :ff)"), 
                         {"id": p_id, "a": anio, "fi": f_ini, "ff": f_fin})
        p_id += 1

    # 7. Operaciones Sintéticas
    print("Generando 700 consumos y transacciones...")
    viv_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Vivienda")).fetchall()]
    per_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Periodo")).fetchall()]
    
    for _ in range(500):
        ts_id = random.randint(1, 5)
        # Generar cantidad coherente con el tipo de servicio
        if ts_id == 1: # < 30
            cant = random.uniform(5, 29)
            tot = random.uniform(200, 500)
        elif ts_id == 2: # >= 30 < 50
            cant = random.uniform(30, 49)
            tot = random.uniform(501, 800)
        elif ts_id == 3: # > 50
            cant = random.uniform(50, 80)
            tot = random.uniform(801, 1200)
        elif ts_id == 4: # Pipa
            cant = random.choice([5.0, 10.0, 15.0])
            tot = cant * 80
        else: # Cuota Fija (ID 5)
            cant = 1.0
            tot = 450.0
            
        execute_statement(text("INSERT INTO Consumo (IDordenCompra, Cantidad, total, id_tipo_de_servicio, id_vivienda, id_periodo) VALUES (:oc, :can, :tot, :ts, :v, :p)"),
                         {"oc": f"OC-{random.randint(100,999)}", "can": cant, "tot": tot, "ts": ts_id, "v": random.choice(viv_ids), "p": random.choice(per_ids)})

    for _ in range(200):
        execute_statement(text("INSERT INTO Transacciones (fecha, monto, tipo_movimiento, id_ccostos, id_concepto) VALUES (:f, :m, :tm, :cc, :c)"),
                         {"f": datetime.now() - timedelta(days=random.randint(0, 365)), "m": random.uniform(100, 5000), "tm": random.choice(['ingreso', 'egreso']), "cc": random.randint(1, 4), "c": random.randint(1, 4)})

    print(f"✅ Población completada. Total periodos generados: {p_id-1}")

if __name__ == "__main__":
    populate()
