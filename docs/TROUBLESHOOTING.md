---
id: TROUBLESHOOTING
titulo: Registro de Incidentes y Diagnósticos — SIGMA
version: 1.1
estado: Activo
fecha-original: 2026-07-04
fecha-revision: 2026-07-06
autor: Prof. Marx A. García Delgado
referencias-minimas: ADR-001, ADR-006, ADR-010
---

# Registro de Incidentes y Diagnósticos — SIGMA

Este documento reúne los problemas reales encontrados durante el desarrollo
y puesta en marcha de SIGMA, con su diagnóstico completo y la solución
exacta aplicada. Cada entrada nació de un incidente real, verificado con
evidencia — no de una suposición. Si el síntoma coincide, la causa casi
seguro es la misma.

**Protocolo de diagnóstico aplicado en todos los incidentes de este
documento:**

1. Verificar el contenido real en disco del archivo sospechoso
   (`findstr`/`grep` de una firma conocida) — no confiar en que "ya se
   entregó la versión correcta" sin comprobarlo.
2. Reproducir el síntoma exacto con el comando más simple posible antes
   de tocar código.
3. Un solo cambio a la vez entre cada verificación — evita mezclar
   variables y no saber cuál arregló (o rompió) qué.

---

## Incidente 1 — PostgreSQL y Redis "caídos" pese a estar sanos

**Fecha:** 4 de julio de 2026
**Severidad:** Alta — bloqueó la primera corrida completa del pipeline
**Estado:** Resuelto

### Síntoma

Durante la primera ejecución completa del pipeline del Hito 1 contra
infraestructura real (PostgreSQL, Redis, MinIO, Langfuse, Ollama en
Docker), el skill `0000-system-health-check` reportó de forma consistente
que PostgreSQL y Redis se encontraban caídos, pese a que ambos contenedores
figuraban como `healthy` en Docker y ambos respondían correctamente a
pruebas de conexión manuales.

El chequeo de PostgreSQL tardaba sistemáticamente entre 4.0 y 4.4 segundos
antes de reportar fallo, y el de Redis entre 47.5 y 49.5 segundos — cifras
notablemente consistentes entre ejecuciones sucesivas, lo cual ya sugería
una causa determinística más que un problema de red genuinamente
intermitente.

### Hipótesis descartadas, en el orden en que se investigaron

1. **Resolución IPv6 de `localhost` en Windows.** Se sustituyó `localhost`
   por `127.0.0.1` explícito en las tres URLs de conexión. Los tiempos no
   cambiaron. Descartada.
2. **Variables de entorno no cargadas correctamente.** Se instrumentó el
   código para imprimir los valores reales vistos por el proceso. Los
   valores resultaron ser exactamente los correctos. Descartada.
3. **Combinación de parámetros de `psycopg2`.** Aislada en un script
   independiente (`test_postgres_sin_ssl.py`): conexión instantánea.
   Descartada.
4. **Interferencia del hilo de fondo del cliente Langfuse.** Neutralizada
   por completo (`test_orchestrator_sin_langfuse.py`). Sin cambios.
   Descartada.
5. **Antivirus/Firewall de Windows.** Desactivado temporalmente. Sin
   cambios. Descartada.
6. **Fallo de conectividad TCP real (Docker Desktop, backend WSL2).**
   Probado con socket crudo de Python (`test_socket_crudo.py`). Los
   cuatro puertos relevantes conectaron en `0.00s`. Descartada.
7. **Resolución de direcciones (`getaddrinfo`) lenta.** Probada con
   `AF_UNSPEC` y `AF_INET` (`test_getaddrinfo.py`). Instantánea.
   Descartada.
8. **Negociación SSL/GSSAPI de `libpq`.** Probada con `sslmode=disable` y
   `gssencmode=disable` explícitos. Ya la primera prueba sin estos
   parámetros fue instantánea — no era la causa.
9. **Construcción no óptima del cliente Redis.** Probada con tres
   construcciones distintas (`test_redis_minimo.py`). Las tres,
   instantáneas. Descartada.
10. **Contención del hilo de fondo de `aiosqlite` (checkpointer de
    LangGraph).** Compilado el grafo sin ningún checkpointer. Sin
    cambios. Descartada.
11. **Variables de entorno de LangSmith activando trazabilidad externa.**
    Verificado que ninguna variable `LANGCHAIN_*`/`LANGSMITH_*` estaba
    presente. Descartada.
12. **Costo de primera carga de la extensión en C de `psycopg2`.** Probado
    con doble llamada en el mismo proceso "caliente"
    (`test_doble_llamada.py`). Ambas, igual de lentas. Descartada.

### Causa raíz

Ninguna de las doce hipótesis explicaba el síntoma porque **el síntoma
nunca fue de red**. El script `test_error_real.py` —que imprimió por
primera vez el texto exacto de la excepción, en vez de solo medir
tiempos— reveló que la conexión se intentaba contra `localhost`, puerto
`5432` (PostgreSQL) y `6379` (Redis): **los puertos por defecto de cada
servicio, no los puertos reales configurados** (`5433` y `6380`).

La causa fue que el archivo `skills/_common.py` instalado en el proyecto
no correspondía a la versión más reciente entregada durante esa misma
conversación — carecía del soporte para leer `DATABASE_URL`, y recurría
silenciosamente a los valores por defecto. El tiempo de espera observado
correspondía al tiempo que Windows tarda en agotar los reintentos contra
un puerto sin nada escuchando.

### Solución

Se reemplazó `skills/_common.py` por la versión correcta ya entregada
previamente, que incluye soporte para `DATABASE_URL`/`REDIS_URL`.
Verificado de inmediato: ambos servicios pasaron a conectar en menos de
0.3 segundos, sin error.

### Decisión permanente relacionada

Aunque la investigación descartó IPv6 como causa de este incidente
específico, se decidió mantener `127.0.0.1` de forma permanente en
`DATABASE_URL`, `REDIS_URL` y `LANGFUSE_HOST`, por preferencia de
explicitud, no por necesidad técnica derivada de este incidente.
`127.0.0.1` y `localhost` identifican la misma máquina — la diferencia es
únicamente textual, sin efecto sobre la conectividad real.

### Scripts de diagnóstico producidos (reutilizables)

| Script | Qué prueba |
|---|---|
| `test_socket_crudo.py` | Conectividad TCP pura, sin bibliotecas de terceros |
| `test_getaddrinfo.py` | Resolución de direcciones (`AF_UNSPEC`/`AF_INET`) |
| `test_postgres_sin_ssl.py` | Negociación SSL/GSSAPI de `libpq` |
| `test_redis_minimo.py` | Construcción mínima del cliente Redis |
| `test_aislamiento_langfuse_postgres.py` | Secuencia Langfuse → PostgreSQL aislada |
| `test_orchestrator_sin_langfuse.py` | Pipeline real con Langfuse neutralizado |
| `test_orchestrator_sin_checkpointer.py` | Pipeline real sin `SqliteSaver` |
| `test_doble_llamada.py` | Costo de primera carga vs. llamadas repetidas |
| `test_error_real.py` | Mensaje de excepción real — el que reveló la causa |

Ubicados en `scripts/diagnosticos_2026-07-04/`. No se eliminan: quedan como
registro del método aplicado y como herramientas reutilizables ante un
incidente similar.

### Cierre — corrida completa exitosa (5 de julio de 2026)

Tras resolver este incidente y una serie de bugs adicionales encontrados en
el camino (contaminación del entorno conda con paquetes globales,
modelo RoBERTa incorrecto inicialmente descargado, escape de rutas de
Windows dentro de YAML, y un bucket de MinIO nunca creado), el pipeline
completo del Hito 1 corrió de principio a fin contra infraestructura
Docker real y el dataset Tirendaz real:

```
0000-system-health-check   → success
0001-data-ingestion        → success
0002-data-cleanser         → success
0003-data-preprocessor     → success_with_warnings
0008-sentiment-analyzer    → success
0011-viz-reporter          → success
✓✓ Pipeline completado exitosamente
```

---

## Incidente 2 — `json.dumps()` rechaza valores NaN de pandas

**Fecha:** 5 de julio de 2026
**Severidad:** Media — bloqueaba `0001-data-ingestion` en filas con
columnas opcionales vacías
**Estado:** Resuelto

### Síntoma

```
PostgreSQLConnectionError — invalid input syntax for type json
DETAIL: Token "NaN" is invalid.
```

### Causa

Pandas convierte celdas vacías (ej. `selected_text` sin valor) en `NaN`
(float especial de NumPy). `json.dumps()` serializa `NaN` como el token
literal `NaN`, que **no es JSON válido** según RFC 8259 — PostgreSQL lo
rechaza. El parámetro `default=str` de `json.dumps()` no ayuda aquí porque
solo se activa con tipos no serializables, y `NaN` técnicamente sí lo es
(solo que produce JSON inválido).

### Solución

Sanear cada valor con `pd.isna()` antes de construir el diccionario, en
`skills/0001-data-ingestion/skill.py`:

```python
metadata = {
    k: (None if pd.isna(v) else v)
    for k, v in row.items()
    if k not in ("row_id", "text")
}
```

`None` de Python sí serializa correctamente como `null`, válido para
PostgreSQL.

---

## Incidente 3 — Langfuse marca `unhealthy` pese a funcionar bien

**Fecha:** 6 de julio de 2026
**Severidad:** Baja (cosmética) — no afecta funcionalidad real
**Estado:** Resuelto

### Síntoma

`docker ps` muestra `sigma_langfuse` como `(unhealthy)` indefinidamente,
pero `http://localhost:3001` carga y funciona con normalidad, y las
trazas del pipeline sí llegan (confirmado con `test_langfuse_connection.py`
enviando y verificando una traza real por API).

### Por qué no es grave

El estado `healthy`/`unhealthy` es una etiqueta que Docker usa solo para
decisiones de orquestación (ej. si otro contenedor con
`depends_on: condition: service_healthy` debe esperar). No tiene ningún
efecto sobre si la aplicación recibe y guarda datos correctamente.

### Causas reales encontradas (tres, acumuladas en la misma investigación)

1. **`curl` no existe en la imagen.** La imagen `ghcr.io/langfuse/langfuse:2`
   no incluye el binario `curl` — el healthcheck original fallaba con
   `executable file not found in $PATH`. Solución parcial: usar `wget`
   (sí está presente, BusyBox 1.36.1).

2. **`wget` resolvía `localhost` a IPv6 (`::1`).** Dentro del contenedor,
   la conexión por esa vía era rechazada. Se probó forzar `127.0.0.1`
   explícitamente — mejoró el diagnóstico pero no resolvió el problema de
   fondo (ver causa 3).

3. **Causa raíz real: el servidor no escucha en ninguna interfaz de
   loopback** (ni `127.0.0.1` ni `::1`) dentro del contenedor — solo en la
   IP de red que Docker le asigna dinámicamente. Confirmado con:
   ```
   docker exec sigma_langfuse hostname -i
   docker exec sigma_langfuse wget --spider http://<esa_ip>:3000/api/public/health
   ```
   Esa IP respondió `remote file exists`, mientras que `127.0.0.1` daba
   `Connection refused`.

### Solución final

Resolver la IP del contenedor dinámicamente dentro del propio healthcheck,
nunca hardcodearla:

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://$(hostname -i):3000/api/public/health || exit 1"]
  interval: 10s
  timeout: 5s
  retries: 10
  start_period: 30s
```

### Nota de diseño — alineación con ADR-006

Se descartó deliberadamente hardcodear la IP observada (`172.18.0.2`)
directamente en el healthcheck. Docker puede reasignar esa dirección en
cualquier recreación futura del contenedor, y un valor fijo habría vuelto
a romperse en silencio más adelante — el mismo problema de portabilidad
entre entornos que ADR-006 previene mediante resolución dinámica en vez de
valores fijos. `$(hostname -i)` resuelve la IP correcta en cada arranque,
sin importar cuál sea.

---

## Incidente 4 — Zulip: escribir en el topic no dispara el webhook

**Fecha:** 6 de julio de 2026
**Severidad:** Alta — bloqueaba por completo la aprobación HITL vía Zulip
**Estado:** Resuelto

### Síntoma

Responder "sí"/"no" en el topic `hitl-approvals` nunca activa el
Outgoing webhook, sin ningún error visible en ningún lado.

### Causa

Según la documentación oficial de Zulip, un Outgoing webhook **solo se
dispara por `@-mención` del bot o por mensaje directo (DM)** — nunca por
un mensaje plano en un stream/topic, aunque el bot esté suscrito a él.

### Solución adoptada

Las respuestas HITL se envían por DM al bot, no en el canal. Ver
`webhook_receiver.py`, validación `message.get("type") == "private"`.

---

## Incidente 5 — `sender_email` de Zulip no coincide con el correo real

**Fecha:** 6 de julio de 2026
**Severidad:** Media
**Estado:** Resuelto

### Síntoma

El webhook rechaza los DMs con `sender_not_authorized`, aunque el
remitente sea el operador legítimo.

### Causa

Zulip puede enmascarar el correo del remitente en el payload (formato
`userNNNNN@dominio`) según su configuración de privacidad
(`email_address_visibility`), sin relación con el correo real configurado
en `ZULIP_EMAIL`.

### Solución

Validar por `sender_id` (estable, siempre visible en el payload) en vez de
`sender_email`. Variable nueva en `.env`: `ZULIP_OWNER_USER_ID`.

---

## Comportamientos normales que parecen errores (pero no lo son)

### "¿Necesito Zulip/webhook corriendo antes de lanzar el pipeline?"

**No.** El pipeline puede pausarse en un punto HITL, y el proceso que lo
reanuda (`webhook_receiver.py`) puede arrancar completamente después. El
estado vive en `sigma_checkpoints.sqlite` en disco, no en memoria
compartida — si el pipeline llega a una pausa antes de que
`uvicorn`/`ngrok` estén listos, simplemente espera ahí indefinidamente.

### "La URL de ngrok cambia cada vez que lo reinicio"

Es el comportamiento esperado del plan gratuito de ngrok — asigna una URL
nueva en cada reinicio del túnel. Hay que actualizar manualmente el
"Endpoint URL" del bot en Zulip cada vez. Solución permanente: migrar a un
VPS con IP/dominio fijo (planeado a partir del Hito 2).

### "Kaggle me dio un token con formato raro (`KGAT_...`)"

No es el `kaggle.json` clásico — es un token de acceso personal nuevo.
Configurar como variable de entorno:
```cmd
set KAGGLE_API_TOKEN=KGAT_tu_token_completo
```
o en `%USERPROFILE%\.kaggle\access_token`.

### "Una tabla Markdown que pegué se ve rota, cada celda en su línea"

No es un problema de renderizado ni de Markdown en sí. Ocurre cuando el
texto se copia desde un entorno que reformatea las celdas de una tabla en
líneas separadas al copiar (pierde el formato de fila única separada por
`|`). Solución: volver a pegar el Markdown fuente original, en una sola
línea por fila — así se renderiza correctamente en GitHub o cualquier
visor de Markdown estándar.
