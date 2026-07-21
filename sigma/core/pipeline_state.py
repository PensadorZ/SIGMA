# =============================================================================
# pipeline_state.py — Estado compartido del pipeline SIGMA
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 (base) + Hito 2 (fix SkillId + migración variantes)
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.2.0
# =============================================================================
# Este módulo define PipelineState, el objeto que LangGraph pasa de nodo
# en nodo a lo largo del DAG. Cada skill lee del estado lo que necesita
# y escribe su output antes de ceder el control al siguiente nodo.
#
# Aprobado en sesión de diseño — Decisión A confirmada por Marx García.
#
# NOTA v1.1.0 — FIX (Hito 2, Rollout 1, cierre acordado):
# "0004" no estaba en SkillId ni en retry_counts de initial_state() pese
# a que el skill 0004-statistical-validator ya tiene código real y suite
# verde. Sin este fix, el circuit breaker de director.py no puede
# rastrear reintentos de 0004 — detectado durante la construcción de la
# suite completa de 0004, corregido aquí antes de escribir director.py.
#
# NOTA v1.2.0 — MIGRACIÓN DE VARIANTES (Hito 2, cierre de Rollout 1):
# sigma_variant deja de mezclar costo y submodo en un solo campo
# (Full/Lite/Dev/Runtime). Se separa en dos campos independientes,
# coherente con config.py (que ya usaba este esquema desde antes sin
# que pipeline_state.py lo reflejara — esa inconsistencia queda resuelta
# aquí):
#   sigma_variant: SIGMA-FE | SIGMA-LE | SIGMA-ME | SIGMA-HE  (costo)
#   sigma_submode: Dev | Runtime                              (submodo)
# is_dev_mode() en _common.py se actualiza en el mismo commit para leer
# sigma_submode en vez de comparar sigma_variant == "Dev".
# =============================================================================

from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict


# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------

SkillId = Literal[
    "0000", "0001", "0002", "0003", "0004", "0008", "0011", "HANDLE_ERROR"
]

SkillStatus = Literal["success", "success_with_warnings", "error", "pending"]

ErrorCategory = Literal["non_recoverable", "recoverable", "unknown"]

SigmaVariant = Literal["SIGMA-FE", "SIGMA-LE", "SIGMA-ME", "SIGMA-HE"]
SigmaSubmode = Literal["Dev", "Runtime"]


class SkillResult(TypedDict):
    """
    Resultado individual de un skill dentro del pipeline.
    Se almacena en PipelineState.outputs[skill_id].
    """
    skill_id: str
    status: SkillStatus
    output: dict[str, Any]       # VizReporterOutput, SentimentAnalyzerOutput, etc.
    error_type: Optional[str]
    error_detail: Optional[str]
    error_category: Optional[ErrorCategory]
    duration_ms: int
    retries_attempted: int


# ---------------------------------------------------------------------------
# Estado principal del pipeline
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    """
    Objeto de estado compartido entre todos los nodos del grafo LangGraph.
    LangGraph lo pasa por referencia inmutable entre nodos;
    cada nodo devuelve un dict con los campos que modifica.

    Campos aprobados — Decisión A (Marx García, 2026-06-30).
    """

    # ── Identificación del run ───────────────────────────────────────────
    trace_id: str
    """
    ID único de este run del pipeline. Inyectado por el orquestador
    en el nodo START. Fluye sin modificación a través de todos los skills.
    Formato recomendado: 'sigma-{YYYYMMDD}-{uuid4_short}'.
    """

    pipeline_run_id: str
    """
    ID de nivel pipeline (distinto del trace_id de Langfuse).
    Permite agrupar múltiples runs del mismo pipeline en informes.
    """

    sigma_variant: SigmaVariant
    """
    Variante de COSTO activa en este run — SIGMA-FE ($0, autoalojado),
    SIGMA-LE (bajo costo), SIGMA-ME (~50% pago), SIGMA-HE (alto
    desempeño). Ya NO mezcla submodo — ver sigma_submode.
    """

    sigma_submode: SigmaSubmode
    """
    Submodo transversal, independiente de la variante de costo — Dev
    (datos sintéticos, sin infraestructura real) o Runtime (producción
    real). "SIGMA-FE en modo Dev" es la combinación usada a diario en
    desarrollo; cualquier variante puede combinarse con cualquier
    submodo.
    """

    data_path: str
    """
    Ruta al dataset de entrada (CSV Tirendaz u otro).
    Inyectada desde el argumento --data-path de CLI.
    """

    # ── Control de flujo ─────────────────────────────────────────────────
    current_skill: SkillId
    """
    Skill que está ejecutándose en este momento. Actualizado por cada nodo
    al inicio de su ejecución. Útil para debugging y trazabilidad.
    """

    pipeline_status: Literal["running", "success", "failed", "aborted"]
    """
    Estado global del pipeline. Solo el nodo HANDLE_ERROR puede escribir
    'failed' o 'aborted'. El nodo END escribe 'success'.
    """

    # ── Outputs acumulados ───────────────────────────────────────────────
    outputs: dict[str, SkillResult]
    """
    Dict indexado por skill_id con el resultado de cada skill ejecutado.
    Ejemplo: outputs['0008'] contiene el SentimentAnalyzerOutput completo.
    Los skills downstream pueden leer aquí los outputs de skills anteriores.
    """

    # ── Warnings acumulativas ────────────────────────────────────────────
    warnings: list[str]
    """
    Lista de advertencias no bloqueantes acumuladas durante el pipeline.
    Cada skill con status 'success_with_warnings' añade sus warnings aquí.
    El nodo END las incluye en el resumen final.
    Ejemplo: ['0003:high_unclear_preprocessed', '0008:high_unclear_rate'].
    """

    # ── Circuit breaker ──────────────────────────────────────────────────
    retry_counts: dict[str, int]
    """
    Número de reintentos realizados por skill_id.
    El circuit breaker consulta este campo antes de decidir si reintentar.
    Formato: {'0001': 0, '0002': 1, ...}
    """

    failed_skill_id: Optional[str]
    """
    ID del skill que causó el fallo del pipeline.
    None si el pipeline terminó exitosamente.
    Escrito por el nodo que detecta el error antes de saltar a HANDLE_ERROR.
    """

    # ── Resultado final ──────────────────────────────────────────────────
    dashboard_url: Optional[str]
    """
    URL o ruta del dashboard generado por 0011-viz-reporter.
    None si el pipeline no llegó al skill de reporte.
    Escrito por el nodo 0011 al completar exitosamente.
    """

    hitl_notified: bool
    """
    True si se envió al menos una notificación HITL a Zulip durante el run.
    Útil para auditoría y para el evaluador de adherencia.
    """

    # ── HITL con interrupt + checkpointer (agregado en esta sesión) ────────
    hitl_decision: Optional[bool]
    """
    Decisión humana recibida vía interrupt(). None mientras no se haya
    resuelto ninguna pausa HITL en este run. No vive dentro de 'outputs'
    porque no tiene la forma de SkillResult — es una decisión humana,
    no el resultado de un skill.
    """

    hitl_question: Optional[str]
    """
    Pregunta exacta que se envió a Zulip cuando el grafo se pausó.
    Se conserva para trazabilidad — qué se preguntó, no solo qué se respondió.
    """


# ---------------------------------------------------------------------------
# Estado inicial — factory function
# ---------------------------------------------------------------------------

def initial_state(
    trace_id: str,
    pipeline_run_id: str,
    sigma_variant: SigmaVariant,
    sigma_submode: SigmaSubmode,
    data_path: str,
) -> PipelineState:
    """
    Construye el PipelineState inicial para un nuevo run del pipeline.
    Llamado por el orquestador en el punto de entrada antes de compilar
    el grafo LangGraph.

    Args:
        trace_id:        ID de trazabilidad Langfuse.
        pipeline_run_id: ID del run del pipeline.
        sigma_variant:   Variante de costo ('SIGMA-FE', 'SIGMA-LE', etc.).
        sigma_submode:   Submodo transversal ('Dev' o 'Runtime').
        data_path:       Ruta al dataset de entrada.

    Returns:
        PipelineState con todos los campos en su valor inicial.
    """
    return PipelineState(
        trace_id=trace_id,
        pipeline_run_id=pipeline_run_id,
        sigma_variant=sigma_variant,
        sigma_submode=sigma_submode,
        data_path=data_path,
        current_skill="0000",
        pipeline_status="running",
        outputs={},
        warnings=[],
        retry_counts={
            "0000": 0,
            "0001": 0,
            "0002": 0,
            "0003": 0,
            "0004": 0,  # nuevo — Hito 2, Rollout 1 (fix v1.1.0)
            "0008": 0,
            "0011": 0,
        },
        failed_skill_id=None,
        dashboard_url=None,
        hitl_notified=False,
        hitl_decision=None,
        hitl_question=None,
    )


# ---------------------------------------------------------------------------
# Clasificación de errores para el circuit breaker
# ---------------------------------------------------------------------------

# Errores que no tienen sentido reintentar. El modelo no va a aparecer solo,
# el schema no va a cambiar, los datos no van a aparecer de la nada.
NON_RECOVERABLE_ERRORS: frozenset[str] = frozenset({
    "ModelNotFoundError",
    "SchemaValidationError",
    "NoDataToAnalyzeError",
    "NoDataForVizError",
    "AllEnginesUnavailableError",
    "InputSchemaError",              # nuevo — 0004 (Hito 2)
    "InsufficientSampleSizeError",   # nuevo — 0004 (Hito 2)
    "PolicyConfigurationError",      # nuevo — 0004 (Hito 2)
})

# Errores de infraestructura que pueden resolverse en segundos.
# Se reintenta máximo 2 veces con backoff exponencial de 5s.
RECOVERABLE_ERRORS: frozenset[str] = frozenset({
    "PostgreSQLConnectionError",
    "MinIOConnectionError",
    "OllamaConnectionError",
    "ZulipConnectionError",
})

# Máximo de reintentos para errores recuperables.
MAX_RETRIES: int = 2

# Tiempo de espera base en segundos para backoff exponencial.
# Intento 1: 5s, Intento 2: 10s.
BACKOFF_BASE_SECONDS: float = 5.0


def classify_error(error_type: str) -> ErrorCategory:
    """
    Clasifica un error en recuperable, no recuperable o desconocido.
    El circuit breaker usa esta clasificación para decidir si reintentar.

    Errores desconocidos se tratan como no recuperables por defecto
    (fallo rápido), pero se notifica a Gemini para análisis si está
    disponible en el entorno.
    """
    if error_type in NON_RECOVERABLE_ERRORS:
        return "non_recoverable"
    if error_type in RECOVERABLE_ERRORS:
        return "recoverable"
    return "unknown"
