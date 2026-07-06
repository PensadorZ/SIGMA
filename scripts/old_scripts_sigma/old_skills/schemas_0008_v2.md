# =============================================================================
# schemas.md — Skill 0008: sentiment-analyzer
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# =============================================================================
# Define el contrato de salida del skill y el schema de la tabla
# sentiment_results en PostgreSQL.
# El Orquestador valida SentimentAnalyzerOutput tras cada invocación.
# =============================================================================

## SentimentAnalyzerOutput — Schema Pydantic

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class SentimentAnalyzerOutput(BaseModel):
    """
    Objeto de retorno canónico del skill 0008-sentiment-analyzer.
    El Orquestador valida este schema tras cada invocación.
    Cumple ADR-009 (especificación de skills) y ADR-008 (K ⊆ X).
    """

    # ── Identificación ──────────────────────────────────────────────────
    skill_id: Literal["0008"] = Field(
        description="Identificador fijo del skill. Siempre '0008'."
    )
    trace_id: str = Field(
        description="ID de trazabilidad del workflow. Inyectado por el Orquestador."
    )

    # ── Estado ───────────────────────────────────────────────────────────
    status: Literal["success", "error", "success_with_warnings"] = Field(
        description="Estado final de la ejecución del skill."
    )

    # ── Modelo utilizado ─────────────────────────────────────────────────
    model_name: str = Field(
        description="Nombre completo del modelo usado para la clasificación."
    )

    # ── Métricas de clasificación ─────────────────────────────────────────
    num_classified: int = Field(
        default=0,
        description="Total de filas clasificadas y escritas en sentiment_results."
    )
    num_unclear: int = Field(
        default=0,
        description="Filas marcadas como UNCLEAR por confidence_score < umbral."
    )
    pct_unclear: float = Field(
        default=0.0,
        description="Porcentaje de filas UNCLEAR sobre el total clasificado."
    )
    avg_confidence: Optional[float] = Field(
        default=None,
        description="Confidence score promedio sobre todas las filas clasificadas."
    )
    min_confidence: Optional[float] = Field(
        default=None,
        description="Confidence score mínimo observado en el batch completo."
    )
    max_confidence: Optional[float] = Field(
        default=None,
        description="Confidence score máximo observado en el batch completo."
    )

    # ── Métricas de ejecución ─────────────────────────────────────────────
    batches_processed: int = Field(
        default=0,
        description="Número total de batches procesados durante la ejecución."
    )
    duration_ms: int = Field(
        description="Duración total de la ejecución del skill en milisegundos."
    )
    generated_at: datetime = Field(
        description="Timestamp UTC de finalización de la clasificación."
    )

    # ── Flags de modo ────────────────────────────────────────────────────
    dev_mode: bool = Field(
        default=False,
        description="True si el skill se ejecutó con SIGMA_VARIANT='Dev'."
    )

    # ── Warnings ─────────────────────────────────────────────────────────
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Lista de advertencias no bloqueantes. Ejemplos: "
            "'synthetic_data', 'high_unclear_rate' (>30% UNCLEAR)."
        )
    )

    # ── Error (solo cuando status='error') ───────────────────────────────
    error_type: Optional[str] = Field(
        default=None,
        description=(
            "Tipo de excepción que causó el error. Valores posibles: "
            "'ModelNotFoundError', 'NoDataToAnalyzeError', "
            "'SchemaValidationError', 'PostgreSQLConnectionError'."
        )
    )
    error_detail: Optional[str] = Field(
        default=None,
        description="Mensaje detallado del error."
    )
    batches_completed_before_error: Optional[int] = Field(
        default=None,
        description="Número de batches completados antes de producirse el error."
    )
```

---

## Schema de la tabla sentiment_results (PostgreSQL)

```sql
CREATE TABLE sentiment_results (
    id              SERIAL PRIMARY KEY,

    -- FK a processed_data
    row_id          TEXT NOT NULL,

    -- Texto clasificado (copia para auditoría y trazabilidad)
    clean_text      TEXT NOT NULL,

    -- Clasificación del modelo
    -- Valores: POSITIVE | NEGATIVE | NEUTRAL | UNCLEAR
    sentiment       TEXT NOT NULL
                    CHECK (sentiment IN ('POSITIVE','NEGATIVE','NEUTRAL','UNCLEAR')),

    -- Score de confianza del modelo (0.0–1.0)
    -- NULL si la fila no pudo ser clasificada
    confidence_score FLOAT,

    -- Nombre del modelo utilizado (trazabilidad de versiones)
    model_name      TEXT NOT NULL,

    -- ID del workflow (ADR-006, placeholder resuelto por ContextResolver)
    trace_id        TEXT NOT NULL,

    -- ──────────────────────────────────────────────────────────────────
    -- Campo reservado para solicitudes del Orquestador.
    -- El skill escribe NULL aquí siempre. El Orquestador puede
    -- enriquecer este campo post-clasificación con cualquier metadata
    -- adicional necesaria para skills downstream (ej. 0011-viz-reporter).
    -- Tipo JSONB permite estructura arbitraria sin cambiar el schema.
    -- ──────────────────────────────────────────────────────────────────
    extra_metadata  JSONB DEFAULT NULL,

    -- Timestamp de inserción
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para consultas frecuentes de viz-reporter y el orquestador
CREATE INDEX idx_sr_trace_id   ON sentiment_results (trace_id);
CREATE INDEX idx_sr_sentiment  ON sentiment_results (sentiment);
CREATE INDEX idx_sr_row_id     ON sentiment_results (row_id);
```

---

## Excepciones definidas

```python
class ModelNotFoundError(Exception):
    """
    Se lanza cuando ROBERTA_MODEL_PATH apunta a una ruta inexistente.
    Indica un problema de configuración del entorno, no de los datos.
    """
    def __init__(self, path: str):
        super().__init__(
            f"Modelo RoBERTa no encontrado en la ruta configurada: '{path}'. "
            f"Verifica ROBERTA_MODEL_PATH en tu archivo .env."
        )


class NoDataToAnalyzeError(Exception):
    """
    Se lanza cuando processed_data existe pero no contiene filas.
    El skill no escribe ningún registro en sentiment_results.
    """
    pass


class SchemaValidationError(Exception):
    """
    Se lanza cuando processed_data no contiene la columna clean_text
    u otras columnas mínimas requeridas.
    """
    def __init__(self, expected: list[str], found: list[str]):
        self.expected = expected
        self.found = found
        missing = set(expected) - set(found)
        super().__init__(
            f"Schema drift detectado en processed_data. "
            f"Columnas esperadas: {expected}. "
            f"Encontradas: {found}. "
            f"Faltantes: {list(missing)}."
        )


class PostgreSQLConnectionError(Exception):
    """
    Se lanza cuando el skill no puede conectarse a PostgreSQL
    en modo Full. En modo Dev este error no aplica.
    """
    pass
```

---

## Columnas mínimas requeridas en processed_data

| Columna | Tipo | Descripción |
|---|---|---|
| `row_id` | `str` | Identificador único de cada fila |
| `clean_text` | `str` | Texto limpio y preprocesado listo para clasificar |

Cualquier columna adicional en `processed_data` es ignorada por este skill.
La columna `extra_metadata` en `sentiment_results` queda en `NULL` tras la
ejecución del skill. El Orquestador puede enriquecerla con cualquier JSONB
arbitrario necesario para skills downstream sin modificar el schema.
