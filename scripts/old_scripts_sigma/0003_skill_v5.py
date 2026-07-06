# =============================================================================
# skills/0003-data-preprocessor/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 / Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 2.0.0
# =============================================================================
# NOTA v2.0.0 — FUSIÓN (Opción C, con extensión de configuración condicional
# aprobada por Marx García). El skill.py original de "Eco MultiAgentes 3
# Skills 1" asumía un flujo de ENTRENAMIENTO supervisado (dataset ya
# etiquetado, típico de Kaggle), donde SMOTE/class_weight/PCA tienen
# sentido directo. Este pipeline es distinto: 0003 corre ANTES que
# 0008-sentiment-analyzer, que es quien GENERA la etiqueta de sentimiento.
# En este punto del pipeline no existe target_column todavía.
#
# Resolución: se incorpora TODA la lógica (leakage, SMOTE, class_weight,
# PCA), pero condicionada por configuración y por detección automática de
# target_column. Si no hay target_column, SMOTE y class_weight se OMITEN
# automáticamente sin error, sin importar el valor del flag. El mismo
# código sirve para este pipeline (todo desactivado) y para un futuro
# pipeline tipo Kaggle (activando los flags en defaults.yaml).
#
# LÍMITE ARQUITECTÓNICO EXPLÍCITO — SMOTE y filas sintéticas:
# SMOTE genera vectores numéricos sintéticos que no corresponden a
# ningún tweet real — no tienen texto, y por lo tanto no pueden escribirse
# en processed_data (0008 necesita clean_text real para clasificar).
# Las filas reales balanceadas por SMOTE se escriben normalmente; las
# filas SINTÉTICAS se reportan solo como métrica (conteo, distribución
# antes/después) — su persistencia física para un futuro entrenador
# queda como HUECO EXPLÍCITO, no resuelto en esta entrega, porque
# requiere una convención de artefacto (parquet/.npz) que este proyecto
# todavía no tiene definida.
# =============================================================================

from __future__ import annotations

import logging
import uuid

import numpy as np
import pandas as pd

from core.pipeline_state import PipelineState, SkillResult
from skills._common import get_pg_connection, is_dev_mode, load_defaults, make_error, make_success, timer

log = logging.getLogger("sigma.skills.0003")

SKILL_ID = "0003"
SKILL_DIR = "0003-data-preprocessor"


class NoDataToProcessError(Exception):
    pass


# ---------------------------------------------------------------------------
# Detección de idioma — sin cambios respecto a v1.0.0 (mejora futura aparte)
# ---------------------------------------------------------------------------

def _detect_lang_simple(text: str) -> str:
    text_lower = text.lower()
    spanish_markers = {"que", "de", "la", "el", "no", "muy", "está", "más"}
    english_markers = {"the", "and", "was", "very", "not", "this", "that"}
    tokens = set(text_lower.split())
    es_hits = len(tokens & spanish_markers)
    en_hits = len(tokens & english_markers)
    if es_hits > en_hits:
        return "es"
    if en_hits > es_hits:
        return "en"
    return "und"


def _compute_engagement_score(text: str) -> float:
    length_score = min(len(text) / 280.0, 1.0)
    emphasis_count = text.count("!") + text.count("?")
    emphasis_score = min(emphasis_count / 5.0, 1.0)
    return round((length_score * 0.7 + emphasis_score * 0.3), 4)


# ---------------------------------------------------------------------------
# Lectura de datos — cleaned_data + metadata de raw_data (para leakage/target)
# ---------------------------------------------------------------------------

def _read_cleaned_data(state: PipelineState) -> pd.DataFrame:
    dev = is_dev_mode(state)
    if dev:
        import random
        samples = [
            "Qué partidazo no lo puedo creer",
            "Muy decepcionante el resultado de hoy",
            "El arbitro estuvo regular nada mas",
            "Increible remontada del equipo local",
            "What a match this was amazing",
        ]
        rows = []
        for _ in range(500):
            rows.append({
                "row_id": f"dev-{uuid.uuid4().hex[:8]}",
                "cleaned_text": random.choice(samples),
                "metadata": {},  # sin target_column en modo Dev por defecto
            })
        return pd.DataFrame(rows)

    conn = get_pg_connection(state)
    try:
        df = pd.read_sql(
            """
            SELECT cd.row_id, cd.cleaned_text, rd.metadata
            FROM cleaned_data cd
            LEFT JOIN raw_data rd
                ON cd.row_id = rd.row_id AND cd.trace_id = rd.trace_id
            WHERE cd.trace_id = %s
            """,
            conn,
            params=(state["trace_id"],),
        )
    finally:
        conn.close()
    return df


def _detect_target_column(metadata_series: pd.Series, candidates: list[str]) -> str | None:
    """
    Busca, en orden, la primera columna candidata presente en al menos
    una fila de metadata. Devuelve None si ninguna existe — el llamador
    debe entonces omitir SMOTE/class_weight sin error.
    """
    all_keys: set[str] = set()
    for md in metadata_series:
        if isinstance(md, dict):
            all_keys.update(md.keys())
    for candidate in candidates:
        if candidate in all_keys:
            return candidate
    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)
        run_id = state.get("pipeline_run_id", state.get("trace_id", "unknown"))

        try:
            cfg = load_defaults(SKILL_DIR)
        except FileNotFoundError:
            cfg = {}

        target_candidates = cfg.get("target_detection", {}).get(
            "candidate_columns", ["sentiment_label", "label", "target"]
        )
        leakage_cols = set(cfg.get("leakage", {}).get("excluded_columns", ["future_engagement"]))
        apply_smote = bool(cfg.get("class_balancing", {}).get("apply_smote", False))
        apply_class_weight = bool(cfg.get("class_balancing", {}).get("apply_class_weight", False))
        imbalance_threshold = float(cfg.get("class_balancing", {}).get("imbalance_ratio_threshold", 3.0))
        apply_pca = bool(cfg.get("dimensionality_reduction", {}).get("apply_pca", False))
        pca_n_components = cfg.get("dimensionality_reduction", {}).get("n_components", 0.95)
        pca_min_features = int(cfg.get("dimensionality_reduction", {}).get("min_features_required", 3))

        df = _read_cleaned_data(state)

        if df.empty:
            return make_error(
                SKILL_ID, "NoDataToProcessError",
                "cleaned_data no contiene filas para este trace_id.", t["ms"],
            )

        df = df[df["cleaned_text"].str.strip() != ""].copy()
        if df.empty:
            return make_error(
                SKILL_ID, "NoDataToProcessError",
                "Todas las filas quedaron vacías tras la limpieza previa.", t["ms"],
            )

        if "metadata" not in df.columns:
            df["metadata"] = [{}] * len(df)
        df["metadata"] = df["metadata"].apply(lambda m: m if isinstance(m, dict) else {})

        df["clean_text"] = df["cleaned_text"]
        df["lang"] = df["clean_text"].apply(_detect_lang_simple)
        df["engagement_score"] = df["clean_text"].apply(_compute_engagement_score)

        # ── Detección automática de target_column ────────────────────────
        target_column = _detect_target_column(df["metadata"], target_candidates)
        target_detected = target_column is not None

        warnings: list[str] = []

        # ── Extracción de features numéricas adicionales de metadata,
        #    excluyendo leakage y la propia target_column ─────────────────
        extra_numeric_cols: list[str] = []
        all_metadata_keys: set[str] = set()
        for md in df["metadata"]:
            all_metadata_keys.update(md.keys())

        candidate_numeric_keys = all_metadata_keys - leakage_cols - ({target_column} if target_column else set())
        excluded_present = all_metadata_keys & leakage_cols
        if excluded_present:
            warnings.append(f"leakage_excluded:{sorted(excluded_present)}")

        for key in sorted(candidate_numeric_keys):
            values = df["metadata"].apply(lambda m: m.get(key))
            numeric_values = pd.to_numeric(values, errors="coerce")
            if numeric_values.notna().sum() == len(df):  # todas las filas tienen valor numérico válido
                df[f"_extra_{key}"] = numeric_values
                extra_numeric_cols.append(f"_extra_{key}")

        # ── Escalado real con StandardScaler ──────────────────────────────
        from sklearn.preprocessing import StandardScaler

        numeric_feature_cols = ["engagement_score"] + extra_numeric_cols
        scaler = StandardScaler()
        scaled_matrix = scaler.fit_transform(df[numeric_feature_cols].values)
        for i, col in enumerate(numeric_feature_cols):
            df[f"scaled_{col}"] = scaled_matrix[:, i]

        # ── PCA — se aplica por-fila, sin filas sintéticas, sin conflicto ─
        pca_applied = False
        pca_components_used = 0
        if apply_pca and len(numeric_feature_cols) >= pca_min_features:
            from sklearn.decomposition import PCA
            pca = PCA(n_components=pca_n_components)
            pca_result = pca.fit_transform(scaled_matrix)
            pca_applied = True
            pca_components_used = pca_result.shape[1]
            for i in range(pca_components_used):
                df[f"pca_{i}"] = pca_result[:, i]
        elif apply_pca:
            warnings.append(
                f"pca_skipped_insufficient_features:{len(numeric_feature_cols)}<{pca_min_features}"
            )

        # ── class_weight — solo métrica, nunca genera filas ───────────────
        class_weights: dict[str, float] | None = None
        if apply_class_weight and target_detected:
            y = df["metadata"].apply(lambda m: m.get(target_column))
            class_counts = y.value_counts()
            total = len(y)
            n_classes = len(class_counts)
            class_weights = {
                str(cls): round(total / (n_classes * count), 4)
                for cls, count in class_counts.items()
            }
        elif apply_class_weight and not target_detected:
            warnings.append("class_weight_skipped_no_target_column")

        # ── SMOTE — filas reales sin cambios, sintéticas solo reportadas ──
        num_smote_synthetic = 0
        class_distribution_before: dict[str, int] | None = None
        class_distribution_after: dict[str, int] | None = None

        if apply_smote and target_detected:
            y = df["metadata"].apply(lambda m: m.get(target_column))
            class_counts = y.value_counts()
            class_distribution_before = {str(k): int(v) for k, v in class_counts.items()}

            if len(class_counts) >= 2:
                ratio = class_counts.max() / class_counts.min()
                if ratio > imbalance_threshold:
                    try:
                        from imblearn.over_sampling import SMOTE
                        X = df[[f"scaled_{c}" for c in numeric_feature_cols]].values
                        y_valid_mask = y.notna()
                        minority_count = int(class_counts.min())

                        if minority_count < 2:
                            warnings.append(
                                f"smote_skipped_minority_too_small:{minority_count}<2"
                            )
                        elif y_valid_mask.sum() >= 2 and len(class_counts) >= 2:
                            # k_neighbors debe ser MENOR que el tamaño de la
                            # clase minoritaria — con el default fijo (5),
                            # SMOTE lanza ValueError si la minoría tiene
                            # menos de 6 muestras. Bug real encontrado al
                            # correr esta suite de pruebas, no hipotético.
                            k_neighbors = min(5, minority_count - 1)
                            smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                            X_res, y_res = smote.fit_resample(X[y_valid_mask.values], y[y_valid_mask].values)
                            num_smote_synthetic = len(X_res) - int(y_valid_mask.sum())
                            resampled_counts = pd.Series(y_res).value_counts()
                            class_distribution_after = {str(k): int(v) for k, v in resampled_counts.items()}
                            warnings.append(
                                "smote_synthetic_rows_not_persisted:"
                                "ver SKILL.md seccion 3 — hueco explicito documentado"
                            )
                    except ImportError:
                        warnings.append("smote_skipped_imblearn_not_installed")
                else:
                    warnings.append(f"smote_skipped_ratio_below_threshold:{ratio:.2f}<={imbalance_threshold}")
        elif apply_smote and not target_detected:
            warnings.append("smote_skipped_no_target_column")

        num_processed = len(df)
        lang_distribution = df["lang"].value_counts().to_dict()

        # ── Escritura — solo filas reales, con features en JSONB ──────────
        if not dev:
            import json
            conn = get_pg_connection(state)
            try:
                with conn.cursor() as cur:
                    for _, row in df.iterrows():
                        features = {
                            f"scaled_{c}": float(row[f"scaled_{c}"]) for c in numeric_feature_cols
                        }
                        if pca_applied:
                            features["pca"] = [
                                float(row[f"pca_{i}"]) for i in range(pca_components_used)
                            ]
                        cur.execute(
                            """
                            INSERT INTO processed_data
                                (row_id, clean_text, engagement_score, lang, features, trace_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            (
                                str(row["row_id"]), row["clean_text"],
                                float(row["engagement_score"]), row["lang"],
                                json.dumps(features), state["trace_id"],
                            ),
                        )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return make_error(
                    SKILL_ID, "PostgreSQLConnectionError",
                    f"Error al escribir en processed_data: {exc}", t["ms"],
                )
            finally:
                conn.close()

        pct_und = lang_distribution.get("und", 0) / max(num_processed, 1) * 100
        if pct_und > 30:
            warnings.append("high_undetermined_language_rate")
        if dev:
            warnings.append("synthetic_data")

        return make_success(
            SKILL_ID,
            {
                "num_processed": num_processed,
                "lang_distribution": lang_distribution,
                "target_column_detected": target_column,
                "extra_numeric_features": [c.replace("_extra_", "") for c in extra_numeric_cols],
                "pca_applied": pca_applied,
                "pca_components_used": pca_components_used,
                "class_weights": class_weights,
                "num_smote_synthetic_rows": num_smote_synthetic,
                "class_distribution_before": class_distribution_before,
                "class_distribution_after": class_distribution_after,
                "run_id": run_id,
                "trace_id": state.get("trace_id"),
                "dev_mode": dev,
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
