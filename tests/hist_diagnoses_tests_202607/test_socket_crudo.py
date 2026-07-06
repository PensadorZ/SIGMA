"""
Prueba de socket CRUDO — sin psycopg2, sin redis-py, sin ninguna
biblioteca de terceros. Solo el módulo socket incluido en Python.

Si esto TAMBIÉN es lento contra los puertos 5433/6380, confirma que el
problema no es de psycopg2 ni de redis-py en absoluto — es algo de cómo
Windows/Docker Desktop (probablemente el backend WSL2) reenvía esos
puertos específicos hacia el host, sin importar qué biblioteca los use.

Si esto es INSTANTÁNEO, el problema sigue siendo específico de
psycopg2/redis-py — habría que investigar sus opciones de socket
internas (TCP_NODELAY, keepalive, etc.).

Uso: python test_socket_crudo.py
"""
import socket
import time


def probar_puerto(nombre: str, host: str, port: int) -> None:
    t0 = time.monotonic()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        elapsed = time.monotonic() - t0
        print(f"{nombre:20s} ({host}:{port}) -> conectado en {elapsed:.2f}s")
        s.close()
    except Exception as exc:
        elapsed = time.monotonic() - t0
        print(f"{nombre:20s} ({host}:{port}) -> FALLO en {elapsed:.2f}s -- {exc}")


print("=== Prueba de socket crudo, sin librerias de terceros ===")
print()
probar_puerto("PostgreSQL", "127.0.0.1", 5433)
probar_puerto("Redis", "127.0.0.1", 6380)
probar_puerto("MinIO (control, rapido)", "127.0.0.1", 9002)
probar_puerto("Langfuse (control, rapido)", "127.0.0.1", 3001)
