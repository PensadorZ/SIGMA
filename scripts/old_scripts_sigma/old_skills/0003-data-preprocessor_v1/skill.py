# =============================================================================
# skills/0003-data-preprocessor/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA v1.0.1: Reubicado desde skills/s0003_data_preprocessor.py (flat) a esta carpeta,
#   siguiendo la convención ya establecida en Eco MultiAgentes 3 Skills 1:
#   'skill.py files in skills/000X-name/'. La resolución de import se
#   hace por ruta de archivo (importlib.util), no por paquete Python,
#   porque '000X-nombre-con-guion' no es un identificador válido.
# Implementación Python del skill 0003-data-preprocessor.
# Detecta idioma, calcula un engagement_score determinista y escribe
# processed_data con las columnas que 0008-sentiment-analyzer necesita
# (clean_text, engagement_score, lang).
# K ⊆ X: engagement_score se calcula con una fórmula determinista sobre
# features ya presentes (longitud, signos de puntuación) — no se infiere.
# =============================================================================

from __future__ import annotations

import logging
import uuid

import pandas as pd

from core.pipeline_state import PipelineState, SkillResult
from skills._common import get_pg_connection, is_dev_mode, make_error, make_success, timer

log = logging.getLogger("sigma.skills.0003")

SKILL_ID = "0003"


class NoDataToProcessError(Exception):
    pass


def _detect_lang_simple(text: str) -> str:
    """
    Heurística determinista simple para el Hito 1 (sin dependencia de
    modelos de detección de idioma). Sustituible por langdetect/fasttext
    en el Hito 2 sin cambiar el contrato de salida (columna 'lang').
    """
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
    return "und"  # indeterminado — no se fuerza una etiqueta (K ⊆ X)


def _compute_engagement_score(text: str) -> float:
    """
    Fórmula determinista sobre features ya observadas: longitud del texto
    y densidad de signos de énfasis. No es un modelo, no infiere intención.
    """
    length_score = min(len(text) / 280.0, 1.0)
    emphasis_count = text.count("!") + text.count("?")
    emphasis_score = min(emphasis_count / 5.0, 1.0)
    return round((length_score * 0.7 + emphasis_score * 0.3), 4)


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
        rows = [
            {"row_id": f"dev-{uuid.uuid4().hex[:8]}", "cleaned_text": random.choice(samples)}
            for _ in range(500)
        ]
        return pd.DataFrame(rows)

    conn = get_pg_connection(state)
    try:
        df = pd.read_sql(
            "SELECT row_id, cleaned_text FROM cleaned_data WHERE trace_id = %s",
            conn,
            params=(state["trace_id"],),
        )
    finally:
        conn.close()
    return df


def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)

        df = _read_cleaned_data(state)

        if df.empty:
            return make_error(
                SKILL_ID,
                "NoDataToProcessError",
                "cleaned_data no contiene filas para este trace_id.",
                t["ms"],
            )

        # Excluye filas con texto vacío tras limpieza (no infiere contenido)
        df = df[df["cleaned_text"].str.strip() != ""].copy()

        if df.empty:
            return make_error(
                SKILL_ID,
                "NoDataToProcessError",
                "Todas las filas quedaron vacías tras la limpieza previa.",
                t["ms"],
            )

        df["clean_text"] = df["cleaned_text"]
        df["lang"] = df["clean_text"].apply(_detect_lang_simple)
        df["engagement_score"] = df["clean_text"].apply(_compute_engagement_score)

        num_processed = len(df)
        lang_distribution = df["lang"].value_counts().to_dict()

        # ── Escritura ─────────────────────────────────────────────────────
        if not dev:
            conn = get_pg_connection(state)
            try:
                with conn.cursor() as cur:
                    for _, row in df.iterrows():
                        cur.execute(
                            """
                            INSERT INTO processed_data
                                (row_id, clean_text, engagement_score,
                                 lang, trace_id)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                str(row["row_id"]),
                                row["clean_text"],
                                float(row["engagement_score"]),
                                row["lang"],
                                state["trace_id"],
                            ),
                        )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return make_error(
                    SKILL_ID,
                    "PostgreSQLConnectionError",
                    f"Error al escribir en processed_data: {exc}",
                    t["ms"],
                )
            finally:
                conn.close()

        warnings = []
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
                "dev_mode": dev,
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
