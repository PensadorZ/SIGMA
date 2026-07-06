# =============================================================================
# skills/0002-data-cleanser/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA v1.0.1: Reubicado desde skills/s0002_data_cleanser.py (flat) a esta carpeta,
#   siguiendo la convención ya establecida en Eco MultiAgentes 3 Skills 1:
#   'skill.py files in skills/000X-name/'. La resolución de import se
#   hace por ruta de archivo (importlib.util), no por paquete Python,
#   porque '000X-nombre-con-guion' no es un identificador válido.
# Implementación Python del skill 0002-data-cleanser.
# Elimina duplicados, marca nulos, limpia texto (URLs, menciones, emojis
# residuales) y escribe en cleaned_data.
# K ⊆ X: solo transforma deterministamente, nunca imputa ni infiere valores.
# =============================================================================

from __future__ import annotations

import logging
import re
import uuid

import pandas as pd

from core.pipeline_state import PipelineState, SkillResult
from skills._common import get_pg_connection, is_dev_mode, make_error, make_success, timer

log = logging.getLogger("sigma.skills.0002")

SKILL_ID = "0002"

_URL_RE = re.compile(r"https?://\S+")
_MENTION_RE = re.compile(r"@\w+")
_MULTISPACE_RE = re.compile(r"\s+")


class NoDataToCleanError(Exception):
    pass


def _clean_text(raw: str) -> str:
    """Limpieza determinista: sin URLs, sin menciones, espacios normalizados."""
    text = _URL_RE.sub("", raw)
    text = _MENTION_RE.sub("", text)
    text = _MULTISPACE_RE.sub(" ", text).strip()
    return text


def _read_raw_data(state: PipelineState) -> pd.DataFrame:
    dev = is_dev_mode(state)
    if dev:
        import random
        samples = [
            "Qué partidazo, no lo puedo creer  https://t.co/x @juan",
            "Muy decepcionante el resultado de hoy",
            "El árbitro estuvo regular, nada más   ",
            "Increíble remontada del equipo local @cuenta",
            "",  # fila vacía intencional para probar el flag had_nulls
        ]
        rows = [
            {"row_id": f"dev-{uuid.uuid4().hex[:8]}", "text": random.choice(samples)}
            for _ in range(500)
        ]
        return pd.DataFrame(rows)

    conn = get_pg_connection(state)
    try:
        df = pd.read_sql(
            "SELECT row_id, text FROM raw_data WHERE trace_id = %s",
            conn,
            params=(state["trace_id"],),
        )
    finally:
        conn.close()
    return df


def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)

        df = _read_raw_data(state)

        if df.empty:
            return make_error(
                SKILL_ID,
                "NoDataToCleanError",
                "raw_data no contiene filas para este trace_id.",
                t["ms"],
            )

        num_input = len(df)

        # ── Deduplicación ────────────────────────────────────────────────
        was_duplicate = df.duplicated(subset=["text"], keep="first")
        num_duplicates = int(was_duplicate.sum())
        df = df[~was_duplicate].copy()

        # ── Limpieza de texto + flag de nulos ────────────────────────────
        df["had_nulls"] = df["text"].isna() | (df["text"].str.strip() == "")
        num_nulls = int(df["had_nulls"].sum())
        df["cleaned_text"] = df["text"].fillna("").apply(_clean_text)

        num_output = len(df)

        # ── Escritura ─────────────────────────────────────────────────────
        if not dev:
            conn = get_pg_connection(state)
            try:
                with conn.cursor() as cur:
                    for _, row in df.iterrows():
                        cur.execute(
                            """
                            INSERT INTO cleaned_data
                                (row_id, cleaned_text, was_duplicate,
                                 had_nulls, trace_id)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                str(row["row_id"]),
                                row["cleaned_text"],
                                False,  # ya filtramos los duplicados
                                bool(row["had_nulls"]),
                                state["trace_id"],
                            ),
                        )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return make_error(
                    SKILL_ID,
                    "PostgreSQLConnectionError",
                    f"Error al escribir en cleaned_data: {exc}",
                    t["ms"],
                )
            finally:
                conn.close()

        warnings = []
        if num_duplicates / max(num_input, 1) > 0.20:
            warnings.append("high_duplicate_rate")
        if dev:
            warnings.append("synthetic_data")

        return make_success(
            SKILL_ID,
            {
                "num_records_input": num_input,
                "num_records_output": num_output,
                "num_duplicates_removed": num_duplicates,
                "num_nulls_flagged": num_nulls,
                "dev_mode": dev,
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
