-- =============================================================================
-- init_schema.sql — Schema PostgreSQL SIGMA Hito 1
-- SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
-- Autor: Prof. Marx Agustín García Delgado
-- Versión: 1.0.0
-- =============================================================================
-- Ejecutar ANTES de la primera ejecución del orquestador:
--   psql -U postgres -d sigma -f db/init_schema.sql
--
-- Crea la base de datos si no existe (ejecutar como superusuario):
--   createdb -U postgres sigma
--
-- Tablas creadas en este script (en orden de dependencia):
--   1. pipeline_runs       — registro de cada ejecución del pipeline
--   2. raw_data            — datos crudos ingestados (0001-data-ingestion)
--   3. cleaned_data        — datos limpiados (0002-data-cleanser)
--   4. processed_data      — datos preprocesados (0003-data-preprocessor)
--   5. sentiment_results   — clasificación de sentimiento (0008-sentiment-analyzer)
--   6. pipeline_events     — log de eventos Langfuse locales (auditoría)
-- =============================================================================

-- Extensión para UUIDs (si no está ya activada)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- 1. pipeline_runs — registro de cada ejecución del orquestador
-- =============================================================================
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                  SERIAL PRIMARY KEY,
    pipeline_run_id     TEXT NOT NULL UNIQUE,
    trace_id            TEXT NOT NULL UNIQUE,
    sigma_variant       TEXT NOT NULL
                        CHECK (sigma_variant IN ('Full','Lite','Dev','Runtime')),
    data_path           TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running','success','failed','aborted')),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at         TIMESTAMPTZ,
    dashboard_url       TEXT,
    failed_skill_id     TEXT,
    warnings            JSONB DEFAULT '[]'::jsonb,
    hitl_notified       BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_pr_trace_id
    ON pipeline_runs (trace_id);
CREATE INDEX IF NOT EXISTS idx_pr_status
    ON pipeline_runs (status);

-- =============================================================================
-- 2. raw_data — datos crudos ingestados por 0001-data-ingestion
-- =============================================================================
CREATE TABLE IF NOT EXISTS raw_data (
    id              SERIAL PRIMARY KEY,

    -- Identificador único de la fila (usado como FK en tablas downstream)
    row_id          TEXT NOT NULL,

    -- Contenido del tweet crudo
    text            TEXT,

    -- Metadatos del tweet (columnas del CSV Tirendaz)
    -- Se almacenan como JSONB para flexibilidad entre datasets
    metadata        JSONB DEFAULT '{}'::jsonb,

    -- Trazabilidad
    trace_id        TEXT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rd_trace_id  ON raw_data (trace_id);
CREATE INDEX IF NOT EXISTS idx_rd_row_id    ON raw_data (row_id);

-- =============================================================================
-- 3. cleaned_data — datos limpiados por 0002-data-cleanser
-- =============================================================================
CREATE TABLE IF NOT EXISTS cleaned_data (
    id                      SERIAL PRIMARY KEY,
    row_id                  TEXT NOT NULL,

    -- Texto tras limpieza (sin URLs, menciones, emojis residuales)
    cleaned_text            TEXT,

    -- Flags de limpieza
    was_duplicate           BOOLEAN DEFAULT FALSE,
    had_nulls               BOOLEAN DEFAULT FALSE,
    null_columns            JSONB DEFAULT '[]'::jsonb,

    -- Trazabilidad
    trace_id                TEXT NOT NULL,
    cleaned_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cd_trace_id  ON cleaned_data (trace_id);
CREATE INDEX IF NOT EXISTS idx_cd_row_id    ON cleaned_data (row_id);

-- =============================================================================
-- 3b. cleaned_rejected — filas rechazadas por 0002-data-cleanser (v2.0.0)
-- =============================================================================
-- NOTA — FUSIÓN (Opción C, Eco MultiAgentes 4 Skills 2): tabla nueva,
-- incorporada desde la línea de trabajo "Eco MultiAgentes 3 Skills 1".
-- Almacena filas que no cumplen el schema mínimo (ej. identificador con
-- tipo inválido) y por lo tanto quedan excluidas de cleaned_data, con
-- la razón del rechazo registrada para auditoría posterior.
CREATE TABLE IF NOT EXISTS cleaned_rejected (
    id                  SERIAL PRIMARY KEY,
    row_id              TEXT NOT NULL,
    raw_text            TEXT,
    rejection_reason    TEXT NOT NULL,
    trace_id            TEXT NOT NULL,
    rejected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cr_trace_id  ON cleaned_rejected (trace_id);
CREATE INDEX IF NOT EXISTS idx_cr_row_id    ON cleaned_rejected (row_id);

-- =============================================================================
-- 4. processed_data — datos preprocesados por 0003-data-preprocessor
-- =============================================================================
CREATE TABLE IF NOT EXISTS processed_data (
    id                  SERIAL PRIMARY KEY,
    row_id              TEXT NOT NULL,

    -- Texto limpio listo para clasificación (columna que lee 0008)
    clean_text          TEXT NOT NULL,

    -- Features numéricas escaladas (StandardScaler)
    engagement_score    FLOAT,

    -- Feature categórica — idioma del tweet (ISO 639-1)
    lang                TEXT,

    -- Features adicionales en formato JSONB para extensibilidad
    features            JSONB DEFAULT '{}'::jsonb,

    -- Trazabilidad
    trace_id            TEXT NOT NULL,
    processed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pd_trace_id  ON processed_data (trace_id);
CREATE INDEX IF NOT EXISTS idx_pd_row_id    ON processed_data (row_id);
CREATE INDEX IF NOT EXISTS idx_pd_lang      ON processed_data (lang);

-- =============================================================================
-- 5. sentiment_results — clasificación de sentimiento (0008-sentiment-analyzer)
-- =============================================================================
CREATE TABLE IF NOT EXISTS sentiment_results (
    id              SERIAL PRIMARY KEY,

    -- FK a processed_data
    row_id          TEXT NOT NULL,

    -- Texto clasificado (copia para auditoría — ADR-008)
    clean_text      TEXT NOT NULL,

    -- Clasificación del modelo RoBERTa
    -- UNCLEAR se asigna cuando confidence_score < umbral configurado
    sentiment       TEXT NOT NULL
                    CHECK (sentiment IN ('POSITIVE','NEGATIVE','NEUTRAL','UNCLEAR')),

    -- Score de confianza del modelo (0.0–1.0)
    -- NULL si la fila no pudo clasificarse
    confidence_score    FLOAT
                        CHECK (confidence_score IS NULL
                               OR (confidence_score >= 0.0
                                   AND confidence_score <= 1.0)),

    -- Nombre del modelo utilizado (trazabilidad de versiones de modelo)
    model_name      TEXT NOT NULL,

    -- Trazabilidad del workflow
    trace_id        TEXT NOT NULL,

    -- ──────────────────────────────────────────────────────────────────────
    -- Campo reservado para el Orquestador.
    -- El skill 0008 escribe NULL aquí siempre.
    -- El Orquestador puede enriquecer este campo post-clasificación
    -- con cualquier metadata JSONB necesaria para skills downstream.
    -- ──────────────────────────────────────────────────────────────────────
    extra_metadata  JSONB DEFAULT NULL,

    classified_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sr_trace_id      ON sentiment_results (trace_id);
CREATE INDEX IF NOT EXISTS idx_sr_sentiment     ON sentiment_results (sentiment);
CREATE INDEX IF NOT EXISTS idx_sr_row_id        ON sentiment_results (row_id);

-- =============================================================================
-- 6. pipeline_events — log local de eventos (auditoría complementaria)
-- =============================================================================
-- Complementa Langfuse con un registro local persistente.
-- Útil cuando Langfuse no está disponible o para auditorías forenses.
CREATE TABLE IF NOT EXISTS pipeline_events (
    id              SERIAL PRIMARY KEY,
    trace_id        TEXT NOT NULL,
    skill_id        TEXT,
    event_name      TEXT NOT NULL,
    event_data      JSONB DEFAULT '{}'::jsonb,
    emitted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pe_trace_id      ON pipeline_events (trace_id);
CREATE INDEX IF NOT EXISTS idx_pe_event_name    ON pipeline_events (event_name);
CREATE INDEX IF NOT EXISTS idx_pe_skill_id      ON pipeline_events (skill_id);

-- =============================================================================
-- Verificación final
-- =============================================================================
DO $$
DECLARE
    tbl TEXT;
    expected_tables TEXT[] := ARRAY[
        'pipeline_runs',
        'raw_data',
        'cleaned_data',
        'cleaned_rejected',
        'processed_data',
        'sentiment_results',
        'pipeline_events'
    ];
BEGIN
    FOREACH tbl IN ARRAY expected_tables LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = tbl
        ) THEN
            RAISE EXCEPTION 'Tabla % no fue creada correctamente.', tbl;
        END IF;
    END LOOP;
    RAISE NOTICE 'init_schema.sql ejecutado correctamente. 6 tablas verificadas.';
END $$;
