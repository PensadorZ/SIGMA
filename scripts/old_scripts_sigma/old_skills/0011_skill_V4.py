# =============================================================================
# skills/0011-viz-reporter/skill.py
# SIGMA v1.5 · Eco MultiAgentes 3 Skills 1
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# NOTA v1.0.1: Reubicado desde skills/s0011_viz_reporter.py (flat) a esta carpeta,
#   siguiendo la convención ya establecida en Eco MultiAgentes 3 Skills 1:
#   'skill.py files in skills/000X-name/'. La resolución de import se
#   hace por ruta de archivo (importlib.util), no por paquete Python,
#   porque '000X-nombre-con-guion' no es un identificador válido.
# Implementación Python del skill 0011-viz-reporter.
# Ver skills/0011-viz-reporter/SKILL.md para el contrato completo.
#
# Selección autónoma de motor: plotly → duckdb+plotly → matplotlib
# Umbral DuckDB: 500 000 filas (ver defaults.yaml)
# Resumen textual: máximo 250 palabras + 5-8 palabras clave (K ⊆ X)
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

log = logging.getLogger("sigma.skills.0011")

SKILL_ID = "0011"
SKILL_DIR = "0011-viz-reporter"


class NoDataForVizError(Exception):
    pass


class SchemaValidationError(Exception):
    def __init__(self, expected: list[str], found: list[str]):
        self.expected = expected
        self.found = found
        super().__init__(f"Schema drift. Esperadas: {expected}. Encontradas: {found}.")


class AllEnginesUnavailableError(Exception):
    pass


# ---------------------------------------------------------------------------
# Lectura de datos
# ---------------------------------------------------------------------------

def _read_sentiment_data(state: PipelineState) -> pd.DataFrame:
    dev = is_dev_mode(state)
    if dev:
        import random
        labels = ["POSITIVE", "NEGATIVE", "NEUTRAL", "UNCLEAR"]
        langs = ["es", "en", "und"]
        rows = [
            {
                "row_id": f"dev-{uuid.uuid4().hex[:8]}",
                "sentiment": random.choices(labels, weights=[50, 25, 20, 5])[0],
                "engagement_score": round(random.uniform(0, 1), 3),
                "lang": random.choice(langs),
            }
            for _ in range(500)
        ]
        return pd.DataFrame(rows)

    conn = get_pg_connection(state)
    try:
        df = pd.read_sql(
            """
            SELECT sr.row_id, sr.sentiment, pd.engagement_score, pd.lang
            FROM sentiment_results sr
            JOIN processed_data pd ON sr.row_id = pd.row_id
            WHERE sr.trace_id = %s
            """,
            conn,
            params=(state["trace_id"],),
        )
    finally:
        conn.close()
    return df


# ---------------------------------------------------------------------------
# Selección autónoma de motor
# ---------------------------------------------------------------------------

def _select_engine(num_rows: int, threshold: int) -> tuple[str, list[str]]:
    warnings = []
    try:
        import plotly  # noqa: F401
        plotly_available = True
    except ImportError:
        plotly_available = False
        warnings.append("plotly_not_available")

    if plotly_available and num_rows > threshold:
        return "duckdb+plotly", warnings
    if plotly_available:
        return "plotly", warnings

    try:
        import matplotlib  # noqa: F401
        return "matplotlib", warnings
    except ImportError:
        raise AllEnginesUnavailableError(
            "Ni plotly ni matplotlib están disponibles en el entorno."
        )


# ---------------------------------------------------------------------------
# Generación del dashboard por motor
# ---------------------------------------------------------------------------

def _build_dashboard_plotly(df: pd.DataFrame, pre_aggregated: bool) -> tuple[str, int]:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    sentiment_counts = df["sentiment"].value_counts().reset_index()
    sentiment_counts.columns = ["sentiment", "count"]

    lang_counts = df["lang"].value_counts().reset_index()
    lang_counts.columns = ["lang", "count"]

    top_engagement = df.nlargest(min(10, len(df)), "engagement_score")

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Distribución de sentimiento", "Top engagement", "Distribución por idioma"),
        specs=[[{"type": "pie"}, {"type": "bar"}, {"type": "pie"}]],
    )
    fig.add_trace(go.Pie(labels=sentiment_counts["sentiment"], values=sentiment_counts["count"]), row=1, col=1)
    fig.add_trace(go.Bar(x=list(range(len(top_engagement))), y=top_engagement["engagement_score"]), row=1, col=2)
    fig.add_trace(go.Pie(labels=lang_counts["lang"], values=lang_counts["count"]), row=1, col=3)

    title_suffix = " (datos pre-agregados con DuckDB)" if pre_aggregated else ""
    fig.update_layout(title_text=f"SIGMA — Dashboard de sentimiento{title_suffix}", height=500)

    html = fig.to_html(full_html=True, include_plotlyjs="cdn")
    return html, 3


def _build_dashboard_matplotlib(df: pd.DataFrame) -> tuple[str, int]:
    import base64
    import io

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    df["sentiment"].value_counts().plot(kind="pie", ax=axes[0], title="Sentimiento")
    df.nlargest(min(10, len(df)), "engagement_score")["engagement_score"].plot(
        kind="bar", ax=axes[1], title="Top engagement"
    )
    df["lang"].value_counts().plot(kind="pie", ax=axes[2], title="Idioma")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    img_b64 = base64.b64encode(buf.read()).decode("utf-8")

    html = f"""<!DOCTYPE html>
<html><head><title>SIGMA — Dashboard (matplotlib fallback)</title></head>
<body>
<h1>SIGMA — Dashboard de sentimiento (fallback matplotlib)</h1>
<img src="data:image/png;base64,{img_b64}" />
</body></html>"""
    return html, 3


def _pre_aggregate_duckdb(df: pd.DataFrame) -> pd.DataFrame:
    import duckdb
    con = duckdb.connect(database=":memory:")
    con.register("sentiment_data", df)
    aggregated = con.execute(
        """
        SELECT sentiment, lang, AVG(engagement_score) AS engagement_score,
               COUNT(*) AS row_count
        FROM sentiment_data
        GROUP BY sentiment, lang
        """
    ).df()
    con.close()
    return aggregated


# ---------------------------------------------------------------------------
# Resumen textual (K ⊆ X, máx 250 palabras + 5-8 keywords)
# ---------------------------------------------------------------------------

EPISTEMIC_CONTRACT = """Eres un reportero de datos. Tienes acceso UNICAMENTE a los
siguientes datos observados: {stats_json}

REGLAS ABSOLUTAS:
1. Solo puedes afirmar hechos directamente presentes en los datos.
2. Tienes prohibido inferir causas, motivaciones o intenciones.
3. Tienes prohibido hacer recomendaciones no respaldadas por los datos.
4. Si un dato no esta presente, responde: DATOS_INSUFICIENTES.
5. Extension maxima: 250 palabras en prosa descriptiva sin bullets.
6. Al final incluye 5 a 8 palabras clave numeradas bajo 'Palabras clave:'.
"""


def _generate_summary(stats: dict, provider: str, cfg: dict) -> tuple[str | None, int, int]:
    if provider == "none":
        return None, 0, 0

    import json as _json
    prompt = EPISTEMIC_CONTRACT.format(stats_json=_json.dumps(stats, default=str))

    try:
        if provider == "ollama":
            import os
            import requests
            model = cfg.get("summary", {}).get("models", {}).get("ollama", "llama3.2:3b")
            ollama_host = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
            # Configurable vía defaults.yaml (summary.ollama_timeout_seconds).
            # Default subido de 30s a 90s -- 30s no alcanza para un arranque
            # en frío del modelo (confirmado con Read timed out real en
            # producción, 5 de julio de 2026).
            ollama_timeout = int(cfg.get("summary", {}).get("ollama_timeout_seconds", 90))
            resp = requests.post(
                f"{ollama_host}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=ollama_timeout,
            )
            text = resp.json().get("response", "").strip()
        elif provider == "gemini":
            # Implementación diferida — requiere GEMINI_API_KEY configurada.
            # Se deja como stub explícito para no bloquear el Hito 1.
            text = "DATOS_INSUFICIENTES"
        else:
            text = "DATOS_INSUFICIENTES"
    except Exception as exc:  # noqa: BLE001
        log.warning("[0011] Fallo generando resumen con provider=%s: %s", provider, exc)
        text = "DATOS_INSUFICIENTES"

    word_count = len(text.split())
    keywords_count = text.lower().count("palabras clave") and text.count("\n") or 0
    return text, word_count, keywords_count


# ---------------------------------------------------------------------------
# Persistencia del dashboard
# ---------------------------------------------------------------------------

def _persist_dashboard(html: str, trace_id: str, dev: bool) -> str:
    if dev:
        out_dir = Path("outputs/dashboards") / trace_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.html"
        out_path.write_text(html, encoding="utf-8")
        return str(out_path)

    import os
    from minio import Minio

    client = Minio(
        os.environ["MINIO_ENDPOINT"],
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=os.environ.get("MINIO_USE_SSL", "false").lower() == "true",
    )
    bucket = os.environ.get("MINIO_BUCKET_DASHBOARDS", "dashboards")
    object_name = f"{trace_id}/index.html"

    import io
    data = html.encode("utf-8")
    client.put_object(
        bucket, object_name, io.BytesIO(data), length=len(data),
        content_type="text/html",
    )
    return f"minio://{bucket}/{object_name}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(state: PipelineState) -> SkillResult:
    with timer() as t:
        dev = is_dev_mode(state)

        try:
            cfg = load_defaults(SKILL_DIR)
        except FileNotFoundError:
            cfg = {
                "visualization": {"large_dataset_threshold": 500000},
                "summary": {"provider": "none", "max_words": 250},
            }

        threshold = int(cfg.get("visualization", {}).get("large_dataset_threshold", 500000))
        summary_provider = cfg.get("summary", {}).get("provider", "none")

        # ── Lectura de datos ──────────────────────────────────────────────
        df = _read_sentiment_data(state)

        if df.empty:
            return make_error(
                SKILL_ID, "NoDataForVizError",
                "No hay datos de sentimiento/engagement para este trace_id.",
                t["ms"],
            )

        required_cols = {"sentiment", "engagement_score", "lang"}
        if not required_cols.issubset(df.columns):
            exc = SchemaValidationError(
                expected=list(required_cols), found=list(df.columns),
            )
            return make_error(SKILL_ID, "SchemaValidationError", str(exc), t["ms"])

        # ── Selección autónoma de motor ──────────────────────────────────
        try:
            engine, engine_warnings = _select_engine(len(df), threshold)
        except AllEnginesUnavailableError as exc:
            return make_error(SKILL_ID, "AllEnginesUnavailableError", str(exc), t["ms"])

        pre_aggregated = False

        # ── Generación del dashboard ─────────────────────────────────────
        if engine == "duckdb+plotly":
            agg_df = _pre_aggregate_duckdb(df)
            html, num_graphs = _build_dashboard_plotly(df, pre_aggregated=True)
            pre_aggregated = True
        elif engine == "plotly":
            html, num_graphs = _build_dashboard_plotly(df, pre_aggregated=False)
        else:  # matplotlib
            html, num_graphs = _build_dashboard_matplotlib(df)

        # ── Persistencia ──────────────────────────────────────────────────
        try:
            dashboard_url = _persist_dashboard(html, state["trace_id"], dev)
        except Exception as exc:  # noqa: BLE001
            return make_error(
                SKILL_ID, "MinIOConnectionError",
                f"No se pudo persistir el dashboard: {exc}", t["ms"],
            )

        # ── Resumen textual ───────────────────────────────────────────────
        stats = {
            "sentiment_distribution": df["sentiment"].value_counts().to_dict(),
            "lang_distribution": df["lang"].value_counts().to_dict(),
            "avg_engagement": round(float(df["engagement_score"].mean()), 3),
            "total_rows": len(df),
        }
        summary_text, word_count, keywords_count = _generate_summary(stats, summary_provider, cfg)

        warnings = list(engine_warnings)
        if dev:
            warnings.append("synthetic_data")

        return make_success(
            SKILL_ID,
            {
                "motor": engine,
                "dashboard_url": dashboard_url,
                "num_graficos": num_graphs,
                "pre_aggregated": pre_aggregated,
                "dev_mode": dev,
                "summary_text": summary_text,
                "summary_provider": summary_provider,
                "summary_length_chars": len(summary_text) if summary_text else None,
                "keywords_count": keywords_count if summary_text else None,
                "run_id": state.get("pipeline_run_id", state.get("trace_id")),
                "trace_id": state.get("trace_id"),
            },
            t["ms"],
            warnings=warnings if warnings else None,
        )
