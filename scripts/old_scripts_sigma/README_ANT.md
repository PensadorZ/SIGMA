# README — Diagnóstico de conectividad PostgreSQL/Redis (4 de julio de 2026)

**Autor:** Prof. Marx Agustín García Delgado
**Proyecto:** SIGMA v1.6 — Hito 1
**Fecha del incidente:** 4 de julio de 2026

---

## Resumen

Durante la primera ejecución completa del pipeline del Hito 1 contra
infraestructura real (PostgreSQL, Redis, MinIO, Langfuse, Ollama en
Docker), el skill `0000-system-health-check` reportó de forma
consistente que PostgreSQL y Redis se encontraban caídos, pese a que
ambos contenedores figuraban como `healthy` en Docker y ambos
respondían correctamente a pruebas de conexión manuales.

El problema fue investigado de forma sistemática, descartando una
por una las causas más probables antes de llegar a la causa real. Este
documento deja constancia del proceso completo — no solo de la
solución — porque la investigación en sí es un ejemplo elocuente de
diagnóstico por eliminación metódica, y porque los ocho scripts
producidos durante el proceso siguen teniendo valor como herramientas
de diagnóstico de red para incidentes futuros.

Nota: Algo importante a tener en cuenta, es que, todo este desarrollo está hcho 
como vibecoding. Lo que fija el primer proyecto de esta naturaleza por los métodos
y comprensión que hay con vibecoding. 

---

## Síntoma observado

Al ejecutar `orchestrator.py`, el chequeo de PostgreSQL tardaba
sistemáticamente entre 4.0 y 4.4 segundos antes de reportar fallo, y el
de Redis entre 47.5 y 49.5 segundos — cifras notablemente consistentes
entre ejecuciones sucesivas, lo cual ya sugería una causa determinística
más que un problema de red genuinamente intermitente.

## Hipótesis descartadas, en el orden en que se investigaron

1. **Resolución IPv6 de `localhost` en Windows.** Se sustituyó
   `localhost` por `127.0.0.1` explícito en las tres URLs de conexión
   (`DATABASE_URL`, `REDIS_URL`, `LANGFUSE_HOST`). Los tiempos no
   cambiaron. Descartada.

2. **Variables de entorno no cargadas correctamente.** Se instrumentó
   el código para imprimir los valores reales vistos por el proceso en
   ejecución. Los valores resultaron ser exactamente los correctos.
   Descartada.

3. **Combinación de parámetros de `psycopg2` (`connect_timeout` +
   DSN completo).** Aislada en un script independiente
   (`test_postgres_sin_ssl.py`, primera prueba): conexión instantánea.
   Descartada.

4. **Interferencia del hilo de fondo del cliente Langfuse.** Se
   neutralizó por completo la emisión de eventos a Langfuse dentro del
   propio proceso del orquestador (`test_orchestrator_sin_langfuse.py`).
   Los tiempos no cambiaron. Descartada.

5. **Antivirus/Firewall de Windows interceptando el tráfico.** Se
   desactivó temporalmente el antivirus del equipo. Los tiempos no
   cambiaron. Descartada.

6. **Fallo de conectividad TCP real (Docker Desktop, backend WSL2).**
   Se probó con un socket crudo de Python (`test_socket_crudo.py`), sin
   ninguna biblioteca de terceros. Los cuatro puertos relevantes
   (`5433`, `6380`, `9002`, `3001`) conectaron en `0.00s`. Descartada.

7. **Resolución de direcciones (`getaddrinfo`) lenta.** Probada
   directamente con `AF_UNSPEC` y `AF_INET`
   (`test_getaddrinfo.py`). Ambas resolvieron instantáneamente.
   Descartada.

8. **Negociación SSL/GSSAPI de `libpq` con un servidor sin cifrado
   configurado.** Probada con `sslmode=disable` y `gssencmode=disable`
   explícitos (`test_postgres_sin_ssl.py`, segunda prueba). Ya la
   primera prueba, sin estos parámetros, resultó instantánea — la
   negociación de cifrado no era la causa.

9. **Construcción no óptima del cliente Redis (protocolo RESP3, pool
   de conexiones).** Probada con tres construcciones distintas
   (`test_redis_minimo.py`). Las tres, instantáneas. Descartada.

10. **Contención del hilo de fondo de `aiosqlite` (usado por el
    checkpointer `SqliteSaver` de LangGraph para HITL).** Se compiló el
    grafo sin ningún checkpointer (`test_orchestrator_sin_checkpointer.py`).
    Los tiempos no cambiaron. Descartada.

11. **Variables de entorno de LangSmith activando trazabilidad externa
    no deseada.** Verificado que ninguna variable
    `LANGCHAIN_*`/`LANGSMITH_*` estaba presente en el sistema. Descartada.

12. **Costo de primera carga de la extensión en C de `psycopg2` dentro
    de un proceso con muchas otras bibliotecas ya cargadas.** Probado
    llamando a la función de verificación dos veces seguidas en el
    mismo proceso ya "caliente" (`test_doble_llamada.py`). Ambas
    llamadas, igual de lentas. Descartada.

## Causa raíz

Ninguna de las doce hipótesis anteriores explicaba el síntoma porque
**el síntoma nunca fue de red**. El script `test_error_real.py` —que
imprimió por primera vez el texto exacto de la excepción capturada, en
vez de solo medir tiempos— reveló que la conexión se intentaba contra
`localhost`, puerto `5432` (PostgreSQL) y `6379` (Redis): **los puertos
por defecto de cada servicio, no los puertos reales configurados**
(`5433` y `6380`).

La causa fue que el archivo `skills/_common.py` instalado en el
proyecto no correspondía a la versión más reciente entregada durante
esta misma conversación —específicamente, carecía del soporte para
leer `DATABASE_URL` como fuente de conexión, y por lo tanto recurría
silenciosamente a los valores por defecto de los campos separados
(`POSTGRES_HOST`, `POSTGRES_PORT`). El tiempo de espera observado
(~4s y ~48s) correspondía al tiempo que Windows tarda en agotar los
reintentos de conexión contra un puerto sin nada escuchando —no un
problema de la aplicación, la red, ni la infraestructura.

## Resolución

Se reemplazó `skills/_common.py` por la versión correcta ya entregada
previamente en la conversación, que incluye el soporte para
`DATABASE_URL`/`REDIS_URL`. Verificado de inmediato con
`test_error_real.py`: ambos servicios pasaron a conectar en menos de
0.3 segundos, sin error.

## Decisión: `127.0.0.1` en lugar de `localhost`

Aunque la investigación descartó la resolución IPv6 como causa del
incidente, el autor decidió mantener `127.0.0.1` de forma permanente en
`DATABASE_URL`, `REDIS_URL` y `LANGFUSE_HOST`, por preferencia de
explicitud, no por necesidad técnica derivada de este incidente.

**Aclaración importante:** esta decisión no afecta en absoluto el
acceso a ningún puerto del proyecto —ni los ya usados (`5433`, `6380`,
`9002`, `3001`) ni los que se usarán más adelante (`8000` para
`webhook_receiver.py`, o cualquier otro). `127.0.0.1` y `localhost`
identifican exactamente la misma máquina —la diferencia es únicamente
si la dirección se escribe como texto a resolver o como número IP
directo. Ningún servicio, librería, ni configuración de Docker
distingue entre ambas formas para efectos de conectividad real.

## Archivos de esta carpeta

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
| `test_error_real.py` | Mensaje de excepción real —el que reveló la causa |

Estos scripts no se eliminan: quedan como registro del método de
diagnóstico aplicado y como herramientas reutilizables si un incidente
de conectividad similar se presenta en el futuro.

---

## Cierre — corrida completa exitosa, 5 de julio de 2026

Tras resolver este incidente y una serie de bugs adicionales encontrados
en el camino (contaminación del entorno conda con paquetes globales por
usuario, modelo RoBERTa incorrecto inicialmente descargado, escape de
rutas de Windows dentro de YAML, y un *bucket* de MinIO nunca creado),
**el pipeline completo del Hito 1 corrió de principio a fin contra
infraestructura Docker real y el dataset Tirendaz real**, con los 6
skills completados exitosamente:

```
0000-system-health-check   → success
0001-data-ingestion        → success
0002-data-cleanser         → success
0003-data-preprocessor     → success_with_warnings
0008-sentiment-analyzer    → success
0011-viz-reporter          → success
✓✓ Pipeline completado exitosamente
```

Esta corrida es la primera confirmación de que **SIGMA Hito 1 funciona
como sistema completo**, no solo como conjunto de pruebas unitarias
aisladas. Si sigues exactamente los pasos de configuración documentados
en `ESTRUCTURA_PROYECTO.md` y `requirements.txt` (incluyendo
`PYTHONNOUSERSITE=1`, el modelo RoBERTa correcto, y el bucket
`dashboards` de MinIO ya creado), el sistema corre de esta misma forma.
