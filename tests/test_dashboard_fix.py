# =============================================================================
# scripts/test_dashboard_fix.py
# SIGMA — Prueba aislada de la corrección en _build_dashboard_plotly()
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Propósito: verificar los 3 arreglos (paleta fija, agrupamiento de idiomas,
# etiquetas reales en engagement) sin correr el pipeline completo. Reutiliza
# los datos ya existentes de una corrida anterior real.
# =============================================================================

import importlib.util
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# Carga el módulo directamente desde su ruta de archivo (el nombre de carpeta
# con guion no es un identificador Python válido para import normal).
SKILL_PATH = Path("skills/0011-viz-reporter/skill.py")
spec = importlib.util.spec_from_file_location("skill_0011", SKILL_PATH)
skill_0011 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skill_0011)

# La corrida de anoche, la que ya tiene datos reales de los 27,481 tweets.
TRACE_ID = "sigma-20260706-621f2fd6"

engine = create_engine(os.environ["DATABASE_URL"])
df = pd.read_sql(
    """
    SELECT sr.row_id, sr.sentiment, pd.engagement_score, pd.lang
    FROM sentiment_results sr
    JOIN processed_data pd ON sr.row_id = pd.row_id
    WHERE sr.trace_id = %(tid)s
    """,
    engine,
    params={"tid": TRACE_ID},
)

print(f"Filas leídas de la corrida real: {len(df)}")
print(f"Idiomas distintos encontrados: {df['lang'].nunique()}")

html, num_graphs = skill_0011._build_dashboard_plotly(df, pre_aggregated=False)

out_path = Path("test_dashboard_fix.html")
out_path.write_text(html, encoding="utf-8")
print(f"\nDashboard de prueba escrito en: {out_path.resolve()}")
print("Ábrelo en el navegador y verifica:")
print("  1. Colores de sentimiento consistentes (verde=positivo, rojo=negativo)")
print("  2. Idiomas agrupados en 'otros' si hay más de 5 categorías")
print("  3. El eje de 'Top engagement' muestra IDs reales, no 0..9")