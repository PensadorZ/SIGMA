"""
Prueba de getaddrinfo() — el paso de resolución de direcciones que
psycopg2/redis-py probablemente SÍ ejecutan internamente (con AF_UNSPEC,
permitiendo IPv4 e IPv6), y que mi prueba de socket crudo anterior evitó
por completo al usar AF_INET explícito.

Si getaddrinfo() con AF_UNSPEC es lento aquí, encontramos la causa real:
no es la conexión TCP, es la resolución de direcciones previa a ella.

Uso: python test_getaddrinfo.py
"""
import socket
import time


def probar_resolucion(nombre: str, host: str, port: int, family) -> None:
    t0 = time.monotonic()
    try:
        resultado = socket.getaddrinfo(host, port, family, socket.SOCK_STREAM)
        elapsed = time.monotonic() - t0
        print(f"{nombre:30s} -> resuelto en {elapsed:.2f}s -> {resultado[0][4]}")
    except Exception as exc:
        elapsed = time.monotonic() - t0
        print(f"{nombre:30s} -> FALLO en {elapsed:.2f}s -- {exc}")


print("=== getaddrinfo() con AF_UNSPEC (IPv4 + IPv6, lo que las librerias probablemente usan) ===")
print()
probar_resolucion("PostgreSQL (AF_UNSPEC)", "127.0.0.1", 5433, socket.AF_UNSPEC)
probar_resolucion("Redis (AF_UNSPEC)", "127.0.0.1", 6380, socket.AF_UNSPEC)
probar_resolucion("MinIO (AF_UNSPEC, control)", "127.0.0.1", 9002, socket.AF_UNSPEC)

print()
print("=== getaddrinfo() con AF_INET explicito (solo IPv4, para comparar) ===")
print()
probar_resolucion("PostgreSQL (AF_INET)", "127.0.0.1", 5433, socket.AF_INET)
probar_resolucion("Redis (AF_INET)", "127.0.0.1", 6380, socket.AF_INET)
