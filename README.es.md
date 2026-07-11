# SIGMA — Sistema Integrado para la Gestión Multiagente


![alt text](assets/sigma_banner.png)


![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-65%2F65%20passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Hito](https://img.shields.io/badge/Hito%201-Completo-success)
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
**Runtime** (producción con datos reales). Detalle completo en
[SIGMA_v1.7.md](SIGMA_v1.7.md).

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
python orchestrator.py --variant Dev --data-path ./data/tirendaz.csv

# Corrida completa — dataset real Tirendaz (27.481 tweets etiquetados)
# contra infraestructura Docker real (PostgreSQL, Redis, MinIO, Langfuse):
python orchestrator.py --variant Full --data-path ./data/tirendaz.csv
```

Guía completa, paso a paso, en [ESTRUCTURA_PROYECTO.md](docs/ESTRUCTURA_PROYECTO.md).

## Documentación

| Documento | Qué encontrarás ahí |
|---|---|
| [SIGMA_v1.7.md](docs/SIGMA_v1.7.md) | Plan Maestro completo — arquitectura, variantes, roadmap |
| [AGENTS_CREATOR.md](docs/AGENTS_CREATOR.md) | Acta fundacional — contrato de todos los agentes |
| [docs/adr/](docs/adr/) | 16 Architecture Decision Records |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Incidentes reales encontrados y su solución exacta |


## 🏗️ Arquitectura

```
sigma-hito1/
├── orchestrator.py          # Grafo LangGraph, punto de entrada del pipeline
├── webhook_receiver.py      # Recibe respuestas HITL desde Zulip
├── sigma/                   # Paquete Python instalable
│   ├── core/                # Config, conexiones, tracing, checkpointer, estado
│   ├── hooks/                # Notificaciones Zulip
│   └── skills/                # Los 6 skills del Hito 1, cada uno con:
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

- **El CLI todavía usa el esquema de variantes anterior.**
  `orchestrator.py --variant {Full,Lite,Dev,Runtime}` sigue vigente;
  la migración al esquema documentado (`SIGMA-FE/LE/ME/HE` + submodo
  `--submode`) se pospuso deliberadamente al Hito 2 para no arriesgar
  la suite de 65 tests verificada del Hito 1.
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
- **Verificación del dashboard de `0011` — completada.** La corrida
  más reciente en modo Full confirmó paleta de sentimiento fija,
  idiomas agrupados correctamente, y cero advertencias
  (`warnings=[]`). Queda una duda menor abierta: las etiquetas del
  eje "Top engagement" muestran identificadores genéricos de fila
  (`row-0`, `row-1`) en vez de un dato más descriptivo — por confirmar
  si es el diseño final o un ajuste pendiente.
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

Ninguna de estas brechas bloquea el uso del Hito 1 tal como está
documentado — son honestamente el terreno que queda para el Hito 2.

## ⚠️ Limitaciones conocidas

Con la misma disciplina de gobernanza que define a SIGMA, estas son las
brechas reales del estado actual — sin maquillaje:

- **El CLI todavía usa el esquema de variantes anterior.**
  `orchestrator.py --variant {Full,Lite,Dev,Runtime}` sigue vigente;
  la migración al esquema documentado (`SIGMA-FE/LE/ME/HE` + submodo
  `--submode`) se pospuso deliberadamente al Hito 2 para no arriesgar
  la suite de 65 tests verificada del Hito 1.
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
- **Verificación del dashboard de `0011` — completada.** La corrida
  más reciente en modo Full confirmó paleta de sentimiento fija,
  idiomas agrupados correctamente, y cero advertencias
  (`warnings=[]`). Queda una duda menor abierta: las etiquetas del
  eje "Top engagement" muestran identificadores genéricos de fila
  (`row-0`, `row-1`) en vez de un dato más descriptivo — por confirmar
  si es el diseño final o un ajuste pendiente.
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

Ninguna de estas brechas bloquea el uso del Hito 1 tal como está
documentado — son honestamente el terreno que queda para el Hito 2.

## Estado del proyecto

Hito 1 completado: pipeline de 6 skills corriendo de extremo a extremo
contra datos reales, con 65/65 pruebas automatizadas pasando. Para este caso,
la salida del Pipeline está en MinIO; Es decir, el producto terminado debe buscarse
dentro del dashboard que ha sido generado en MinIO. 
El Hito 2 está en diseño: y tendrá mejoras para la entrega de las Ouputs, la orquestación de las distintatas tareas dentro del Pipeline será jerárquica de tres niveles (Director/Engineer/Auditor).

## Licencia

[MIT](LICENSE)

---

<p align="center">
Hecho con 🧠 y gobernanza disciplinada por
<a href="https://orcid.org/0009-0003-4849-3369">Prof. Marx Agustín García Delgado</a>
</p>
