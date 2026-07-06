"""
skills/0001-data-ingestion/skill.py

Implementación real del skill 0001-data-ingestion.
Ver SKILL.md para la especificación completa.

ALCANCE DE ESTA VERSIÓN (honestidad deliberada, no overpromise):
la especificación original en SKILL.md describe seis fuentes
soportadas (csv, parquet, json, api, postgresql, gsheets). Esta
primera implementación cubre únicamente CSV, porque es la única
fuente que el Hito 1 (dataset Tirendaz) necesita. Las demás fuentes
quedan declaradas pero no implementadas, y el skill falla con un
error explícito y claro si se invoca con un `source` no soportado
todavía — nunca falla en silencio ni finge soportarlas.
"""

from __future__ import annotations

import csv
import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sigma.core import emit_trace_event, get_required_env

SUPPORTED_SOURCES = {"csv"}
NOT_YET_IMPLEMENTED_SOURCES = {"parquet", "json", "api", "postgresql", "gsheets"}


class SourceNotFoundError(FileNotFoundError):
    """La ruta de la fuente de datos no existe o no es legible."""


class EmptySourceError(ValueError):
    """La fuente existe pero no contiene ningún registro de datos."""


class SchemaValidationError(ValueError):
    """El schema de la fuente no coincide con el esperado por el proyecto."""


class UnsupportedSourceTypeError(NotImplementedError):
    """
    Se solicitó un tipo de fuente declarado en SKILL.md pero aún no
    implementado en código. Falla explícitamente en vez de fingir éxito.
    """


@dataclass
class IngestionResult:
    trace_id: str
    run_id: str
    output_table: str
    total_rows: int
    source_type: str
    source_path: str
    extraction_timestamp: str
    checksum_sha256: str
    columns_found: list[str]
    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "output_table": self.output_table,
            "total_rows": self.total_rows,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "extraction_timestamp": self.extraction_timestamp,
            "checksum_sha256": self.checksum_sha256,
            "columns_found": self.columns_found,
            "duration_ms": self.duration_ms,
        }


def _compute_checksum(path: Path) -> str:
    """Checksum SHA-256 real del archivo completo, leído en bloques."""
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _read_csv_rows(path: Path, encoding: str = "utf-8") -> tuple[list[str], list[dict[str, str]]]:
    """
    Lee un CSV completo en memoria. Para el Hito 1 (Tirendaz, ~22.500
    filas) esto es razonable; cargar en streaming/batches se añade
    cuando el dataset objetivo (WC2026, hasta 28M filas) lo requiera
    en la Fase 2 ampliada del Roadmap Técnico — no antes, para no
    construir paralelismo que nadie todavía necesita (YAGNI deliberado).
    """
    with path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        rows = list(reader)
    return list(columns), rows


def _validate_schema(found_columns: list[str], expected_columns: list[str] | None) -> None:
    """
    Valida que las columnas esperadas estén presentes. No exige
    coincidencia exacta (tolera columnas extra) salvo que falten
    columnas requeridas — ver SKILL.md, strict_schema en defaults.yaml
    para el comportamiento estricto, no implementado aún en esta versión.
    """
    if not expected_columns:
        return
    missing = [c for c in expected_columns if c not in found_columns]
    if missing:
        raise SchemaValidationError(
            f"Columnas esperadas ausentes: {missing}. "
            f"Columnas encontradas en la fuente: {found_columns}. "
            f"Columnas esperadas: {expected_columns}."
        )


def run_data_ingestion(
    source: str,
    path: str,
    run_id: str | None = None,
    trace_id: str | None = None,
    expected_columns: list[str] | None = None,
    encoding: str = "utf-8",
    output_table_name: str | None = None,
) -> IngestionResult:
    """
    Punto de entrada del skill. Implementa la trayectoria esperada de
    SKILL.md: validate_source_config -> connect_to_source ->
    sample_and_validate_schema -> load_in_batches -> compute_checksum
    -> write_raw_table -> register_source_metadata.

    Esta versión escribe el resultado como estructura en memoria
    (IngestionResult con columnas y row count) en vez de escribir
    literalmente en PostgreSQL — la integración real con
    `sigma.core.connections` para escritura de tablas se añade cuando
    0002-data-cleanser exista y necesite leer de una tabla real, no
    antes (de nuevo, YAGNI: no construir la tubería completa de
    PostgreSQL hasta que el siguiente eslabón de la cadena la consuma).
    Esto se documenta explícitamente como deuda técnica de esta versión.
    """
    start = time.monotonic()
    run_id = run_id or f"di-{uuid.uuid4().hex[:8]}"
    trace_id = trace_id or f"tr-{uuid.uuid4().hex[:8]}"

    emit_trace_event(
        "data_ingestion.started",
        trace_id=trace_id,
        run_id=run_id,
        source_type=source,
        source_path_or_url=path,
        expected_schema=expected_columns,
        sampling_method="full",
    )

    # ── validate_source_config ───────────────────────────────────────────
    if source in NOT_YET_IMPLEMENTED_SOURCES:
        emit_trace_event(
            "data_ingestion.failed",
            trace_id=trace_id,
            run_id=run_id,
            error_type="UnsupportedSourceTypeError",
            error_message=f"source='{source}' está declarado en SKILL.md pero no implementado aún.",
        )
        raise UnsupportedSourceTypeError(
            f"La fuente '{source}' está declarada en SKILL.md pero no tiene "
            f"implementación todavía en esta versión del skill. "
            f"Fuentes soportadas actualmente: {sorted(SUPPORTED_SOURCES)}."
        )
    if source not in SUPPORTED_SOURCES:
        raise UnsupportedSourceTypeError(
            f"Fuente desconocida '{source}'. Soportadas: {sorted(SUPPORTED_SOURCES)}."
        )

    # ── connect_to_source ─────────────────────────────────────────────────
    source_path = Path(path)
    if not source_path.exists() or not source_path.is_file():
        emit_trace_event(
            "data_ingestion.failed",
            trace_id=trace_id,
            run_id=run_id,
            error_type="SourceNotFoundError",
            error_message=f"No existe el archivo: {path}",
        )
        raise SourceNotFoundError(f"No se encontró el archivo fuente: {path}")

    # ── sample_and_validate_schema + load_in_batches (CSV completo) ──────
    columns, rows = _read_csv_rows(source_path, encoding=encoding)

    if not rows:
        emit_trace_event(
            "data_ingestion.failed",
            trace_id=trace_id,
            run_id=run_id,
            error_type="EmptySourceError",
            error_message="La fuente no contiene registros (solo cabecera o vacía).",
        )
        raise EmptySourceError(
            f"El archivo '{path}' existe pero no contiene ningún registro de datos."
        )

    try:
        _validate_schema(columns, expected_columns)
    except SchemaValidationError as exc:
        emit_trace_event(
            "data_ingestion.schema_error",
            trace_id=trace_id,
            run_id=run_id,
            expected_cols=expected_columns,
            found_cols=columns,
        )
        raise

    emit_trace_event(
        "data_ingestion.schema_validated",
        trace_id=trace_id,
        run_id=run_id,
        columns_found=columns,
        sample_rows_checked=len(rows),
    )

    # ── compute_checksum ──────────────────────────────────────────────────
    checksum = _compute_checksum(source_path)

    # ── write_raw_table (en memoria por ahora, ver docstring) ─────────────
    output_table = output_table_name or f"{source_path.stem}_raw"

    duration_ms = int((time.monotonic() - start) * 1000)

    result = IngestionResult(
        trace_id=trace_id,
        run_id=run_id,
        output_table=output_table,
        total_rows=len(rows),
        source_type=source,
        source_path=str(source_path),
        extraction_timestamp=datetime.now(timezone.utc).isoformat(),
        checksum_sha256=checksum,
        columns_found=columns,
        duration_ms=duration_ms,
    )

    # ── register_source_metadata (evento final) ───────────────────────────
    emit_trace_event(
        "data_ingestion.completed",
        trace_id=trace_id,
        run_id=run_id,
        output_table=output_table,
        total_rows=len(rows),
        checksum_sha256=checksum,
        duration_ms=duration_ms,
        source_registered_in_feature_store=False,  # Feature Store aún no implementado, ver Fase 4
    )

    return result


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Uso: python skill.py <ruta_al_csv> [columna1,columna2,...]")
        sys.exit(2)

    csv_path = sys.argv[1]
    expected = sys.argv[2].split(",") if len(sys.argv) > 2 else None

    try:
        result = run_data_ingestion(source="csv", path=csv_path, expected_columns=expected)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        sys.exit(0)
    except (SourceNotFoundError, EmptySourceError, SchemaValidationError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
