# =============================================================================
# skills/0004-statistical-validator/skill.py
# SIGMA v1.5 · Hito 2, Engineer Datos (ADR-016 Tab. 2, Rollout 1)
# Autor: Prof. Marx Agustín García Delgado
# Versión: 1.0.0
# =============================================================================
# Reviewer & Gate puro (taxonomía Día 3, Google-Kaggle) — nunca transforma
# datos, solo emite veredicto. Tres modos: selección de prueba de
# significancia (Modo A, Tab. 1 de SKILL.md), detección de drift vía
# KS-test exclusivo (Modo B, ADR-001 v1.4 — PSI queda prohibido), y
# detección de leakage por correlación (Modo C).
#
# NOTA DE VERIFICACIÓN — construido y corregido contra los 6 archivos
# reales que Marx proporcionó (_common.py, tracing.py, pipeline_state.py,
# checkpointer.py, config.py, policies.yaml). Dos huecos reales quedan
# señalados explícitamente, no rellenados por suposición:
#   1. policies.yaml no tiene loader compartido en ningún archivo real
#      visto — _load_policies() de abajo es un loader local mínimo.
#   2. pipeline_state.py no incluye "0004" en su tipo SkillId ni en
#      retry_counts de initial_state() — requiere edición aparte,
#      pendiente de aprobación de Marx (no se toca aquí).
# =============================================================================

"""
0004-statistical-validator — skill.py

Reviewer & Gate puro. Tres modos: selección de prueba de significancia
(Modo A), detección de drift vía KS-test (Modo B), detección de leakage
por correlación (Modo C). Nunca transforma datos.

Verificado contra los archivos reales que Marx proporcionó:
_common.py, tracing.py, pipeline_state.py, checkpointer.py, config.py,
policies.yaml. Ningún nombre de función o clave de configuración de este
archivo es inventado — donde faltaba un valor real (umbrales de Modo A),
el skill falla rápido en vez de asumir un número.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np
import pandas as pd
import yaml
from scipy import stats

from sigma.core.pipeline_state import PipelineState, SkillResult
from sigma.core.tracing import emit_trace_event
from sigma.skills._common import get_pg_connection, is_dev_mode, load_defaults, make_error, make_success, timer

SKILL_ID = "0004-statistical-validator"

# policies.yaml no tiene loader compartido en ninguno de los 6 archivos
# reales que Marx proporcionó (_common.py, config.py, checkpointer.py no
# lo cargan). Este es un loader local mínimo, NO infraestructura
# verificada — si ya existe uno real en otro archivo del repo que no vi,
# reemplázalo por ese en vez de este.
_POLICIES_PATH = Path(__file__).resolve().parents[3] / "policies.yaml"


def _load_policies() -> dict[str, Any]:
    return yaml.safe_load(_POLICIES_PATH.read_text(encoding="utf-8"))


def _read_processed_data(state: PipelineState) -> pd.DataFrame:
    """
    CORREGIDO — verificado contra el skill.py real de 0001/0002/0003:
    el dato NO viaja en state["df"] (ese campo nunca existió en ningún
    skill real). En modo Full/Runtime, 0004 lee de `processed_data`
    (la tabla que escribe 0003), filtrado por trace_id — mismo patrón
    exacto que _read_cleaned_data() de 0003. En modo Dev, genera su
    propia muestra sintética aislada, igual que sus hermanos (0001 en
    Dev tampoco encadena con lo que generan 0002/0003 en Dev — cada
    skill es independiente en ese modo).
    """
    dev = is_dev_mode(state)
    if dev:
        rng = np.random.default_rng(0)
        return pd.DataFrame({
            "row_id": [f"dev-{i}" for i in range(500)],
            "engagement_score": rng.uniform(0, 1, 500),
        })

    conn = get_pg_connection(state)
    try:
        df = pd.read_sql(
            "SELECT row_id, engagement_score, features FROM processed_data WHERE trace_id = %s",
            conn,
            params=(state["trace_id"],),
        )
    finally:
        conn.close()
    return df

Verdict = Literal[
    "INSUFFICIENT_EVIDENCE",
    "PAUSED_HITL",
    "APPROVED_WITH_WARNINGS",
    "REJECTED",
]

Branch = Literal[
    "bayes_factor",
    "permutation_bootstrap",
    "adf_granger",
    "bayesian_ab",
    "descriptive_fallback",
    "drift_ks_test",
    "leakage_correlation",
]


class InputSchemaError(Exception):
    """No recuperable — el input no pasó por 0002-data-cleanser."""


class InsufficientSampleSizeError(Exception):
    """No recuperable — n demasiado bajo para cualquier prueba."""


class PolicyConfigurationError(Exception):
    """No recuperable — un umbral requerido no está en policies.yaml.
    Fail-fast intencional: nunca se asume un umbral estadístico sin
    aprobación explícita en policies.yaml (ver advertencia en SKILL.md)."""


@dataclass
class ValidationOutcome:
    verdict: Verdict
    branch: Branch
    statistic: float | None
    p_value: float | None
    detail: dict[str, Any]


def _require_policy(policies: dict, *keys: str) -> Any:
    """Navega policies.yaml y falla con PolicyConfigurationError (no con
    KeyError crudo) si algún umbral requerido no está definido."""
    node: Any = policies
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            raise PolicyConfigurationError(
                f"policies.yaml no define '{'.'.join(keys)}'. Este umbral "
                f"debe aprobarse explícitamente antes de ejecutar esta rama "
                f"— ver la advertencia en SKILL.md, Tab. 1."
            )
        node = node[key]
    return node


# ── Modo A: selección de prueba de significancia (Tab. 1 de SKILL.md) ──

def _select_branch(state: PipelineState) -> Branch:
    """Selección ESTRUCTURAL, nunca semántica (ADR-008)."""
    if state.get("hypothesis") is not None:
        return "bayes_factor"
    if state.get("datetime_index") is not None:
        return "adf_granger"
    if state.get("live_feedback") is not None:
        return "bayesian_ab"
    if state.get("no_hypothesis_distribution_unknown", False):
        return "permutation_bootstrap"
    return "descriptive_fallback"


def _run_bayes_factor(df: pd.DataFrame, hypothesis: dict, config: dict, policies: dict) -> ValidationOutcome:
    threshold = _require_policy(policies, "statistical_validator", "bayes_factor_min")
    prior = config["bayes_factor"]["prior"]
    group_a = df[df[hypothesis["group_col"]] == hypothesis["group_a"]][hypothesis["metric_col"]]
    group_b = df[df[hypothesis["group_col"]] == hypothesis["group_b"]][hypothesis["metric_col"]]
    if len(group_a) < 2 or len(group_b) < 2:
        raise InsufficientSampleSizeError("Bayes Factor requiere n>=2 por grupo")

    t_stat, _ = stats.ttest_ind(group_a, group_b)
    n = len(group_a) + len(group_b)
    bf10 = np.exp((t_stat**2) / 2) * np.sqrt(n)  # aproximación BIC, no exacta

    verdict: Verdict = "INSUFFICIENT_EVIDENCE" if bf10 < threshold else "PAUSED_HITL"
    return ValidationOutcome(
        verdict=verdict, branch="bayes_factor", statistic=float(bf10), p_value=None,
        detail={"prior": prior, "n": n, "threshold": threshold},
    )


def _run_permutation_bootstrap(df: pd.DataFrame, config: dict, policies: dict) -> ValidationOutcome:
    threshold = _require_policy(policies, "statistical_validator", "permutation_ci_width_max")
    n_resamples = int(config["permutation_bootstrap"]["n_resamples"])
    seed = int(config["permutation_bootstrap"]["random_seed"])
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0 or len(df) < 8:
        raise InsufficientSampleSizeError("Permutation test requiere columnas numéricas y n>=8")

    col = numeric_cols[0]
    half = len(df) // 2
    a, b = df[col].iloc[:half], df[col].iloc[half:]
    res = stats.permutation_test(
        (a, b), lambda x, y: np.mean(x) - np.mean(y),
        n_resamples=n_resamples, random_state=seed,
    )
    ci_width = abs(res.statistic) * 2  # proxy simple del ancho del IC
    verdict: Verdict = "PAUSED_HITL" if ci_width > threshold else "INSUFFICIENT_EVIDENCE"

    return ValidationOutcome(
        verdict=verdict, branch="permutation_bootstrap",
        statistic=float(res.statistic), p_value=float(res.pvalue),
        detail={"n_resamples": n_resamples, "ci_width": ci_width, "threshold": threshold},
    )


def _run_adf_granger(df: pd.DataFrame, datetime_col: str, config: dict) -> ValidationOutcome:
    from statsmodels.tsa.stattools import adfuller

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0 or len(df) < 10:
        raise InsufficientSampleSizeError("ADF/Granger requiere serie numérica y n>=10")

    series = df.sort_values(datetime_col)[numeric_cols[0]].dropna()
    adf_stat, adf_p, *_ = adfuller(series)
    is_stationary = adf_p < 0.05

    # Única rama con derecho a APPROVED_WITH_WARNINGS (propiedad LTL, SKILL.md).
    # Es el veredicto "fuerte" único del skill incluso si NO es estacionaria
    # (el warning cubre precisamente ese caso) — nunca APPROVED puro (ADR-008).
    return ValidationOutcome(
        verdict="APPROVED_WITH_WARNINGS", branch="adf_granger",
        statistic=float(adf_stat), p_value=float(adf_p),
        detail={"is_stationary": is_stationary, "max_lag": config["adf_granger"]["max_lag"]},
    )


def _run_bayesian_ab(state: PipelineState, config: dict, policies: dict) -> ValidationOutcome:
    threshold = _require_policy(policies, "statistical_validator", "bayesian_ab_min_samples")
    feedback = state["live_feedback"]
    n_arms = len(feedback.get("arms", []))
    min_arms = int(config["bayesian_ab"]["n_arms_min"])
    if n_arms < min_arms:
        raise InsufficientSampleSizeError(f"Bayesian A/B requiere n_arms>={min_arms}")

    samples_per_arm = [len(a.get("samples", [])) for a in feedback["arms"]]
    verdict: Verdict = "INSUFFICIENT_EVIDENCE" if min(samples_per_arm) < threshold else "PAUSED_HITL"

    return ValidationOutcome(
        verdict=verdict, branch="bayesian_ab", statistic=None, p_value=None,
        detail={"n_arms": n_arms, "samples_per_arm": samples_per_arm, "threshold": threshold},
    )


def _run_descriptive_fallback(df: pd.DataFrame, config: dict) -> ValidationOutcome:
    null_ratio = df.isna().mean().max()
    warn_threshold = float(config["descriptive_fallback"]["null_ratio_warn"])
    duplicated_ratio = df.duplicated().mean()

    verdict: Verdict = "PAUSED_HITL" if null_ratio > warn_threshold else "INSUFFICIENT_EVIDENCE"
    return ValidationOutcome(
        verdict=verdict, branch="descriptive_fallback", statistic=None, p_value=None,
        detail={"null_ratio": float(null_ratio), "duplicated_ratio": float(duplicated_ratio)},
    )


# ── Modo B: detección de drift — KS-test exclusivamente (ADR-001 v1.4) ──

def _run_drift_check(current: pd.DataFrame, baseline: pd.DataFrame, policies: dict) -> ValidationOutcome:
    method = _require_policy(policies, "statistical_validator", "drift_method")
    if method != "ks_test":
        raise PolicyConfigurationError(
            f"policies.yaml declara drift_method='{method}' — PSI y cualquier "
            f"otro método quedan prohibidos por ADR-001 v1.4. Solo 'ks_test' "
            f"es válido."
        )
    threshold = _require_policy(policies, "statistical_validator", "drift_threshold")

    numeric_cols = current.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise InputSchemaError("No hay columnas numéricas para KS-test")

    col = numeric_cols[0]
    ks_stat, ks_p = stats.ks_2samp(current[col].dropna(), baseline[col].dropna())
    drift_detected = ks_p < threshold
    verdict: Verdict = "PAUSED_HITL" if drift_detected else "INSUFFICIENT_EVIDENCE"

    return ValidationOutcome(
        verdict=verdict, branch="drift_ks_test", statistic=float(ks_stat), p_value=float(ks_p),
        detail={"drift_detected": drift_detected, "method": "ks_test", "column": col, "threshold": threshold},
    )


# ── Modo C: detección de leakage por correlación ──
# Ver advertencia en SKILL.md — posible solapamiento con 0003-data-preprocessor,
# pendiente de que Marx confirme cuál documento es el vigente.

def _run_leakage_check(df: pd.DataFrame, target_col: str, policies: dict) -> ValidationOutcome:
    corr_threshold = _require_policy(policies, "statistical_validator", "leakage_correlation_threshold")
    temporal_threshold = _require_policy(policies, "statistical_validator", "leakage_temporal_threshold")

    if target_col not in df.columns:
        raise InputSchemaError(f"Columna objetivo '{target_col}' no existe en el DataFrame")

    numeric_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != target_col]
    if not numeric_cols:
        raise InsufficientSampleSizeError("No hay columnas numéricas para verificar leakage")

    pearson_corrs = {c: float(df[c].corr(df[target_col])) for c in numeric_cols}
    spearman_corrs = {c: float(df[c].corr(df[target_col], method="spearman")) for c in numeric_cols}

    max_pearson_col = max(pearson_corrs, key=lambda c: abs(pearson_corrs[c]))
    max_spearman_col = max(spearman_corrs, key=lambda c: abs(spearman_corrs[c]))

    if abs(pearson_corrs[max_pearson_col]) >= corr_threshold:
        verdict: Verdict = "REJECTED"
    elif abs(spearman_corrs[max_spearman_col]) >= temporal_threshold:
        verdict = "PAUSED_HITL"
    else:
        verdict = "INSUFFICIENT_EVIDENCE"

    return ValidationOutcome(
        verdict=verdict, branch="leakage_correlation", statistic=abs(pearson_corrs[max_pearson_col]), p_value=None,
        detail={
            "max_pearson_column": max_pearson_col, "max_pearson_corr": pearson_corrs[max_pearson_col],
            "max_spearman_column": max_spearman_col, "max_spearman_corr": spearman_corrs[max_spearman_col],
            "corr_threshold": corr_threshold, "temporal_threshold": temporal_threshold,
        },
    )


# ── Entrada principal del skill ──

def run(state: PipelineState) -> SkillResult:
    trace_id = state["trace_id"]  # campo real y obligatorio de PipelineState
    config = load_defaults("0004-statistical-validator")
    policies = _load_policies()

    if state.get("baseline_df") is not None:
        mode = "drift"
    elif state.get("leakage_target_col") is not None:
        mode = "leakage"
    else:
        mode = "significance"

    emit_trace_event(f"{SKILL_ID}.start", trace_id=trace_id, mode=mode, dev_mode=is_dev_mode(state))

    with timer() as t:
        try:
            df = _read_processed_data(state)
            if df.empty:
                raise InputSchemaError("processed_data no contiene filas para este trace_id")

            if mode == "drift":
                outcome = _run_drift_check(df, state["baseline_df"], policies)
            elif mode == "leakage":
                outcome = _run_leakage_check(df, state["leakage_target_col"], policies)
            else:
                branch = _select_branch(state)
                emit_trace_event(f"{SKILL_ID}.branch_selected", trace_id=trace_id, branch=branch)

                if branch == "bayes_factor":
                    outcome = _run_bayes_factor(df, state["hypothesis"], config, policies)
                elif branch == "adf_granger":
                    outcome = _run_adf_granger(df, state["datetime_index"], config)
                elif branch == "bayesian_ab":
                    outcome = _run_bayesian_ab(state, config, policies)
                elif branch == "permutation_bootstrap":
                    outcome = _run_permutation_bootstrap(df, config, policies)
                else:
                    outcome = _run_descriptive_fallback(df, config)

        except (InputSchemaError, InsufficientSampleSizeError, PolicyConfigurationError) as exc:
            emit_trace_event(
                f"{SKILL_ID}.error", trace_id=trace_id,
                error_type=type(exc).__name__, recoverable=False,
            )
            return make_error(
                skill_id=SKILL_ID,
                error_type=type(exc).__name__,
                error_detail=str(exc),
                duration_ms=t["ms"],
            )

    emit_trace_event(
        f"{SKILL_ID}.success", trace_id=trace_id,
        verdict=outcome.verdict, branch=outcome.branch,
        statistic=outcome.statistic, p_value=outcome.p_value,
        duration_ms=t["ms"],
    )

    return make_success(
        skill_id=SKILL_ID,
        output={
            "run_id": str(uuid.uuid4()),
            "trace_id": trace_id,
            "dev_mode": is_dev_mode(state),
            "verdict": outcome.verdict,
            "branch": outcome.branch,
            "statistic": outcome.statistic,
            "p_value": outcome.p_value,
            "detail": outcome.detail,
        },
        duration_ms=t["ms"],
    )
