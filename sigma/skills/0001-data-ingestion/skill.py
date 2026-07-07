# =============================================================================
# skills/0001-data-ingestion/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1 / Eco MultiAgentes 4 Skills 2
# Autor: Prof. Marx Agustín García Delgado
# Versión: 2.0.1
# =============================================================================
# NOTA v2.0.1 — Corrección de bug: valores NaN de pandas en columnas
# opcionales (ej. selected_text vacío) rompían la serialización JSON al
# escribir en PostgreSQL, porque json.dumps() convierte NaN al token
# literal `NaN`, que no es JSON válido según RFC 8259. Se sanea cada
# valor con pd.isna() antes de construir el diccionario metadata,
# convirtiendo NaN/NaT a None (que sí serializa como `null`).
#
# NOTA v2.0.0 — FUSIÓN (Opción C, política por defecto confirmada en
# Eco MultiAgentes 4 Skills 2). Incorpora sobre la base ya verificada:
#   - checksum_sha256 del archivo fuente (integridad, trazabilidad)
#   - run_id junto a trace_id en el output
#   - Lectura en chunks con métrica chunks_processed (arquitectura lista
#     para el Hito 2, workers=1 secuencial en el Hito 1 — ver SKILL.md)
#
# Los nombres de excepción (SourceNotFoundError, EmptySourceError,
# SchemaValidationError) YA COINCIDÍAN entre ambas líneas de trabajo —
# no fue necesario reconciliar nada ahí.
# =============================================================================

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from pathlib import Path

import pandas as pd

from sigma.core.pipeline_state import PipelineState, SkillResult
from sigma.skills._common import (
    get_pg_connection,
    is_dev_mode,
    load_defaults,
    make_error,
    make_success,
    timer,
)

log = logging.getLogger("sigma.skills.0001")

SKILL_ID = "0001"
SKILL_DIR = "0001-data-ingestion"

# Valor histórico — YA NO SE USA en run(), que ahora lee esto desde
# defaults.yaml (ingestion.required_column). Se conserva solo como
# referencia rápida de cuál es el default esperado sin abrir el YAML.
REQUIRED_COLUMN = "text"


class SourceNotFoundError(Exception):
    pass


class EmptySourceError(Exception):
    pass


class SchemaValidationError(Exception):
    pass


def _generate_synthetic_rows(n: int = 500) -> pd.DataFrame:
    """Modo Dev: genera filas sintéticas sin tocar el filesystem."""
    import random

    samples_es = [
        "Qué partidazo, no lo puedo creer",
        "Muy decepcionante el resultado de hoy",
        "El árbitro estuvo regular, nada más",
        "Increíble remontada del equipo local",
        "No entiendo por qué no cambiaron antes",
    ]
    rows = [
        {"row_id": f"dev-{uuid.uuid4().hex[:8]}", "text": random.choice(samples_es)}
        for _ in range(n)
    ]
    return pd.DataFrame(rows)


def _compute_checksum_sha256(path: Path, block_size: int = 65536) -> str:
    """
    Calcula el checksum SHA-256 del archivo fuente en modo streaming —
    no carga el archivo completo en memoria solo para este cálculo,
    importante para cuando el Hito 2 traiga datasets de cientos de MB.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            sha256.update(block)
    return sha256.hexdigest()


def _read_in_chunks(path: Path, chunk_size: int) -> tuple[pd.DataFrame, int]:
    """
    Lee el CSV en chunks vía pandas.read_csv(chunksize=...) y los
    concatena. Con workers=1 (Hito 1) esto es secuencial — la ganancia
    real es que la arquitectura queda lista para paralelizar en el
    Hito 2 sin reescribir esta función, solo el bucle que la consume.

    Returns:
        (DataFrame concatenado, número de chunks procesados)
    """
    chunks = []
    chunks_processed = 0
    for chunk in pd.read_csv(path, chunksize=chunk_size):
        chunks.append(chunk)
        chunks_processed += 1
    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    return df, chunks_processed


def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)
        run_id = state.get("pipeline_run_id", state.get("trace_id", "unknown"))

        try:
            cfg = load_defaults(SKILL_DIR)
        except FileNotFoundError:
            cfg = {"ingestion": {"chunk_size": 25000}}

        chunk_size = int(cfg.get("ingestion", {}).get("chunk_size", 25000))
        required_column = cfg.get("ingestion", {}).get("required_column", "text")

        # ── Carga de datos ───────────────────────────────────────────────
        checksum: str | None = None
        chunks_processed = 0

        if dev:
            df = _generate_synthetic_rows(500)
        else:
            data_path = Path(state["data_path"])
            if not data_path.exists():
                return make_error(
                    SKILL_ID, "SourceNotFoundError",
                    f"No se encontró el archivo de datos en '{data_path}'.",
                    t["ms"],
                )

            # Checksum ANTES de cualquier procesamiento — garantiza que
            # refleja exactamente el archivo tal como se encontró.
            try:
                checksum = _compute_checksum_sha256(data_path)
            except Exception as exc:  # noqa: BLE001
                return make_error(
                    SKILL_ID, "SourceNotFoundError",
                    f"Error al calcular checksum de '{data_path}': {exc}",
                    t["ms"],
                )

            try:
                df, chunks_processed = _read_in_chunks(data_path, chunk_size)
            except Exception as exc:  # noqa: BLE001
                return make_error(
                    SKILL_ID, "SourceNotFoundError",
                    f"Error al leer el CSV en '{data_path}': {exc}",
                    t["ms"],
                )

            if df.empty:
                return make_error(
                    SKILL_ID, "EmptySourceError",
                    f"El archivo '{data_path}' no contiene filas.",
                    t["ms"],
                )

            if required_column not in df.columns:
                return make_error(
                    SKILL_ID, "SchemaValidationError",
                    f"Columna requerida '{required_column}' no encontrada. "
                    f"Columnas presentes: {list(df.columns)}.",
                    t["ms"],
                )

            if "row_id" not in df.columns:
                df["row_id"] = [f"row-{i}" for i in range(len(df))]

        num_records = len(df)

        # ── Escritura ─────────────────────────────────────────────────────
        if not dev:
            conn = get_pg_connection(state)
            try:
                with conn.cursor() as cur:
                    for _, row in df.iterrows():
                        # FIX v2.0.1: sanear NaN/NaT de pandas antes de
                        # serializar a JSON. json.dumps() convierte NaN al
                        # token literal `NaN`, inválido según RFC 8259.
                        # pd.isna() detecta NaN, NaT y None de forma
                        # uniforme; se normaliza todo a None → `null`.
                        metadata = {
                            k: (None if pd.isna(v) else v)
                            for k, v in row.items()
                            if k not in ("row_id", "text")
                        }
                        cur.execute(
                            """
                            INSERT INTO raw_data (row_id, text, metadata, trace_id)
                            VALUES (%s, %s, %s, %s)
                            """,
                            (
                                str(row["row_id"]),
                                str(row["text"]),
                                json.dumps(metadata, default=str),
                                state["trace_id"],
                            ),
                        )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return make_error(
                    SKILL_ID, "PostgreSQLConnectionError",
                    f"Error al escribir en raw_data: {exc}", t["ms"],
                )
            finally:
                conn.close()

        return make_success(
            SKILL_ID,
            {
                "num_records": num_records,
                "source_path": str(state.get("data_path", "synthetic")),
                "checksum_sha256": checksum,
                "chunks_processed": chunks_processed if not dev else 0,
                "run_id": run_id,
                "trace_id": state.get("trace_id"),
                "dev_mode": dev,
            },
            t["ms"],
            warnings=["synthetic_data"] if dev else None,
        )