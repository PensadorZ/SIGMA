"""
Script de aislamiento — reproduce la secuencia EXACTA de orchestrator.py:
1. Inicializar el cliente Langfuse (igual que orchestrator.py al importarse)
2. Emitir un evento (igual que node_start)
3. Inmediatamente después, intentar conectar a PostgreSQL (igual que check_postgres)

Si el paso 3 tarda ~4 segundos aquí (en vez de los 0.05s que ya confirmaste
en aislamiento total), confirma que Langfuse es el que interfiere.
Si sigue siendo instantáneo, el problema está en otra parte del código
que todavía no hemos aislado.

Uso: python test_aislamiento_langfuse_postgres.py
"""
import os
import time

from dotenv import load_dotenv
load_dotenv()

print("=== Paso 1: inicializando cliente Langfuse (igual que orchestrator.py) ===")
t0 = time.monotonic()
from langfuse import Langfuse
langfuse = Langfuse(
    public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
    secret_key=os.environ["LANGFUSE_SECRET_KEY"],
    host=os.environ.get("LANGFUSE_HOST", "http://127.0.0.1:3001"),
)
print(f"Cliente Langfuse inicializado en {time.monotonic() - t0:.2f}s")

print()
print("=== Paso 2: emitiendo evento (igual que node_start) ===")
t0 = time.monotonic()
try:
    langfuse.event(trace_id="test-aislamiento", name="test.event", metadata={"test": True})
except Exception as exc:
    print(f"(evento falló, esperado si no hay red — {exc})")
print(f"Llamada a langfuse.event() retornó en {time.monotonic() - t0:.2f}s")

print()
print("=== Paso 3: conectando a PostgreSQL INMEDIATAMENTE después ===")
import psycopg2
t0 = time.monotonic()
conn = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=3)
elapsed = time.monotonic() - t0
print(f"psycopg2.connect() tardó {elapsed:.2f}s")
conn.close()

print()
if elapsed > 1.0:
    print("⚠️  CONFIRMADO: Langfuse interfiere con la conexión posterior a PostgreSQL.")
else:
    print("✅ Postgres sigue siendo instantáneo — Langfuse NO es la causa. Hay que seguir buscando.")
