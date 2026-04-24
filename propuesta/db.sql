-- Eliminar tablas en orden inverso a su jerarquía para evitar errores de FK
DROP TABLE IF EXISTS Consumo;
DROP TABLE IF EXISTS Transacciones;
DROP TABLE IF EXISTS Vivienda;
DROP TABLE IF EXISTS Periodo;
DROP TABLE IF EXISTS Lote;
DROP TABLE IF EXISTS Conceptos;
DROP TABLE IF EXISTS CCostos;
DROP TABLE IF EXISTS Fraccionamiento;
DROP TABLE IF EXISTS Usuario;
DROP TABLE IF EXISTS TipoPeriodo;
DROP TABLE IF EXISTS TipoServicio;
DROP TABLE IF EXISTS TipoLote;

-- 1. Tablas Independientes (Nivel 1)
CREATE TABLE TipoLote (
    ID SERIAL PRIMARY KEY,
    TipoLote VARCHAR(100) NOT NULL
);

CREATE TABLE TipoServicio (
    ID SERIAL PRIMARY KEY,
    TipoServicio VARCHAR(100) NOT NULL
);

CREATE TABLE TipoPeriodo (
    ID SERIAL PRIMARY KEY,
    Tipo VARCHAR(50) NOT NULL -- SEMANAL, QUINCENAL, MENSUAL, ANUAL
);

CREATE TABLE Usuario (
    ID SERIAL PRIMARY KEY,
    Nombre VARCHAR(255) NOT NULL,
    Telefono VARCHAR(20),
    Email VARCHAR(100)
);

CREATE TABLE Fraccionamiento (
    ID SERIAL PRIMARY KEY,
    Clave VARCHAR(50) UNIQUE,
    Nombre VARCHAR(150),
    No_lotes INTEGER
);

CREATE TABLE CCostos (
    ID SERIAL PRIMARY KEY,
    descripcion VARCHAR(255)
);

CREATE TABLE Conceptos (
    ID SERIAL PRIMARY KEY,
    concepto VARCHAR(255),
    clasificacion VARCHAR(100) -- BANCOS, CANCELADO, INTERCOMPAÑIAS
);

-- 2. Tablas con Dependencias (Nivel 2)
CREATE TABLE Lote (
    ID SERIAL PRIMARY KEY,
    id_fraccionamiento INTEGER REFERENCES Fraccionamiento(ID),
    id_tipo INTEGER REFERENCES TipoLote(ID),
    Clave VARCHAR(50),
    manzana VARCHAR(50),
    subclave VARCHAR(50),
    seccion VARCHAR(50)
);

CREATE TABLE Periodo (
    ID SERIAL PRIMARY KEY,
    Anio INTEGER NOT NULL,
    id_tipo_periodo INTEGER REFERENCES TipoPeriodo(ID),
    semana INTEGER,
    fecha_inicio DATE,
    fecha_fin DATE
); -- <-- Corrección: Paréntesis y punto y coma añadidos

-- 3. Tablas con Dependencias (Nivel 3)
CREATE TABLE Vivienda (
    ID SERIAL PRIMARY KEY,
    id_lote INTEGER REFERENCES Lote(ID),
    id_user INTEGER REFERENCES Usuario(ID),
    Clave VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    saldo DECIMAL(12, 2) DEFAULT 0.00
);

-- 4. Tablas Operativas (Nivel 4)
CREATE TABLE Consumo (
    ID SERIAL PRIMARY KEY,
    IDordenCompra VARCHAR(50), 
    Cantidad DECIMAL(10, 2),
    total DECIMAL(12, 2),
    subCuenta VARCHAR(100),
    fechaPago DATE,
    id_tipo_de_servicio INTEGER REFERENCES TipoServicio(ID),
    id_vivienda INTEGER REFERENCES Vivienda(ID),
    id_periodo INTEGER REFERENCES Periodo(ID)
);

CREATE TABLE Transacciones (
    ID SERIAL PRIMARY KEY,
    fecha TIMESTAMP,
    monto DECIMAL(12, 2),
    tipo_movimiento VARCHAR(20), -- ingreso / egreso
    id_ccostos INTEGER REFERENCES CCostos(ID),
    id_cuenta INTEGER, -- Referencia opcional (campo escalar por ahora)
    id_concepto INTEGER REFERENCES Conceptos(ID)
);