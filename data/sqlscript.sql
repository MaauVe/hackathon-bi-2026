/* ASEGÚRATE DE ESTAR EN LA BASE DE DATOS CORRECTA */
USE db_hackaton;

-- 1. LIMPIEZA TOTAL (En orden inverso de dependencias)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS FactIngresoEgreso, FactConsumoAgua, DimVivienda, DimLote, 
                    DimTipoMovimiento, DimClasificacion, DimPeriodo, 
                    DimTipoCobro, DimFraccionamiento;
SET FOREIGN_KEY_CHECKS = 1;

-- 2. DIMENSIONES MAESTRAS (Sin dependencias)
CREATE TABLE DimFraccionamiento (
    id_fraccionamiento INT NOT NULL AUTO_INCREMENT,
    clave VARCHAR(10) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    no_lotes INT DEFAULT 0,
    PRIMARY KEY (id_fraccionamiento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE DimTipoCobro (
    id INT NOT NULL AUTO_INCREMENT,
    descripcion VARCHAR(50) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE DimPeriodo (
    id_periodo INT NOT NULL AUTO_INCREMENT,
    anio INT NOT NULL,
    messem VARCHAR(5),
    sem INT,
    finicio DATETIME,
    ffin DATETIME,
    PRIMARY KEY (id_periodo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE DimClasificacion (
    id INT NOT NULL AUTO_INCREMENT,
    descripcion VARCHAR(55) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE DimTipoMovimiento (
    id INT NOT NULL AUTO_INCREMENT,
    descripcion VARCHAR(55) NOT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. DIMENSIONES CON FK
CREATE TABLE DimLote (
    id_lote INT NOT NULL AUTO_INCREMENT,
    fraccionamiento_id INT NOT NULL,
    clave_lote VARCHAR(30) NOT NULL,
    tipo VARCHAR(10),
    manzana VARCHAR(10),
    PRIMARY KEY (id_lote),
    CONSTRAINT fk_lote_fracc FOREIGN KEY (fraccionamiento_id) 
        REFERENCES DimFraccionamiento (id_fraccionamiento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE DimVivienda (
    id_vivienda INT NOT NULL AUTO_INCREMENT,
    clave VARCHAR(20) NOT NULL UNIQUE,
    manzana VARCHAR(10),
    lote VARCHAR(20),
    fraccionamiento_id INT NOT NULL,
    user_id INT,
    saldo DECIMAL(12,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    uso_id INT,
    PRIMARY KEY (id_vivienda),
    CONSTRAINT fk_vivienda_fracc FOREIGN KEY (fraccionamiento_id) 
        REFERENCES DimFraccionamiento (id_fraccionamiento)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. TABLAS DE HECHOS
CREATE TABLE FactConsumoAgua (
    id_detalle_orden_compra INT NOT NULL AUTO_INCREMENT,
    id_orden_compra INT,
    cantidad DECIMAL(12,2),
    id_tipo_de_cobro INT,
    descuento DECIMAL(12,2) DEFAULT 0.00,
    iva DECIMAL(12,2) DEFAULT 0.00,
    importe DECIMAL(12,2),
    total DECIMAL(12,2),
    unidad VARCHAR(50),
    date_pago DATETIME,
    observaciones VARCHAR(250),
    lote_id INT,
    periodo_id INT,
    PRIMARY KEY (id_detalle_orden_compra),
    CONSTRAINT fk_fact_tipo_cobro FOREIGN KEY (id_tipo_de_cobro) REFERENCES DimTipoCobro (id),
    CONSTRAINT fk_fact_lote FOREIGN KEY (lote_id) REFERENCES DimLote (id_lote),
    CONSTRAINT fk_fact_periodo FOREIGN KEY (periodo_id) REFERENCES DimPeriodo (id_periodo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE FactIngresoEgreso (
    id_detalle_cheque INT NOT NULL AUTO_INCREMENT,
    ccostos INT,
    fecha DATE NOT NULL,
    fact VARCHAR(50),
    nombre VARCHAR(100),
    concepto VARCHAR(255),
    referencia VARCHAR(100),
    clasificacion_id INT,
    entra DECIMAL(12,2) DEFAULT 0.00,
    sale DECIMAL(12,2) DEFAULT 0.00,
    tipo_movimiento_id INT,
    op VARCHAR(50),
    trans INT,
    saldo_anterior VARCHAR(100),
    PRIMARY KEY (id_detalle_cheque),
    CONSTRAINT fk_fact_clasif FOREIGN KEY (clasificacion_id) REFERENCES DimClasificacion (id),
    CONSTRAINT fk_fact_tipo_mov FOREIGN KEY (tipo_movimiento_id) REFERENCES DimTipoMovimiento (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;