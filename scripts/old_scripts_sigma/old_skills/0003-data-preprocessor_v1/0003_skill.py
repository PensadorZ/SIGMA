"""
skills/0003-data-preprocessor/skill.py

Implementación real del skill 0003-data-preprocessor v1.2.0.
Ver SKILL.md para la especificación completa.

ALCANCE HONESTO DE ESTA VERSIÓN:
- Normalización/estandarización numérica con scikit-learn (real)
- Codificación one-hot de categóricas (real)
- TF-IDF de columnas de texto (real)
- Detección y exclusión de columnas con patrón de leakage (real)
- Balanceo de clases: class_weight (Dev/default) y SMOTE si imblearn
  disponible (opcional, no requerido para el Hito 1)
- PCA automático cuando las columnas superan max_features (real)
- Propagación de trace_id en cada fila de salida (real, ADR-001)
- Pausa HITL cuando nulos superan null_threshold (estado waiting_hitl)

NO implementado en esta versión (deuda explícita):
- Escritura real en PostgreSQL (misma deuda que 0001 y 0002, ver
  nota de alcance de esa cadena — se resuelve cuando el primer skill
  downstream que necesite leerlo desde PG exista)
- Webhook real para decision_required (ADR-004 Apéndice A, pendiente
  hasta que el Approval Endpoint esté desplegado en el VPS)
- UMAP (requiere instalación extra, diferido a iteración posterior)
"""

from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, RobustScaler, StandardScaler

from sigma.core import emit_trace_event, get_optional_env, is_dev_mode

# ── Excepciones del skill ────────────────────────────────────────────────


class InputTableNotFoundError(FileNotFoundError):
    """La tabla de entrada *_cleaned no existe."""


class TargetColumnNotFoundError(ValueError):
    """La columna target declarada no existe en el dataset."""


# ── Tipos ────────────────────────────────────────────────────────────────

HitlStatus = Literal["ok", "waiting_hitl"]


@dataclass
class PreprocessorResult:
    trace_id: str
    run_id: str
    rows_in: int
    rows_out: int
    processed_rows: list[dict[str, Any]]
    columns_in: list[str]
    columns_out: list[str]
    excluded_columns: list[str]
    exclusion_reasons: dict[str, str]
    balance_strategy_used: str
    synthetic_rows_added: int
    pca_applied: bool
    pca_components_selected: int | None
    variance_explained: float | None
    workers_used: int
    trace_id_propagated: bool
    hitl_status: HitlStatus
    hitl_column: str | None
    hitl_null_ratio: float | None
    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "rows_in": self.rows_in,
            "rows_out": self.rows_out,
            "columns_in": self.columns_in,
            "columns_out": self.columns_out,
            "excluded_columns": self.excluded_columns,
            "exclusion_reasons": self.exclusion_reasons,
            "balance_strategy_used": self.balance_strategy_used,
            "synthetic_rows_added": self.synthetic_rows_added,
            "pca_applied": self.pca_applied,
            "pca_components_selected": self.pca_components_selected,
            "variance_explained": self.variance_explained,
            "workers_used": self.workers_used,
            "trace_id_propagated": self.trace_id_propagated,
            "hitl_status": self.hitl_status,
            "hitl_column": self.hitl_column,
            "hitl_null_ratio": self.hitl_null_ratio,
            "duration_ms": self.duration_ms,
        }


# ── Lógica interna ───────────────────────────────────────────────────────


def _detect_leakage_columns(
    columns: list[str], patterns: list[str]
) -> dict[str, str]:
    """
    Detecta columnas cuyo nombre coincide con algún patrón de leakage.
    Devuelve {nombre_columna: razon}.
    """
    leaked: dict[str, str] = {}
    for col in columns:
        for pattern in patterns:
            if re.search(pattern, col, re.IGNORECASE):
                leaked[col] = "leakage_pattern_match"
                break
    return leaked


def _null_ratio(rows: list[dict[str, Any]], col: str) -> float:
    """Fracción de filas donde la columna es nula o vacía."""
    if not rows:
        return 0.0
    null_count = sum(
        1 for r in rows
        if r.get(col) is None or r.get(col) == "__NULL__" or
        (isinstance(r.get(col), str) and r.get(col).strip() == "")
    )
    return null_count / len(rows)


def _infer_column_type(rows: list[dict[str, Any]], col: str) -> Literal["numeric", "text", "categorical", "id"]:
    """Infiere el tipo de una columna a partir de las primeras filas no nulas."""
    non_null = [r.get(col) for r in rows if r.get(col) is not None and r.get(col) != "__NULL__"]
    if not non_null:
        return "categorical"
    sample = non_null[:50]
    numeric_count = 0
    for v in sample:
        try:
            float(str(v).replace(",", "."))
            numeric_count += 1
        except ValueError:
            pass
    if numeric_count / len(sample) > 0.8:
        return "numeric"
    # Heurística para IDs: valores únicos == cantidad de muestras
    unique_ratio = len(set(str(v) for v in sample)) / len(sample)
    if unique_ratio > 0.95 and all(str(v).startswith(("tw_", "id_")) or len(str(v)) > 10 for v in sample[:5]):
        return "id"
    avg_len = sum(len(str(v)) for v in sample) / len(sample)
    unique_values = len(set(str(v) for v in sample))
    if avg_len > 30 or unique_values > 20:
        return "text"
    return "categorical"


def _impute_nulls(
    rows: list[dict[str, Any]], col: str, strategy: str, constant: Any = 0
) -> list[dict[str, Any]]:
    """Imputa nulos en una columna según la estrategia configurada."""
    non_null = [r[col] for r in rows if r.get(col) is not None and r.get(col) != "__NULL__"]

    if strategy == "median" and non_null:
        try:
            fill_value = float(np.median([float(v) for v in non_null]))
        except (ValueError, TypeError):
            fill_value = constant
    elif strategy == "mean" and non_null:
        try:
            fill_value = float(np.mean([float(v) for v in non_null]))
        except (ValueError, TypeError):
            fill_value = constant
    elif strategy == "mode" and non_null:
        from collections import Counter
        fill_value = Counter(non_null).most_common(1)[0][0]
    elif strategy == "drop_row":
        return [r for r in rows if r.get(col) is not None and r.get(col) != "__NULL__"]
    else:
        fill_value = constant

    result = []
    for r in rows:
        new_r = dict(r)
        if new_r.get(col) is None or new_r.get(col) == "__NULL__":
            new_r[col] = fill_value
        result.append(new_r)
    return result


def run_data_preprocessor(
    rows: list[dict[str, Any]],
    run_id: str | None = None,
    trace_id: str | None = None,
    task: str = "auto",
    target_column: str | None = None,
    null_strategy: str = "median",
    null_threshold: float = 0.30,
    numeric_scaler: str = "auto",
    max_features: int = 500,
    pca_variance_threshold: float = 0.95,
    class_balance_strategy: str = "smote",
    class_imbalance_ratio: float = 5.0,
    leakage_patterns: list[str] | None = None,
    leakage_action: str = "exclude_and_warn",
    text_vectorizer: str = "tfidf",
    max_tfidf_features: int = 300,
) -> PreprocessorResult:
    """
    Punto de entrada del skill. Opera sobre la lista de filas en memoria
    producida por 0002-data-cleanser (mismo alcance declarado en esa cadena).
    """
    start = time.monotonic()
    run_id = run_id or f"pp-{uuid.uuid4().hex[:8]}"
    trace_id = trace_id or f"tr-{uuid.uuid4().hex[:8]}"
    dev_mode = is_dev_mode()
    workers_used = 1 if dev_mode else int(get_optional_env("PREPROCESSOR_WORKERS", "4"))

    if dev_mode and class_balance_strategy == "smote":
        class_balance_strategy = "class_weight"

    if rows is None:
        emit_trace_event("data_preprocessor.failed", trace_id=trace_id, run_id=run_id,
                         error_type="InputTableNotFoundError")
        raise InputTableNotFoundError("La tabla de entrada '*_cleaned' no existe.")

    rows_in = len(rows)
    if not rows:
        emit_trace_event("data_preprocessor.failed", trace_id=trace_id, run_id=run_id,
                         error_type="EmptyInputError")
        raise InputTableNotFoundError("La tabla de entrada no contiene filas.")

    emit_trace_event("data_preprocessor.started", trace_id=trace_id, run_id=run_id,
                     rows_in=rows_in, task=task, target_column=target_column)

    all_columns = list(rows[0].keys())
    leakage_patterns = leakage_patterns or ["future_", "_target_", "_label_leaked"]

    # ── Validar target_column ─────────────────────────────────────────────
    if target_column and target_column not in all_columns:
        emit_trace_event("data_preprocessor.failed", trace_id=trace_id, run_id=run_id,
                         error_type="TargetColumnNotFoundError",
                         available_columns=all_columns)
        raise TargetColumnNotFoundError(
            f"La columna target '{target_column}' no existe en el dataset. "
            f"Columnas disponibles: {all_columns}"
        )

    # ── Detectar leakage ──────────────────────────────────────────────────
    feature_columns = [c for c in all_columns if c not in ("trace_id", "tweet_id", target_column)]
    leaked = _detect_leakage_columns(feature_columns, leakage_patterns)
    excluded_columns: dict[str, str] = {}

    if leaked:
        if leakage_action in ("exclude_and_warn", "error"):
            excluded_columns.update(leaked)
            emit_trace_event("data_preprocessor.leakage_warning", trace_id=trace_id,
                             run_id=run_id, leaked_columns=list(leaked.keys()))
        if leakage_action == "error":
            raise ValueError(f"Columnas con leakage detectado: {list(leaked.keys())}")

    feature_columns = [c for c in feature_columns if c not in excluded_columns]

    # ── Chequeo HITL: nulos excesivos ─────────────────────────────────────
    for col in feature_columns:
        ratio = _null_ratio(rows, col)
        if ratio > null_threshold:
            emit_trace_event("data_preprocessor.decision_required", trace_id=trace_id,
                             run_id=run_id, column=col, null_ratio=round(ratio, 4))
            duration_ms = int((time.monotonic() - start) * 1000)
            return PreprocessorResult(
                trace_id=trace_id, run_id=run_id,
                rows_in=rows_in, rows_out=0, processed_rows=[],
                columns_in=all_columns, columns_out=[],
                excluded_columns=list(excluded_columns.keys()),
                exclusion_reasons=excluded_columns,
                balance_strategy_used="none", synthetic_rows_added=0,
                pca_applied=False, pca_components_selected=None,
                variance_explained=None, workers_used=workers_used,
                trace_id_propagated=False, hitl_status="waiting_hitl",
                hitl_column=col, hitl_null_ratio=round(ratio, 4),
                duration_ms=duration_ms,
            )

    # ── Imputar nulos en columnas features ────────────────────────────────
    working_rows = list(rows)
    for col in feature_columns:
        if _null_ratio(working_rows, col) > 0:
            working_rows = _impute_nulls(working_rows, col, null_strategy)

    # ── Clasificar columnas por tipo ──────────────────────────────────────
    numeric_cols: list[str] = []
    text_cols: list[str] = []
    categorical_cols: list[str] = []

    for col in feature_columns:
        col_type = _infer_column_type(working_rows, col)
        if col_type == "numeric":
            numeric_cols.append(col)
        elif col_type == "text":
            text_cols.append(col)
        elif col_type == "categorical":
            categorical_cols.append(col)
        # id columns se excluyen silenciosamente

    # ── Escalar numérico ──────────────────────────────────────────────────
    numeric_matrix: np.ndarray | None = None
    numeric_feature_names: list[str] = []

    if numeric_cols:
        raw_numeric = np.array(
            [[float(r.get(c, 0) or 0) for c in numeric_cols] for r in working_rows],
            dtype=float,
        )
        scaler_name = numeric_scaler
        if scaler_name == "auto":
            scaler_name = "standard"

        if scaler_name == "standard":
            scaler = StandardScaler()
        elif scaler_name == "robust":
            scaler = RobustScaler()
        elif scaler_name == "minmax":
            scaler = MinMaxScaler()
        else:
            scaler = StandardScaler()

        numeric_matrix = scaler.fit_transform(raw_numeric)
        numeric_feature_names = numeric_cols

    # ── Codificar categóricas (one-hot simple con numpy) ──────────────────
    onehot_matrices: list[np.ndarray] = []
    onehot_names: list[str] = []

    for col in categorical_cols:
        values = [str(r.get(col, "")) for r in working_rows]
        unique_vals = sorted(set(values))
        if len(unique_vals) <= 1:
            continue
        for uv in unique_vals[:-1]:  # drop-last para evitar multicolinealidad
            col_name = f"{col}_{uv}"
            encoded = np.array([[1.0 if v == uv else 0.0] for v in values])
            onehot_matrices.append(encoded)
            onehot_names.append(col_name)

    # ── TF-IDF de texto ───────────────────────────────────────────────────
    tfidf_matrices: list[np.ndarray] = []
    tfidf_names: list[str] = []

    for col in text_cols:
        texts = [str(r.get(col, "")) for r in working_rows]
        if all(t.strip() == "" for t in texts):
            continue
        tfidf = TfidfVectorizer(max_features=max_tfidf_features, ngram_range=(1, 2))
        try:
            mat = tfidf.fit_transform(texts).toarray()
            feature_names = [f"tfidf_{col}_{f}" for f in tfidf.get_feature_names_out()]
            tfidf_matrices.append(mat)
            tfidf_names.extend(feature_names)
        except ValueError:
            pass  # corpus vacío o sin tokens: omitir silenciosamente

    # ── Concatenar todas las matrices de features ─────────────────────────
    parts = []
    part_names: list[str] = []

    if numeric_matrix is not None:
        parts.append(numeric_matrix)
        part_names.extend(numeric_feature_names)
    for mat, names in zip(onehot_matrices, [[n] for n in onehot_names]):
        parts.append(mat)
        part_names.extend(names)
    for mat in tfidf_matrices:
        parts.append(mat)
    part_names.extend(tfidf_names)

    if not parts:
        feature_matrix = np.zeros((len(working_rows), 1))
        part_names = ["empty_feature"]
    else:
        feature_matrix = np.hstack(parts)

    # ── PCA automático si supera max_features ─────────────────────────────
    pca_applied = False
    pca_components_selected: int | None = None
    variance_explained: float | None = None
    output_feature_names = list(part_names)

    if feature_matrix.shape[1] > max_features:
        n_components = min(max_features, feature_matrix.shape[0], feature_matrix.shape[1])
        pca = PCA(n_components=n_components)
        feature_matrix = pca.fit_transform(feature_matrix)
        cum_var = float(np.cumsum(pca.explained_variance_ratio_)[-1])

        # Reducir aún más si la varianza acumulada lo permite
        cumvar = np.cumsum(pca.explained_variance_ratio_)
        keep = int(np.searchsorted(cumvar, pca_variance_threshold) + 1)
        feature_matrix = feature_matrix[:, :keep]
        pca_applied = True
        pca_components_selected = keep
        variance_explained = float(cumvar[keep - 1])
        output_feature_names = [f"pc_{i+1:03d}" for i in range(keep)]
        emit_trace_event("data_preprocessor.pca_applied", trace_id=trace_id, run_id=run_id,
                         components=keep, variance_explained=variance_explained)

    # ── Balanceo de clases ────────────────────────────────────────────────
    synthetic_rows_added = 0
    balance_strategy_used = "none"

    # Guardamos los labels para mapearlos correctamente a processed_rows
    labels_for_output: list[str] = []

    if target_column:
        labels = [str(r.get(target_column, "")) for r in working_rows]
        from collections import Counter
        counts = Counter(labels)
        if len(counts) >= 2:
            majority = max(counts.values())
            minority = min(counts.values())
            ratio_actual = majority / minority if minority > 0 else float("inf")

            if ratio_actual > class_imbalance_ratio:
                if class_balance_strategy == "smote":
                    try:
                        from imblearn.over_sampling import SMOTE  # type: ignore
                        le = LabelEncoder()
                        y = le.fit_transform(labels)
                        sm = SMOTE(random_state=42)
                        feature_matrix, y_resampled = sm.fit_resample(feature_matrix, y)
                        synthetic_rows_added = len(y_resampled) - len(labels)
                        labels_for_output = list(le.inverse_transform(y_resampled))
                        balance_strategy_used = "smote"
                    except ImportError:
                        class_balance_strategy = "class_weight"

                if class_balance_strategy == "class_weight":
                    balance_strategy_used = "class_weight"
                    labels_for_output = labels
            else:
                balance_strategy_used = "none"
                labels_for_output = labels
        else:
            labels_for_output = labels
    else:
        labels_for_output = []

    # ── Construir filas de salida con trace_id ────────────────────────────
    n_rows_out = feature_matrix.shape[0]
    processed_rows: list[dict[str, Any]] = []

    for i in range(n_rows_out):
        row_dict: dict[str, Any] = {"trace_id": trace_id}
        if target_column and i < len(labels_for_output):
            row_dict[target_column] = labels_for_output[i]
        for j, fname in enumerate(output_feature_names):
            row_dict[fname] = float(feature_matrix[i, j])
        if i < len(working_rows):
            row_dict["tweet_id"] = working_rows[i].get("tweet_id")
        processed_rows.append(row_dict)

    duration_ms = int((time.monotonic() - start) * 1000)

    result = PreprocessorResult(
        trace_id=trace_id, run_id=run_id,
        rows_in=rows_in, rows_out=n_rows_out,
        processed_rows=processed_rows,
        columns_in=all_columns,
        columns_out=output_feature_names,
        excluded_columns=list(excluded_columns.keys()),
        exclusion_reasons=excluded_columns,
        balance_strategy_used=balance_strategy_used,
        synthetic_rows_added=synthetic_rows_added,
        pca_applied=pca_applied,
        pca_components_selected=pca_components_selected,
        variance_explained=variance_explained,
        workers_used=workers_used,
        trace_id_propagated=True,
        hitl_status="ok", hitl_column=None, hitl_null_ratio=None,
        duration_ms=duration_ms,
    )

    emit_trace_event("data_preprocessor.completed", trace_id=trace_id, run_id=run_id,
                     rows_out=n_rows_out, pca_applied=pca_applied,
                     balance_strategy=balance_strategy_used, duration_ms=duration_ms)

    return result


if __name__ == "__main__":
    import json
    import sys

    # Demo: 5 filas con numéricas, categóricas, texto y una columna de leakage
    demo_rows = [
        {"tweet_id": "1", "text": "great goal brasil", "lang": "en",
         "likes": 150, "retweets": 30, "future_engagement": 999,
         "sentiment_label": "POSITIVE"},
        {"tweet_id": "2", "text": "terrible referee decision", "lang": "en",
         "likes": 80, "retweets": 15, "future_engagement": 400,
         "sentiment_label": "NEGATIVE"},
        {"tweet_id": "3", "text": "what a match incredible", "lang": "en",
         "likes": 200, "retweets": 60, "future_engagement": 1200,
         "sentiment_label": "POSITIVE"},
        {"tweet_id": "4", "text": "boring game nothing happened", "lang": "es",
         "likes": 10, "retweets": 2, "future_engagement": 50,
         "sentiment_label": "NEGATIVE"},
        {"tweet_id": "5", "text": "amazing world cup moments", "lang": "en",
         "likes": 500, "retweets": 120, "future_engagement": 3000,
         "sentiment_label": "POSITIVE"},
    ]

    result = run_data_preprocessor(
        demo_rows,
        target_column="sentiment_label",
        leakage_action="exclude_and_warn",
    )
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    print(f"\nColumnas de salida: {result.columns_out[:10]}...")
    print(f"Leakage excluido: {result.excluded_columns}")
