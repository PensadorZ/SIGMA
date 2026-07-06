"""
Prueba con sslmode=disable y gssencmode=disable explicitos.

libpq (la biblioteca en C detras de psycopg2) puede intentar negociar
SSL o GSSAPI por defecto antes de caer a conexion simple. Si el servidor
no tiene SSL configurado, ese intento-y-rechazo puede tardar varios
segundos - y ese codigo vive dentro de libpq, no en Python, por eso
nuestras pruebas anteriores (socket crudo, getaddrinfo) nunca lo tocaron.

Uso: python test_postgres_sin_ssl.py
"""
import os
import time

from dotenv import load_dotenv
load_dotenv()

import psycopg2

dsn_original = os.environ["DATABASE_URL"]

print("=== Prueba 1: DSN original, tal como lo usa el pipeline ===")
t0 = time.monotonic()
try:
    conn = psycopg2.connect(dsn_original, connect_timeout=3)
    print(f"Conectado en {time.monotonic() - t0:.2f}s")
    conn.close()
except Exception as exc:
    print(f"FALLO en {time.monotonic() - t0:.2f}s -- {exc}")

print()
print("=== Prueba 2: mismo DSN + sslmode=disable + gssencmode=disable ===")
t0 = time.monotonic()
try:
    conn = psycopg2.connect(
        dsn_original,
        connect_timeout=3,
        sslmode="disable",
        gssencmode="disable",
    )
    print(f"Conectado en {time.monotonic() - t0:.2f}s")
    conn.close()
except Exception as exc:
    print(f"FALLO en {time.monotonic() - t0:.2f}s -- {exc}")
