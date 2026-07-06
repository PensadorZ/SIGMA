"""
Prueba definitiva #3 - importa TODO lo que orchestrator.py importa
(para calentar el proceso exactamente igual), y luego llama a
check_postgres()/check_redis() DOS VECES SEGUIDAS.

Si la PRIMERA llamada es lenta (~4s / ~49s) pero la SEGUNDA es
instantanea, confirma que es un costo de PRIMERA CARGA de la
extension C de psycopg2/redis-py dentro de un proceso ya cargado con
muchas otras bibliotecas (langgraph, langfuse, los 6 skills) - no un
problema de cada conexion individual.

Si AMBAS llamadas son igual de lentas, descarta tambien esta hipotesis.

Uso: python test_doble_llamada.py
"""
import time

from dotenv import load_dotenv
load_dotenv()

print("=== Calentando el proceso: importando orchestrator.py completo ===")
t0 = time.monotonic()
import orchestrator  # noqa: F401 -- esto carga TODO: langgraph, langfuse, los 6 skills
print(f"orchestrator.py importado completamente en {time.monotonic() - t0:.2f}s")
print()

from skills._common import check_postgres, check_redis

print("=== PostgreSQL: primera llamada ===")
t0 = time.monotonic()
r1 = check_postgres(timeout_seconds=3.0)
print(f"1ra llamada: {time.monotonic() - t0:.2f}s -- available={r1.available}")

print()
print("=== PostgreSQL: segunda llamada (proceso ya caliente) ===")
t0 = time.monotonic()
r2 = check_postgres(timeout_seconds=3.0)
print(f"2da llamada: {time.monotonic() - t0:.2f}s -- available={r2.available}")

print()
print("=== Redis: primera llamada ===")
t0 = time.monotonic()
r3 = check_redis(timeout_seconds=3.0)
print(f"1ra llamada: {time.monotonic() - t0:.2f}s -- available={r3.available}")

print()
print("=== Redis: segunda llamada (proceso ya caliente) ===")
t0 = time.monotonic()
r4 = check_redis(timeout_seconds=3.0)
print(f"2da llamada: {time.monotonic() - t0:.2f}s -- available={r4.available}")
