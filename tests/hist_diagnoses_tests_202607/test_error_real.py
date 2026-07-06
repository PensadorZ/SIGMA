"""
Diagnostico final - imprime el MENSAJE DE ERROR real, que nunca
habiamos visto hasta ahora (solo mediamos tiempos, nunca el texto de
la excepcion capturada). Tambien prueba con un timeout mucho mas
generoso (15s) para ver si eventualmente tiene exito o si falla de
forma genuina sin importar cuanto se espere.

Uso: python test_error_real.py
"""
import time

from dotenv import load_dotenv
load_dotenv()

print("=== Calentando el proceso: importando orchestrator.py completo ===")
import orchestrator  # noqa: F401
print("orchestrator.py importado.")
print()

from skills._common import check_postgres, check_redis

print("=== PostgreSQL: timeout=3s (igual que el pipeline real) ===")
r1 = check_postgres(timeout_seconds=3.0)
print(f"available={r1.available}")
print(f"latency_ms={r1.latency_ms}")
print(f"ERROR REAL: {r1.error}")

print()
print("=== PostgreSQL: timeout=15s (mucho mas generoso) ===")
t0 = time.monotonic()
r2 = check_postgres(timeout_seconds=15.0)
print(f"Tardo: {time.monotonic() - t0:.2f}s")
print(f"available={r2.available}")
print(f"ERROR REAL: {r2.error}")

print()
print("=== Redis: timeout=3s ===")
r3 = check_redis(timeout_seconds=3.0)
print(f"available={r3.available}")
print(f"ERROR REAL: {r3.error}")
