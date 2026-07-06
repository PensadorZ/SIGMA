# =============================================================================
# skills/0002-data-cleanser/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 / Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 2.0.0
# =============================================================================
# NOTA v2.0.0 — FUSIÓN (Opción C, política por defecto confirmada en
# Eco MultiAgentes 4 Skills 2). Incorpora sobre la base ya verificada:
#   - Deduplicación de CASI-exactos (near-duplicates), además de los
#     exactos que ya existían. Implementada en O(n) por agrupación con
#     clave normalizada — NO por comparación por pares O(n²), que fue
#     exactamente el bug de rendimiento que "Eco MultiAgentes 3 Skills 1"
#     encontró y corrigió (290s para 22.500 filas con el algoritmo
#     ingenuo). Aquí se evita ese error desde el diseño, no se repite.
#   - Tabla cleaned_rejected para filas con schema inválido, separadas
#     de cleaned_data en vez de solo marcarlas con un flag.
#   - run_id junto a trace_id en el output.
#
# DECISIÓN DE ADAPTACIÓN: la versión original definía "schema inválido"
# como tweet_id no castable a entero. En este proyecto row_id es un
# string libre (ej. 'row-42', 'dev-a1b2c3d4'), no siempre numérico —
# no tendría sentido aplicar esa regla tal cual. Se adapta el criterio
# de rechazo a lo que sí es estructuralmente inválido aquí: row_id nulo
# o vacío, que impide cualquier trazabilidad downstream.
#
# SIGMA_VARIANT se mantiene (no se renombra a SIGMA_ENV) — decisión ya
# tomada explícitamente: el costo de propagar un renombrado de variable
# de entorno por todo el proyecto no se justifica frente al beneficio
# cosmético de adoptar el nombre de la otra línea de trabajo.
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
_PUNCTUATION_RE = re.compile(r"[^\w\s]")


class NoDataToCleanError(Exception):
    pass


def _clean_text(raw: str) -> str:
    """Limpieza determinista: sin URLs, sin menciones, espacios normalizados."""
    text = _URL_RE.sub("", raw)
    text = _MENTION_RE.sub("", text)
    text = _MULTISPACE_RE.sub(" ", text).strip()
    return text


def _normalize_for_near_dup(cleaned: str) -> str:
    """
    Clave de normalización PARA AGRUPAR casi-duplicados, más agresiva
    que _clean_text: minúsculas y sin puntuación, además de lo que
    _clean_text ya quita. Dos filas cuyo texto limpio solo difiere en
    mayúsculas o puntuación producen la MISMA clave aquí, y por lo
    tanto se agrupan como casi-duplicados.

    O(n): esta función se aplica una vez por fila, y el agrupamiento
    posterior es un groupby de pandas — nunca una comparación por pares.
    """
    lowered = cleaned.lower()
    no_punct = _PUNCTUATION_RE.sub("", lowered)
    return _MULTISPACE_RE.sub(" ", no_punct).strip()


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
        run_id = state.get("pipeline_run_id", state.get("trace_id", "unknown"))

        df = _read_raw_data(state)

        if df.empty:
            return make_error(
                SKILL_ID, "NoDataToCleanError",
                "raw_data no contiene filas para este trace_id.", t["ms"],
            )

        num_input = len(df)

        # ── 1. Filas rechazadas por schema inválido ─────────────────────
        # row_id nulo o vacío no se puede trazar downstream — se separa
        # a cleaned_rejected en vez de intentar procesarlo.
        invalid_row_id_mask = df["row_id"].isna() | (df["row_id"].astype(str).str.strip() == "")
        rejected_df = df[invalid_row_id_mask].copy()
        df = df[~invalid_row_id_mask].copy()
        num_rejected_schema = len(rejected_df)

        # ── 2. Deduplicación exacta (idéntica desde v1.0.0, sin cambios) ─
        was_exact_duplicate = df.duplicated(subset=["text"], keep="first")
        num_exact_duplicates = int(was_exact_duplicate.sum())
        df = df[~was_exact_duplicate].copy()

        # ── 3. Limpieza de texto + flag de nulos (sin cambios) ───────────
        df["had_nulls"] = df["text"].isna() | (df["text"].str.strip() == "")
        num_nulls = int(df["had_nulls"].sum())
        df["cleaned_text"] = df["text"].fillna("").apply(_clean_text)

        # ── 4. Deduplicación de casi-exactos — NUEVO, O(n) ───────────────
        df["_near_dup_key"] = df["cleaned_text"].apply(_normalize_for_near_dup)
        was_near_duplicate = df.duplicated(subset=["_near_dup_key"], keep="first")
        # No cuenta como casi-duplicado si la clave normalizada quedó vacía
        # (texto que era solo URL/mención, ej.) — evitaría agrupar de más.
        was_near_duplicate = was_near_duplicate & (df["_near_dup_key"] != "")
        num_near_duplicates = int(was_near_duplicate.sum())
        df = df[~was_near_duplicate].copy()
        df = df.drop(columns=["_near_dup_key"])

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
                                False,
                                bool(row["had_nulls"]),
                                state["trace_id"],
                            ),
                        )
                    for _, row in rejected_df.iterrows():
                        cur.execute(
                            """
                            INSERT INTO cleaned_rejected
                                (row_id, raw_text, rejection_reason, trace_id)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                str(row["row_id"]) if pd.notna(row["row_id"]) else "unknown",
                                str(row.get("text", "")),
                                "missing_row_id",
                                state["trace_id"],
                            ),
                        )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return make_error(
                    SKILL_ID, "PostgreSQLConnectionError",
                    f"Error al escribir en cleaned_data/cleaned_rejected: {exc}",
                    t["ms"],
                )
            finally:
                conn.close()

        warnings = []
        if num_exact_duplicates / max(num_input, 1) > 0.20:
            warnings.append("high_duplicate_rate")
        if num_rejected_schema > 0:
            warnings.append("rows_rejected_schema")
        if dev:
            warnings.append("synthetic_data")

        return make_success(
            SKILL_ID,
            {
                "num_records_input": num_input,
                "num_records_output": num_output,
                "num_exact_duplicates_removed": num_exact_duplicates,
                "num_near_duplicates_removed": num_near_duplicates,
                "num_rejected_schema": num_rejected_schema,
                "num_nulls_flagged": num_nulls,
                "run_id": run_id,
                "trace_id": state.get("trace_id"),
                "dev_mode": dev,
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
