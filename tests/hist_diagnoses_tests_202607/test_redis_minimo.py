"""
Prueba de Redis con la construccion MAS SIMPLE posible del cliente,
sin from_url(), sin parametros extra de timeout, para aislar si el
retraso viene de algo especifico en como construimos la conexion.

Uso: python test_redis_minimo.py
"""
import time

import redis

print("=== Prueba 1: Redis() minimo, host/port directos, sin timeouts extra ===")
t0 = time.monotonic()
try:
    r = redis.Redis(host="127.0.0.1", port=6380)
    r.ping()
    print(f"Ping exitoso en {time.monotonic() - t0:.2f}s")
    r.close()
except Exception as exc:
    print(f"FALLO en {time.monotonic() - t0:.2f}s -- {exc}")

print()
print("=== Prueba 2: igual, pero con protocol=2 explicito (RESP2, sin HELLO/RESP3) ===")
t0 = time.monotonic()
try:
    r = redis.Redis(host="127.0.0.1", port=6380, protocol=2)
    r.ping()
    print(f"Ping exitoso en {time.monotonic() - t0:.2f}s")
    r.close()
except Exception as exc:
    print(f"FALLO en {time.monotonic() - t0:.2f}s -- {exc}")

print()
print("=== Prueba 3: single_connection_client=True, sin pool ===")
t0 = time.monotonic()
try:
    r = redis.Redis(host="127.0.0.1", port=6380, single_connection_client=True)
    r.ping()
    print(f"Ping exitoso en {time.monotonic() - t0:.2f}s")
    r.close()
except Exception as exc:
    print(f"FALLO en {time.monotonic() - t0:.2f}s -- {exc}")
