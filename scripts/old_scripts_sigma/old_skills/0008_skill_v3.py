# =============================================================================
# skills/0008-sentiment-analyzer/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA v1.0.1: Reubicado desde skills/s0008_sentiment_analyzer.py (flat) a esta carpeta,
#   siguiendo la convención ya establecida en Eco MultiAgentes 3 Skills 1:
#   'skill.py files in skills/000X-name/'. La resolución de import se
#   hace por ruta de archivo (importlib.util), no por paquete Python,
#   porque '000X-nombre-con-guion' no es un identificador válido.
# Implementación Python del skill 0008-sentiment-analyzer.
# Ver skills/0008-sentiment-analyzer/SKILL.md para el contrato completo.
#
# Modelo: cardiffnlp/twitter-roberta-base-sentiment-latest (local, ~500 MB)
# Batch size: 32 (ver defaults.yaml — justificación de RAM en comentario)
# Umbral de confianza: 0.65 → por debajo, sentiment='UNCLEAR' (K ⊆ X)
# =============================================================================

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import pandas as pd

from core.pipeline_state import PipelineState, SkillResult
from skills._common import (
    get_pg_connection,
    is_dev_mode,
    load_defaults,
    make_error,
    make_success,
    timer,
)

log = logging.getLogger("sigma.skills.0008")

SKILL_ID = "0008"
SKILL_DIR = "0008-sentiment-analyzer"

# Valor histórico — YA NO SE USA directamente en run(), que ahora lee
# esto desde defaults.yaml (model.name). Se conserva como fallback si
# el archivo de configuración no está disponible.
MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
LABEL_MAP = {0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"}


class ModelNotFoundError(Exception):
    pass


class NoDataToAnalyzeError(Exception):
    pass


class SchemaValidationError(Exception):
    def __init__(self, expected: list[str], found: list[str]):
        self.expected = expected
        self.found = found
        missing = set(expected) - set(found)
        super().__init__(
            f"Schema drift detectado. Esperadas: {expected}. "
            f"Encontradas: {found}. Faltantes: {list(missing)}."
        )


def _read_processed_data(state: PipelineState) -> pd.DataFrame:
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
            {"row_id": f"dev-{uuid.uuid4().hex[:8]}", "clean_text": random.choice(samples)}
            for _ in range(500)
        ]
        return pd.DataFrame(rows)

    conn = get_pg_connection(state)
    try:
        df = pd.read_sql(
            "SELECT row_id, clean_text FROM processed_data WHERE trace_id = %s",
            conn,
            params=(state["trace_id"],),
        )
    finally:
        conn.close()
    return df


def _load_model(model_path: str, dev: bool):
    """
    Carga el modelo RoBERTa desde disco. En modo Dev usa un clasificador
    dummy determinista basado en palabras clave (sin descargar 500 MB).
    """
    if dev:
        return "DEV_DUMMY_CLASSIFIER"

    if not Path(model_path).exists():
        raise ModelNotFoundError(
            f"Modelo RoBERTa no encontrado en '{model_path}'. "
            f"Verifica ROBERTA_MODEL_PATH en tu .env."
        )

    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    return {"tokenizer": tokenizer, "model": model}


def _classify_batch_dev(texts: list[str]) -> list[tuple[str, float]]:
    """Clasificador dummy determinista para modo Dev — sin cómputo real."""
    results = []
    positive_words = {"increible", "partidazo", "amazing", "genial"}
    negative_words = {"decepcionante", "regular", "malo", "pesimo"}
    for text in texts:
        tokens = set(text.lower().split())
        if tokens & positive_words:
            results.append(("POSITIVE", 0.91))
        elif tokens & negative_words:
            results.append(("NEGATIVE", 0.88))
        else:
            results.append(("NEUTRAL", 0.70))
    return results


def _classify_batch_real(model_bundle: dict, texts: list[str], max_length: int) -> list[tuple[str, float]]:
    import torch
    import torch.nn.functional as F

    tokenizer = model_bundle["tokenizer"]
    model = model_bundle["model"]

    inputs = tokenizer(
        texts, return_tensors="pt", padding=True,
        truncation=True, max_length=max_length,
    )
    with torch.no_grad():
        logits = model(**inputs).logits
        probs = F.softmax(logits, dim=-1)

    results = []
    for row in probs:
        idx = int(row.argmax())
        confidence = float(row[idx])
        results.append((LABEL_MAP[idx], confidence))
    return results


def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)

        try:
            cfg = load_defaults(SKILL_DIR)
        except FileNotFoundError:
            cfg = {
                "model": {"path": ""},
                "inference": {"batch_size": 32},
                "confidence": {"threshold": 0.65, "unclear_label": "UNCLEAR"},
            }

        batch_size = int(cfg.get("inference", {}).get("batch_size", 32))
        threshold = float(cfg.get("confidence", {}).get("threshold", 0.65))
        model_path = cfg.get("model", {}).get("path", "")
        max_length = int(cfg.get("model", {}).get("max_length", 128))
        model_name = cfg.get("model", {}).get("name", MODEL_NAME)

        # ── Carga de datos ───────────────────────────────────────────────
        df = _read_processed_data(state)

        if df.empty:
            return make_error(
                SKILL_ID, "NoDataToAnalyzeError",
                "processed_data no contiene filas para este trace_id.",
                t["ms"],
            )

        if "clean_text" not in df.columns:
            exc = SchemaValidationError(
                expected=["row_id", "clean_text"], found=list(df.columns),
            )
            return make_error(SKILL_ID, "SchemaValidationError", str(exc), t["ms"])

        # ── Carga de modelo ──────────────────────────────────────────────
        try:
            model_bundle = _load_model(model_path, dev)
        except ModelNotFoundError as exc:
            return make_error(SKILL_ID, "ModelNotFoundError", str(exc), t["ms"])

        # ── Inferencia por batches ───────────────────────────────────────
        texts = df["clean_text"].fillna("").tolist()
        row_ids = df["row_id"].tolist()

        all_results: list[tuple[str, float]] = []
        batches_processed = 0

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            if dev:
                batch_results = _classify_batch_dev(batch_texts)
            else:
                batch_results = _classify_batch_real(model_bundle, batch_texts, max_length)
            all_results.extend(batch_results)
            batches_processed += 1

        # ── Aplicación del umbral UNCLEAR (K ⊆ X) ────────────────────────
        final_labels = []
        for label, confidence in all_results:
            if confidence < threshold:
                final_labels.append(("UNCLEAR", confidence))
            else:
                final_labels.append((label, confidence))

        num_unclear = sum(1 for lbl, _ in final_labels if lbl == "UNCLEAR")
        confidences = [c for _, c in final_labels]

        # ── Escritura ─────────────────────────────────────────────────────
        if not dev:
            conn = get_pg_connection(state)
            try:
                with conn.cursor() as cur:
                    for row_id, text, (label, confidence) in zip(row_ids, texts, final_labels):
                        cur.execute(
                            """
                            INSERT INTO sentiment_results
                                (row_id, clean_text, sentiment, confidence_score,
                                 model_name, trace_id, extra_metadata)
                            VALUES (%s, %s, %s, %s, %s, %s, NULL)
                            """,
                            (row_id, text, label, confidence, model_name, state["trace_id"]),
                        )
                conn.commit()
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                return make_error(
                    SKILL_ID, "PostgreSQLConnectionError",
                    f"Error al escribir en sentiment_results: {exc}", t["ms"],
                )
            finally:
                conn.close()

        pct_unclear = round(num_unclear / len(final_labels) * 100, 2)
        avg_confidence = round(sum(confidences) / len(confidences), 4)

        warnings = []
        if pct_unclear > 30.0:
            warnings.append("high_unclear_rate")
        if dev:
            warnings.append("synthetic_data")

        return make_success(
            SKILL_ID,
            {
                "num_classified": len(final_labels),
                "num_unclear": num_unclear,
                "pct_unclear": pct_unclear,
                "avg_confidence": avg_confidence,
                "min_confidence": round(min(confidences), 4),
                "max_confidence": round(max(confidences), 4),
                "batches_processed": batches_processed,
                "model_name": model_name if not dev else "DEV_DUMMY_CLASSIFIER",
                "run_id": state.get("pipeline_run_id", state.get("trace_id")),
                "trace_id": state.get("trace_id"),
                "dev_mode": dev,
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
