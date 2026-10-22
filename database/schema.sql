-- ============================================================
-- ANVIORA - Script DDL de Base de Datos
-- Sistema Inteligente para el Monitoreo, Análisis y Seguimiento
-- del Bienestar Emocional
-- Autor: Adrian Ferley Figueroa Flórez
-- Institución: Unidades Tecnológicas de Santander (UTS)
-- Motor: PostgreSQL 14+
-- ============================================================

BEGIN;

-- ============================================================
-- TABLA: usuarios
-- Cuentas de usuario y autenticación (RF-01, RNF-02)
-- ============================================================
CREATE TABLE usuarios (
    id_usuario           SERIAL PRIMARY KEY,
    nombre               VARCHAR(100) NOT NULL,
    correo               VARCHAR(150) NOT NULL,
    contrasena_hash      VARCHAR(255) NOT NULL,        -- Hash bcrypt (salt >= 10), nunca texto plano
    fecha_registro       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo               BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT uq_usuarios_correo UNIQUE (correo),
    CONSTRAINT chk_usuarios_correo_formato
        CHECK (correo ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

COMMENT ON TABLE usuarios IS
    'Cuentas registradas. Contraseñas cifradas con bcrypt; sesiones vía JWT (RF-01, RNF-02).';

-- ============================================================
-- TABLA: registros_emocionales
-- Registro diario de estado emocional y rutina (RF-02)
-- ============================================================
CREATE TABLE registros_emocionales (
    id_registro            SERIAL PRIMARY KEY,
    id_usuario             INTEGER NOT NULL,
    fecha_registro         DATE NOT NULL DEFAULT CURRENT_DATE,
    estado_animo           SMALLINT NOT NULL,           -- Escala 1 a 5
    horas_sueno            NUMERIC(4,2) NOT NULL,        -- Ej: 7.50
    nivel_estres           SMALLINT NOT NULL,            -- Escala 1 a 5
    etiquetas_actividades  TEXT[] DEFAULT '{}',          -- Ej: {'ejercicio','trabajo','estudio'}
    descripcion_texto      TEXT,                         -- Texto libre sobre el día
    fecha_creacion         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_registros_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT uq_registro_usuario_fecha
        UNIQUE (id_usuario, fecha_registro),             -- Un registro por usuario por día
    CONSTRAINT chk_estado_animo   CHECK (estado_animo BETWEEN 1 AND 5),
    CONSTRAINT chk_nivel_estres   CHECK (nivel_estres BETWEEN 1 AND 5),
    CONSTRAINT chk_horas_sueno    CHECK (horas_sueno BETWEEN 0 AND 24)
);

COMMENT ON TABLE registros_emocionales IS
    'Registro diario de ánimo, horas de sueño, nivel de estrés, etiquetas de actividades y texto libre (RF-02).';

-- ============================================================
-- TABLA: analisis_ia
-- Resultado del análisis de sentimiento y palabras clave (RF-03)
-- ============================================================
CREATE TABLE analisis_ia (
    id_analisis            SERIAL PRIMARY KEY,
    id_registro            INTEGER NOT NULL,
    polaridad_sentimiento  VARCHAR(10),                  -- Positivo | Neutro | Negativo; NULL mientras está pendiente
    puntuacion_confianza   NUMERIC(5,4),                 -- 0.0000 a 1.0000
    palabras_clave         TEXT[] DEFAULT '{}',          -- Palabras correlacionadas con estrés
    estado_procesamiento   VARCHAR(20) NOT NULL DEFAULT 'pendiente',
    fecha_procesamiento    TIMESTAMP,
    fecha_creacion         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_analisis_registro
        FOREIGN KEY (id_registro) REFERENCES registros_emocionales(id_registro) ON DELETE CASCADE,
    CONSTRAINT uq_analisis_registro UNIQUE (id_registro),   -- Un análisis por registro
    CONSTRAINT chk_polaridad
        CHECK (polaridad_sentimiento IN ('Positivo','Neutro','Negativo')),
    CONSTRAINT chk_estado_procesamiento
        CHECK (estado_procesamiento IN ('pendiente','procesando','completado','error')),
    CONSTRAINT chk_confianza
        CHECK (puntuacion_confianza IS NULL OR puntuacion_confianza BETWEEN 0 AND 1)
);

COMMENT ON TABLE analisis_ia IS
    'Resultado de la llamada asíncrona de IA (polaridad y palabras clave) tras anonimizar el PII del texto libre (RF-03, RNF-01).';

-- ============================================================
-- TABLA: recomendaciones
-- Recomendaciones de bienestar por reglas + enriquecimiento de IA (RF-04)
-- ============================================================
CREATE TABLE recomendaciones (
    id_recomendacion        SERIAL PRIMARY KEY,
    id_usuario               INTEGER NOT NULL,
    id_registro               INTEGER,                    -- NULL si nace de un patrón multi-día
    tipo_recomendacion       VARCHAR(50) NOT NULL,        -- Ej: 'sueño', 'estrés', 'autocuidado'
    contenido_recomendacion  TEXT NOT NULL,
    nivel_prioridad           VARCHAR(10) NOT NULL DEFAULT 'media',
    vista                     BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_generacion          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_recomendaciones_usuario
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_recomendaciones_registro
        FOREIGN KEY (id_registro) REFERENCES registros_emocionales(id_registro) ON DELETE SET NULL,
    CONSTRAINT chk_prioridad CHECK (nivel_prioridad IN ('baja','media','alta'))
);

COMMENT ON TABLE recomendaciones IS
    'Recomendaciones no clínicas de autocuidado, generadas por un motor de reglas combinado con IA (RF-04).';

-- ============================================================
-- ÍNDICES para las consultas más frecuentes (RNF-01: < 2s)
-- ============================================================
CREATE INDEX idx_registros_usuario_fecha
    ON registros_emocionales (id_usuario, fecha_registro DESC);

CREATE INDEX idx_analisis_estado
    ON analisis_ia (estado_procesamiento);

CREATE INDEX idx_recomendaciones_usuario_fecha
    ON recomendaciones (id_usuario, fecha_generacion DESC);

-- Índice GIN para búsquedas dentro de las etiquetas de actividades
CREATE INDEX idx_registros_etiquetas_gin
    ON registros_emocionales USING GIN (etiquetas_actividades);

-- ============================================================
-- TRIGGER: mantener fecha_actualizacion al día en usuarios
-- ============================================================
CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_usuarios_actualizar
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_fecha_actualizacion();

COMMIT;
