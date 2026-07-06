# =============================================================================
# skills/0001-data-ingestion/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA v1.0.1: Reubicado desde skills/s0001_data_ingestion.py (flat) a esta carpeta,
#   siguiendo la convención ya establecida en Eco MultiAgentes 3 Skills 1:
#   'skill.py files in skills/000X-name/'. La resolución de import se
#   hace por ruta de archivo (importlib.util), no por paquete Python,
#   porque '000X-nombre-con-guion' no es un identificador válido.
# Implementación Python del skill 0001-data-ingestion.
# Carga el CSV de entrada (Tirendaz u otro) y lo escribe en raw_data.
# K ⊆ X: no infiere ni completa columnas — copia exactamente lo observado.
# =============================================================================

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path

import pandas as pd

from core.pipeline_state import PipelineState, SkillResult
from skills._common import get_pg_connection, is_dev_mode, make_error, make_success, timer

log = logging.getLogger("sigma.skills.0001")

SKILL_ID = "0001"

# Columna mínima requerida en el CSV de entrada
REQUIRED_COLUMN = "text"


class SourceNotFoundError(Exception):
    pass


class EmptySourceError(Exception):
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
    rows = []
    for i in range(n):
        rows.append({
            "row_id": f"dev-{uuid.uuid4().hex[:8]}",
            "text": random.choice(samples_es),
        })
    return pd.DataFrame(rows)


def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)

        # ── Carga de datos ───────────────────────────────────────────────
        if dev:
            df = _generate_synthetic_rows(500)
        else:
            data_path = Path(state["data_path"])
            if not data_path.exists():
                return make_error(
                    SKILL_ID,
                    "SourceNotFoundError",
                    f"No se encontró el archivo de datos en '{data_path}'.",
                    t["ms"],
                )
            try:
                df = pd.read_csv(data_path)
            except Exception as exc:  # noqa: BLE001
                return make_error(
                    SKILL_ID,
                    "SourceNotFoundError",
                    f"Error al leer el CSV en '{data_path}': {exc}",
                    t["ms"],
                )

            if df.empty:
                return make_error(
                    SKILL_ID,
                    "EmptySourceError",
                    f"El archivo '{data_path}' no contiene filas.",
                    t["ms"],
                )

            if REQUIRED_COLUMN not in df.columns:
                return make_error(
                    SKILL_ID,
                    "SchemaValidationError",
                    f"Columna requerida '{REQUIRED_COLUMN}' no encontrada. "
                    f"Columnas presentes: {list(df.columns)}.",
                    t["ms"],
                )

            # Genera row_id si el dataset no lo trae
            if "row_id" not in df.columns:
                df["row_id"] = [f"row-{i}" for i in range(len(df))]

        num_records = len(df)

        # ── Escritura ─────────────────────────────────────────────────────
        if dev:
            # En Dev no se escribe en PostgreSQL real; queda en memoria
            # dentro del propio SkillResult para que 0002 lo pueda leer
            # (en esta implementación stub, downstream re-genera sintético
            # de forma independiente por simplicidad del Hito 1 en Dev).
            pass
        else:
            conn = get_pg_connection(state)
            try:
                with conn.cursor() as cur:
                    for _, row in df.iterrows():
                        metadata = {
                            k: v for k, v in row.items()
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
                    SKILL_ID,
                    "PostgreSQLConnectionError",
                    f"Error al escribir en raw_data: {exc}",
                    t["ms"],
                )
            finally:
                conn.close()

        return make_success(
            SKILL_ID,
            {
                "num_records": num_records,
                "source_path": str(state.get("data_path", "synthetic")),
                "dev_mode": dev,
            },
            t["ms"],
            warnings=["synthetic_data"] if dev else None,
        )
