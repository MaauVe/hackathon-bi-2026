import pandas as pd
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from propuesta.frontend.database import get_engine, execute_statement
from sqlalchemy import text
import random
from datetime import datetime, timedelta

def populate():
    engine = get_engine()
    
    # 1. Catalogos Simples
    tipos_lote = ['Habitacional', 'Comercial', 'Baldío']
    tipos_servicio = ['Agua Potable (Red)', 'Pipa de Agua']
    tipos_periodo = ['SEMANAL', 'QUINCENAL', 'MENSUAL', 'ANUAL']
    
    with engine.begin() as conn:
        for t in tipos_lote:
            conn.execute(text("INSERT INTO TipoLote (TipoLote) VALUES (:t)"), {"t": t})
        for t in tipos_servicio:
            conn.execute(text("INSERT INTO TipoServicio (TipoServicio) VALUES (:t)"), {"t": t})
        for t in tipos_periodo:
            conn.execute(text("INSERT INTO TipoPeriodo (Tipo) VALUES (:t)"), {"t": t})

    # 2. Fraccionamientos (Desde CSV)
    df_frac = pd.read_csv('data/processed/fraccionamientos.csv', encoding='latin-1')
    # Mapear columnas: Id_fraccionamiento -> ID, Fraccionamiento -> Nombre, NoLotes -> No_lotes
    df_frac = df_frac.rename(columns={
        'Id_fraccionamiento': 'ID',
        'Fraccionamiento': 'Nombre',
        'NoLotes': 'No_lotes'
    })
    df_frac.to_sql('Fraccionamiento', con=engine, if_exists='append', index=False)

    # 3. Lotes
    df_lotes = pd.read_csv('data/processed/lotes.csv', encoding='latin-1')
    # id_lote, Fraccionamiento, ClaveLote, manzana
    for _, row in df_lotes.iterrows():
        execute_statement(text("""
            INSERT INTO Lote (id_fraccionamiento, id_tipo, Clave, manzana) 
            VALUES (:f, :t, :c, :m)
        """), {
            "f": row['Fraccionamiento'], 
            "t": random.randint(1, 3), 
            "c": row['ClaveLote'], 
            "m": row['manzana']
        })

    # 4. Usuarios (Sintéticos)
    nombres = ['Juan Pérez', 'María García', 'Luis Rodriguez', 'Ana Martinez', 'Carlos Lopez']
    for n in nombres:
        execute_statement(text("INSERT INTO Usuario (Nombre, Telefono, Email) VALUES (:n, :t, :e)"), 
                         {"n": n, "t": "555-0102", "e": f"{n.lower().replace(' ', '.')}@example.com"})

    # 5. Viviendas
    lotes_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Lote")).fetchall()]
    usuarios_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Usuario")).fetchall()]
    for lid in lotes_ids:
        execute_statement(text("INSERT INTO Vivienda (id_lote, id_user, Clave, saldo) VALUES (:l, :u, :c, :s)"), 
                         {"l": lid, "u": random.choice(usuarios_ids), "c": f"V-{lid}", "s": random.uniform(0, 5000)})

    # 6. Periodos
    df_periodos = pd.read_csv('data/processed/periodos.csv', encoding='latin-1')
    for _, row in df_periodos.iterrows():
        execute_statement(text("""
            INSERT INTO Periodo (Anio, id_tipo_periodo, semana, fecha_inicio, fecha_fin) 
            VALUES (:a, :tp, :s, :fi, :ff)
        """), {
            "a": row['año'], 
            "tp": 3, # Mensual por defecto
            "s": row['sem'], 
            "fi": datetime.strptime(row['finicio'], '%d/%m/%Y'), 
            "ff": datetime.strptime(row['ffin'], '%d/%m/%Y')
        })

    # 7. Consumo (BI target)
    viviendas_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Vivienda")).fetchall()]
    periodos_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Periodo")).fetchall()]
    for _ in range(200):
        execute_statement(text("""
            INSERT INTO Consumo (IDordenCompra, Cantidad, total, id_tipo_de_servicio, id_vivienda, id_periodo) 
            VALUES (:oc, :can, :tot, :ts, :v, :p)
        """), {
            "oc": f"OC-{random.randint(1000,9999)}",
            "can": random.uniform(10, 50),
            "tot": random.uniform(200, 1500),
            "ts": random.randint(1, 2),
            "v": random.choice(viviendas_ids),
            "p": random.choice(periodos_ids)
        })

    # 8. Conceptos y CCostos
    conceptos = ['PAGO AGUA', 'REPARACION TUBO', 'CUOTA MANTENIMIENTO', 'PAGO PIPAS']
    for c in conceptos:
        execute_statement(text("INSERT INTO Conceptos (concepto, clasificacion) VALUES (:c, 'BANCOS')"), {"c": c})
    
    ccostos = ['OPERACION', 'MANTENIMIENTO', 'ADMINISTRACION']
    for cc in ccostos:
        execute_statement(text("INSERT INTO CCostos (descripcion) VALUES (:cc)"), {"cc": cc})

    # 9. Transacciones
    concepto_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM Conceptos")).fetchall()]
    ccosto_ids = [r[0] for r in engine.connect().execute(text("SELECT ID FROM CCostos")).fetchall()]
    for i in range(100):
        tipo = 'ingreso' if random.random() > 0.4 else 'egreso'
        execute_statement(text("""
            INSERT INTO Transacciones (fecha, monto, tipo_movimiento, id_ccostos, id_concepto) 
            VALUES (:f, :m, :tm, :cc, :c)
        """), {
            "f": datetime.now() - timedelta(days=random.randint(0, 365)),
            "m": random.uniform(100, 10000),
            "tm": tipo,
            "cc": random.choice(ccosto_ids),
            "c": random.choice(concepto_ids)
        })

if __name__ == "__main__":
    populate()
    print("Base de datos poblada con éxito.")
