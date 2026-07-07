# =============================================================================
# scripts/test_langfuse_connection.py
# SIGMA — Prueba en caliente aislada de conectividad con Langfuse
# Autor: Prof. Marx Agustín García Delgado
# =============================================================================
# Propósito: confirmar que Langfuse recibe y persiste trazas, sin correr
# el pipeline completo. Envía una traza de prueba y la verifica de vuelta
# por API en el mismo script — no depende de que abras la UI manualmente.
# =============================================================================

import os
import time

import requests
from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv()

public_key = os.environ["LANGFUSE_PUBLIC_KEY"]
secret_key = os.environ["LANGFUSE_SECRET_KEY"]
host = os.environ.get("LANGFUSE_HOST", "http://127.0.0.1:3001")

print(f"Host: {host}")
print(f"Public key: {public_key[:15]}...")

# ── Paso 1: enviar una traza de prueba ──────────────────────────────────
langfuse = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

trace = langfuse.trace(
    name="sigma-test-conexion",
    metadata={"origen": "test_langfuse_connection.py", "proposito": "prueba en caliente"},
)
span = trace.span(name="test-span")
span.end()

print("\nTraza creada, forzando envío con flush()...")
langfuse.flush()
print("Flush completado.")

# ── Paso 2: esperar un momento y verificar por API que llegó ────────────
print("\nEsperando 3 segundos antes de verificar...")
time.sleep(3)

resp = requests.get(
    f"{host}/api/public/traces",
    params={"limit": 5},
    auth=(public_key, secret_key),
    timeout=10,
)

if resp.status_code != 200:
    print(f"\nERROR al consultar la API: {resp.status_code} — {resp.text[:300]}")
else:
    traces = resp.json().get("data", [])
    found = any(t.get("id") == trace.id for t in traces)
    print(f"\nTrazas recientes encontradas: {len(traces)}")
    if found:
        print(f"CONFIRMADO: la traza '{trace.id}' llegó a Langfuse correctamente.")
    else:
        print(f"ADVERTENCIA: la traza '{trace.id}' no aparece todavía.")
        print("Puede ser solo demora de indexación — revisa la UI en unos segundos.")