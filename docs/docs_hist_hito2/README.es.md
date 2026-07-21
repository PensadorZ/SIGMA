# SIGMA — Sistema Integrado para la Gestión Multiagente


![alt text](assets/sigma_banner.png)


![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-65%2F65%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Hito](https://img.shields.io/badge/Hito%202-Rollout%201%20completo-success)
[![ORCID](https://img.shields.io/badge/ORCID-0009--0003--4849--3369-a6ce39?logo=orcid&logoColor=white)](https://orcid.org/0009-0003-4849-3369)

> **SIGMA no es una respuesta. Es el sistema que aprende a responder.**

🇬🇧 [English version available here](README.md)

---

SIGMA es un ecosistema de agentes autónomos de código abierto para
analizar, diseñar, calcular y decidir, construido mediante una
metodología de desarrollo asistido por IA (*vibecoding*) y documentado
desde su arquitectura hasta la resolución real de incidentes en
producción.

Múltiples agentes especializados colaboran bajo una arquitectura de
orquestación central triangular — Director/Auditor/Engineer, tres
orquestadores (ver ADR-016) — para abordar proyectos en Ingeniería de
Datos, Data Science, Análisis de Datos, Ingeniería General, Física,
Matemática y Axiometría.

## ✅ Verificado localmente

El pipeline completo del Hito 1 corrió de extremo a extremo contra
infraestructura Docker real y el dataset Tirendaz real (27.481 tweets):

```
0000-system-health-check   → success
0001-data-ingestion        → success
0002-data-cleanser         → success
0003-data-preprocessor     → success_with_warnings
0008-sentiment-analyzer    → success
0011-viz-reporter          → success
✓✓ Pipeline completado exitosamente
```

Suite de pruebas completa:

```
================================ 65 passed, 36 warnings in 20.80s ================================
```

> **Nota sobre la cobertura de pruebas:** los 65 tests incluyen tanto
> pruebas unitarias completamente aisladas (con conectores simulados
> para PostgreSQL/Redis) como pruebas de integración contra
> infraestructura real. La evidencia más fuerte de corrección de
> extremo a extremo no es el conteo de tests en sí, sino la corrida
> completa del pipeline contra infraestructura Docker real mostrada
> arriba (`warnings=[]`, los 6 skills en `status=success`).

**El Hito 2, Rollout 1 (orquestación jerárquica, ADR-016) ya está
completo** — verificado contra las 4 condiciones de salida: suite
pytest-bdd completa en verde (65/65, incluyendo
`0004-statistical-validator`), 4+ corridas reales consecutivas sin
fallo, circuit breaker verificado con un fallo no recuperable forzado
(cero reintentos, fallo rápido confirmado), y traza Langfuse completa
verificada de extremo a extremo (trace padre + eventos hijos,
confirmado directamente contra la base de datos). Ver
[docs/adr/adr-016-orquestacion-jerarquica.md](docs/adr/adr-016-orquestacion-jerarquica.md)
para el plan completo de Rollouts.

### 📊 Ejemplos de dashboards reales

Los siguientes dashboards fueron generados por el pipeline real de
SIGMA (`0011-viz-reporter`), no simulados ni armados a mano:

**Tirendaz — corrida post-reestructuración** (línea base, `warnings=[]`)
![Dashboard de Tirendaz](assets/dashboard_screenshots/dashboard_run4_tirendaz.png)

**Reseñas de IMDb — prueba cross-domain** (texto largo, `warnings=[]`)
![Dashboard de IMDb](assets/dashboard_screenshots/dashboard_run5_imdb.png)

**Redes sociales 2026 — prueba cross-domain** (activó correctamente el disparador de calidad HITL)
![Dashboard de redes sociales](assets/dashboard_screenshots/dashboard_run6_social.png)

Dashboards interactivos completos: [`outputs/`](outputs/) (descarga y
abre localmente — GitHub muestra el código HTML crudo, no la página
renderizada). Metodología y hallazgos completos: [`output_report.md`](outputs/output_report.md)

## ✨ Características

- 🧠 **Memoria epistémica** — Feature Store temporal + Grafo de Suposiciones que separa hechos verificados de hipótesis refutables ([ADR-001](docs/adr/adr-001-memoria-epistemica.md))
- 🔒 **Contención epistémica K ⊆ X** — ningún agente puede afirmar algo que no provenga de un dato observado ([ADR-008](docs/adr/adr-008-restriccion-epistemica.md))
- 🛡️ **Seguridad automática Red/Blue/Green** — pre-vuelo adversarial, monitoreo AgBOM en tiempo real, y recuperación auditada ([ADR-003](docs/adr/adr-003-equipo-3-colores.md))
- ✅ **Aprobación humana con Vibe Diff** — cadena de custodia persistente en MinIO antes de cualquier acción de impacto medio o alto ([ADR-004](docs/adr/adr-004-vibe-diff-mfa.md))
- 📊 **Evaluación en 7 dimensiones** — intención, corrección, coste, calidad de código, trayectoria y autoreparación, no solo "pasa los tests" ([ADR-007](docs/adr/adr-007-evaluacion-multidimensional.md))
- 🔍 **Trazabilidad completa en Langfuse V2** — cada decisión, cada llamada a herramienta, con degradación elegante si Langfuse cae ([ADR-011](docs/adr/adr-011-trazabilidad-langfuse.md))
- 🐳 **100% autoalojable en su variante gratuita** — SIGMA-FE corre completo en tu propia máquina, sin depender de ningún servicio de pago
- 🔀 **4 escalones de costo** — de SIGMA-FE ($0) a SIGMA-HE (alto desempeño), cada uno operable en submodo Dev o Runtime
- 🌳 **Orquestación jerárquica** — un Director coordina Engineers especializados (Datos, Modelos, Auditor), construidos por Rollouts verificados, no todos a la vez ([ADR-016](docs/adr/adr-016-orquestacion-jerarquica.md))

---

## Por qué SIGMA es distinto

La mayoría de proyectos de agentes construyen primero una funcionalidad
vistosa y añaden gobernanza después, si acaso. SIGMA se construyó al
revés, deliberadamente: memoria epistémica, seguridad automática,
gestión de secretos y contención de alucinaciones (`K ⊆ X`) existieron
**antes** de que hubiera un solo dashboard que mostrar. Cada decisión
arquitectónica está respaldada por un Architecture Decision Record (ADR)
explícito — 16 hasta la fecha — no por convención tácita.

## Escalones de costo

SIGMA se adapta a cuatro niveles de presupuesto, del mismo stack
arquitectónico:

| Variante | Costo | Para quién |
|---|---|---|
| **SIGMA-FE** (Full Engineer) | $0 | Ingeniería propia, stack 100% autoalojado |
| **SIGMA-LE** (Low-Cost Engineer) | Bajo | Servicios premontados esenciales |
| **SIGMA-ME** (Medium-Cost Engineer) | ~50% pago | Equipos con presupuesto moderado |
| **SIGMA-HE** (High-Cost Engineer) | Alto | Empresas que requieren alto desempeño |

Cada variante puede además operar en submodo **Dev** (depuración) o
**Runtime** (producción con datos reales) — un eje completamente
independiente del costo, ej. `--variant SIGMA-FE --submode Dev`. Detalle
completo en [SIGMA_v1.7.md](docs/SIGMA_v1.7.md).

## Requisitos previos

- Docker y Docker Compose
- Python 3.12+
- [Ngrok](https://ngrok.com/download) — expone el webhook HITL local a
  Zulip durante el desarrollo (no es un paquete Python, se instala y
  ejecuta por separado)
- Cuenta de Kaggle con token API (formato KGAT) — para descargar el
  dataset de entrenamiento

## Empezar

```bash
git clone https://github.com/PensadorZ/SIGMA.git
cd SIGMA
cp .env.example .env
# Edita .env con tus valores reales
docker compose up -d

# Prueba rápida — datos sintéticos generados internamente, sin
# dependencia de infraestructura real, iteración rápida:
python director_main.py --variant SIGMA-FE --submode Dev --data-path ./data/tirendaz.csv

# Corrida completa — dataset real Tirendaz (27.481 tweets etiquetados)
# contra infraestructura Docker real (PostgreSQL, Redis, MinIO, Langfuse):
python director_main.py --variant SIGMA-FE --submode Runtime --data-path ./data/tirendaz.csv
```

### 🩹 Si el pipeline no corre — diagnóstico de Docker

El bloqueo más común no es el código, es que Docker no está arriba.
Antes que cualquier otra cosa:

```bash
# 1. Confirma que la aplicación Docker Desktop esté abierta y
#    completamente iniciada (el ícono de la bandeja del sistema deja
#    de animarse cuando el motor ya está listo).

# 2. Verifica qué contenedores existen y en qué estado están:
docker ps -a

# 3. Si aparecen como "Exited" (postgres, langfuse_db, redis, minio,
#    langfuse), arráncalos directamente -- no los recrees:
docker start sigma_postgres sigma_langfuse_db sigma_redis sigma_minio sigma_langfuse

# 4. Confirma que los 5 quedaron "Up (healthy)" -- dale 10-15 segundos,
#    especialmente a Postgres y Langfuse:
docker ps

# 5. Solo si los contenedores no existen en absoluto (clon nuevo, o
#    Docker Desktop reinstalado), recréalos:
docker compose up -d
```

Guía completa, paso a paso, en [ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md).

## Documentación

| Documento | Qué encontrarás ahí |
|---|---|
| [SIGMA_v1.7.md](docs/SIGMA_v1.7.md) | Plan Maestro completo — arquitectura, variantes, roadmap |
| [AGENTS_CREATOR.md](docs/AGENTS_CREATOR.md) | Acta fundacional — contrato de todos los agentes |
| [docs/adr/](docs/adr/) | 16 Architecture Decision Records |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Incidentes reales del Hito 1 y su solución exacta |
| [TROUBLESHOOTING_HITO2.md](docs/TROUBLESHOOTING_HITO2.md) | Incidentes reales de Hito 2 en adelante |


## 🏗️ Arquitectura

```
sigma-hito2/
├── director_main.py         # Punto de entrada -- reemplaza a orchestrator.py (Hito 1, archivado)
├── webhook_receiver.py      # Recibe respuestas HITL desde Zulip
├── sigma/                   # Paquete Python instalable
│   ├── core/                # Config, conexiones, tracing, checkpointer, estado,
│   │                         director.py, engineer_datos.py, skill_runner.py
│   ├── hooks/                # Notificaciones Zulip
│   └── skills/                # Los 7 skills de Engineer Datos, cada uno con:
│       └── 000X-nombre/        SKILL.md, skill.py, defaults.yaml,
│                                references/, evals/, tests/
├── db/                      # Esquema PostgreSQL (7 tablas)
├── docs/
│   ├── SIGMA_v1.7.md         # Documento fundacional del Arnés
│   ├── AGENTS_CREATOR.md    # Contrato de gobernanza de agentes
│   └── adr/                  # 16 Architecture Decision Records
└── tests/                   # Suite compartida (65/65 pasando)
```

Ver [ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md) para el árbol
completo y el detalle de cada carpeta.

## ⚠️ Limitaciones conocidas

Con la misma disciplina de gobernanza que define a SIGMA, estas son las
brechas reales del estado actual — sin maquillaje:

- **`INSTALL.md` y `PIPELINES.md` no existen todavía.** La guía de
  instalación paso a paso vive por ahora en
  [ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md).
- **Ngrok requiere arranque manual en dos terminales.** El flujo HITL
  vía Zulip necesita `uvicorn` + `ngrok` corriendo antes de lanzar el
  pipeline — no hay automatización de arranque todavía. Gracias al Dev
  Domain gratuito de Ngrok (desde enero de 2026), la URL se mantiene
  fija entre reinicios, pero el arranque en sí sigue siendo manual.
- **Sin CI configurado.** Los 65/65 tests se verifican localmente; no
  hay GitHub Actions corriendo la suite en cada push todavía.
- **Bug de autorreporte de `duration_ms` en dos skills, mitigado, sin
  causa raíz confirmada.** `0003-data-preprocessor` y `0011-viz-reporter`
  autorreportan `0ms` sin importar el tiempo real transcurrido;
  `skill_runner.py` ahora mide su propio reloj real de forma
  independiente y ya no confía en el valor autorreportado, así que esto
  no afecta la corrección — pero el bug real dentro de esos dos skills
  todavía no se ha diagnosticado.
- **El bot de Zulip solo reacciona a mensajes directos, nunca a
  mensajes de canal/topic** — comportamiento propio de la plataforma
  Zulip (los Outgoing webhooks solo se disparan por DM o @-mención), no
  una limitación de SIGMA. Ver `TROUBLESHOOTING.md`, Incidente 4.
  Además, una vez configurada la URL del webhook de un bot, **Zulip no
  permite editarla desde la interfaz** — crear un bot nuevo es la única
  forma de apuntar a un endpoint distinto.
- **Cuenta del bot de Zulip desactivada intermitentemente** — causa
  todavía no diagnosticada; el pipeline no falla por esto (degradación
  elegante ya verificada, ADR-011), pero las notificaciones no llegan
  mientras la cuenta esté inactiva.

Ninguna de estas brechas bloquea el uso del pipeline tal como está
documentado.

## Estado del proyecto

Hito 1 completado: pipeline de 6 skills corriendo de extremo a extremo
contra datos reales, con 65/65 pruebas automatizadas pasando. La salida
del pipeline vive en MinIO — el producto terminado debe buscarse dentro
del dashboard generado ahí.

**Hito 2 — Rollout 1 completo** (Director + Engineer Datos,
`0000-0004, 0008, 0011`, ADR-016): arquitectura jerárquica de tres
orquestadores (Director/Engineer Datos/Engineer Modelos/Engineer
Auditor), construida por fases verificadas. Las 4 condiciones de salida
cumplidas — suite completa en verde, múltiples corridas reales
consecutivas, circuit breaker verificado con fallo forzado, y
trazabilidad Langfuse confirmada de extremo a extremo. Esquema de
variantes de costo migrado a `SIGMA-FE/LE/ME/HE` + submodo `Dev/Runtime`
independiente en todo el código de Rollout 1.

Siguen Rollout 2 (Engineer Modelos: `0005-0007, 0009-0010`) y Rollout 3
(Engineer Auditor: `0012-0015`, condicionado al sandboxing de ADR-017).

## Licencia

[MIT](LICENSE)

---

<p align="center">
Hecho con 🧠 y gobernanza disciplinada por
<a href="https://orcid.org/0009-0003-4849-3369">Prof. Marx Agustín García Delgado</a>
</p>
