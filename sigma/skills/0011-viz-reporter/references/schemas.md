# =============================================================================
# schemas.md — Skill 0011: viz-reporter
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# =============================================================================
# Este archivo define el contrato de salida del skill.
# El Orquestador valida cada respuesta contra este schema antes de
# continuar el pipeline o registrar el resultado en Langfuse.
# =============================================================================

# VizReporterOutput — Schema Pydantic

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class VizReporterOutput(BaseModel):
    """
    Objeto de retorno canónico del skill 0011-viz-reporter.
    El Orquestador valida este schema tras cada invocación.
    Cumple ADR-009 (especificación de skills) y ADR-008 (K ⊆ X).
    """

    # ── Identificación ──────────────────────────────────────────────────
    skill_id: Literal["0011"] = Field(
        description="Identificador fijo del skill. Siempre '0011'."
    )
    trace_id: str = Field(
        description="ID de trazabilidad del workflow. Inyectado por el Orquestador."
    )
    run_id: str = Field(
        description=(
            "ID de nivel pipeline, igual al de los demás skills del Hito 1 "
            "(0000-0003, 0008). Agregado en v1.1.0 — antes se usaba "
            "internamente pero no se exponía en el output."
        )
    )

    # ── Estado ───────────────────────────────────────────────────────────
    status: Literal["success", "error", "success_with_warnings"] = Field(
        description=(
            "Estado final de la ejecución. "
            "'success_with_warnings' indica que el artefacto se generó "
            "pero con al menos una degradación (ej. fallback a matplotlib)."
        )
    )

    # ── Motor utilizado ──────────────────────────────────────────────────
    motor: Literal["plotly", "duckdb+plotly", "matplotlib"] = Field(
        description="Motor de visualización efectivamente seleccionado y usado."
    )

    # ── Artefacto generado ───────────────────────────────────────────────
    dashboard_url: Optional[str] = Field(
        default=None,
        description=(
            "URL o ruta de destino del dashboard generado. "
            "Formato: 'minio://dashboards/{trace_id}/index.html' en Full. "
            "None si el skill terminó en error."
        )
    )
    num_graficos: int = Field(
        default=0,
        description="Número de gráficos incluidos en el dashboard generado."
    )

    # ── Flags de modo ────────────────────────────────────────────────────
    pre_aggregated: bool = Field(
        default=False,
        description=(
            "True si se aplicó pre-agregación con DuckDB antes de graficar "
            "(activado cuando el dataset supera 500 000 filas)."
        )
    )
    dev_mode: bool = Field(
        default=False,
        description="True si el skill se ejecutó con SIGMA_VARIANT='Dev' y datos sintéticos."
    )

    # ── Resumen textual ──────────────────────────────────────────────────
    summary_text: Optional[str] = Field(
        default=None,
        description=(
            "Resumen ejecutivo en lenguaje natural generado bajo contrato K ⊆ X. "
            "Máximo 250 palabras + 5-8 palabras clave numeradas. "
            "None si summary_provider es 'none'."
        )
    )
    summary_provider: Literal["ollama", "gemini", "none"] = Field(
        description="Provider LLM efectivamente utilizado para el resumen textual."
    )
    summary_length_chars: Optional[int] = Field(
        default=None,
        description="Longitud en caracteres del summary_text generado. None si no hay resumen."
    )
    keywords_count: Optional[int] = Field(
        default=None,
        description="Número de palabras clave incluidas en el resumen. Entre 5 y 8."
    )

    # ── Warnings ─────────────────────────────────────────────────────────
    warnings: list[str] = Field(
        default_factory=list,
        description=(
            "Lista de advertencias no bloqueantes. Ejemplos: "
            "'plotly_not_available', 'synthetic_data', 'llm_timeout_fallback'."
        )
    )

    # ── Error (solo cuando status='error') ───────────────────────────────
    error_type: Optional[str] = Field(
        default=None,
        description=(
            "Tipo de excepción que causó el error. Valores posibles: "
            "'NoDataForVizError', 'SchemaValidationError', "
            "'MinIOConnectionError', 'AllEnginesUnavailableError'."
        )
    )
    error_detail: Optional[str] = Field(
        default=None,
        description="Mensaje detallado del error, incluyendo columnas esperadas vs encontradas en caso de SchemaValidationError."
    )

    # ── Métricas de ejecución ─────────────────────────────────────────────
    duration_ms: int = Field(
        description="Duración total de la ejecución del skill en milisegundos."
    )
    generated_at: datetime = Field(
        description="Timestamp UTC de generación del artefacto."
    )
```

---

## Excepciones definidas

```python
class NoDataForVizError(Exception):
    """
    Se lanza cuando la tabla de entrada existe pero no contiene filas.
    El skill no genera ningún artefacto y emite viz-reporter.error
    con reason='empty_dataset'.
    """
    pass


class SchemaValidationError(Exception):
    """
    Se lanza cuando la tabla de entrada no contiene las columnas
    mínimas requeridas por el skill.
    El mensaje incluye las columnas esperadas y las encontradas.
    """
    def __init__(self, expected: list[str], found: list[str]):
        self.expected = expected
        self.found = found
        missing = set(expected) - set(found)
        super().__init__(
            f"Schema drift detectado. "
            f"Esperadas: {expected}. "
            f"Encontradas: {found}. "
            f"Faltantes: {list(missing)}."
        )


class AllEnginesUnavailableError(Exception):
    """
    Se lanza cuando ningún motor de visualización está disponible
    en el entorno (ni plotly ni matplotlib).
    Indica un problema de configuración del entorno.
    """
    pass


class MinIOConnectionError(Exception):
    """
    Se lanza cuando el skill no puede persistir el artefacto en MinIO
    tras generarlo correctamente.
    El artefacto queda disponible en ruta temporal local.
    """
    pass
```

---

## Columnas mínimas requeridas en processed_data

| Columna | Tipo | Descripción |
|---|---|---|
| `sentiment` | `str` | Valor de sentimiento: POSITIVO, NEGATIVO, NEUTRAL |
| `engagement_score` | `float` | Score numérico de engagement |
| `lang` | `str` | Código de idioma (ISO 639-1, ej. "es", "en") |

Columnas adicionales presentes en `processed_data` son ignoradas sin error.
