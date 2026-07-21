# SIGMA — Roadmap Técnico de Implementación

**Versión:** 1.0.0
**Fecha:** 2026-06-30
**Estado:** Aceptado
**Propósito:** Cerrar la brecha entre especificación (ADRs + SKILL.md) y código ejecutable.

---

## 0. Diagnóstico de partida

A la fecha de este documento, SIGMA tiene 14 ADRs aceptados, 7 skills
completamente especificados con SKILL.md + defaults.yaml + tests +
schemas + evals, y cero líneas de código de producción ejecutándose.
Este roadmap existe para revertir esa proporción.

**Principio rector de este roadmap:** ningún ítem se marca como
completado por tener un esqueleto o un borrador conceptual. Solo se
marca completado cuando corre contra infraestructura real (PostgreSQL,
Redis real, no mocks) y produce un resultado verificable.

---

## 1. Infraestructura de despliegue: análisis y decisión

### 1.1 Qué necesita estar disponible 24/7 (y qué no)

No todo SIGMA necesita presencia permanente. Se distinguen dos capas:

**Capa ligera (debe estar siempre disponible):**
- Approval Endpoint — para aprobar HITL desde el móvil sin depender del PC encendido
- Redis ligero — cola de aprobaciones pendientes
- Proceso de heartbeat/monitoreo de pipelines programados

**Capa pesada (permanece en el PC local, SIGMA Full tal como fue diseñado):**
- Orquestador completo con LangGraph
- Ollama y los modelos locales (deepseek-coder, mistral, llama3.2)
- PostgreSQL con los datos completos (hasta 28M tweets)
- MinIO, modelos de Deep Learning, todo el cómputo pesado

### 1.2 Comparativa de opciones para la capa ligera

| Criterio | Oracle Cloud Free Tier | Raspberry Pi local | VPS de bajo costo |
|---|---|---|---|
| Costo | $0 permanente | ~$70 hardware único | ~€5/mes (~€60/año) |
| Riesgo de suspensión de cuenta | Alto (patrón reportado de forma amplia y consistente) | Ninguno | Ninguno |
| SLA | Ninguno | No aplica | ~99.9% típico |
| Dependencia de tu conexión residencial | No | Sí (no resuelve el problema original) | No |
| Mantenimiento físico | No | Sí (SD, UPS, actualizaciones) | No |
| Especificaciones | 4 OCPU ARM + 24GB RAM | Variable (Pi 5: 8GB RAM) | 2-4 vCPU, 4-8GB RAM |

### 1.3 Decisión

**VPS de bajo costo (Hetzner CX22 o Contabo VPS, ~€5/mes) exclusivamente
para la capa ligera.** No es Google Cloud Agent Runtime con Cloud Trace
y BigQuery — eso permanece descartado por sobredimensionado para un
sistema de un solo operador. Es un punto medio deliberado: preserva el
stack gratuito para el 95% del sistema, y reserva un gasto mínimo
predecible solo para el componente de gobernanza que no puede fallar
(el Approval Endpoint es, por diseño, la pieza de seguridad de todo
el ecosistema — no es coherente que dependa de una cuenta gratuita
con historial de suspensiones arbitrarias).

**Pendiente de tu confirmación:** elegir entre Hetzner o Contabo y
proceder con el aprovisionamiento cuando lleguemos a la fase 3 de
este roadmap.

---

## 2. Fases del roadmap

### FASE 1 — Núcleo ejecutable mínimo (prioridad máxima)

Objetivo: que un pipeline real corra de extremo a extremo en tu PC,
aunque sea con un solo skill.

| # | Ítem | Artefacto a producir | Criterio de "completado" |
|---|---|---|---|
| 1.1 | `sigma/core/` — módulo base | `get_required_env()`, `emit_trace_event()`, conexión PostgreSQL/Redis | Importable y testeado con `pytest` |
| 1.2 | `skill.py` de `0000-system-health-check` | Implementación Python completa | Ejecuta contra PostgreSQL y Redis reales, devuelve veredicto HEALTHY/DEGRADED/BLOCKED |
| 1.3 | `tests/test_skill.py` de `0000` | Steps de pytest-bdd para el `.feature` ya escrito | Los 5 escenarios Gherkin pasan en verde |
| 1.4 | `orchestrator.py` — esqueleto mínimo real | Grafo LangGraph que invoca un único nodo (`0000`) | `python -m sigma run` ejecuta el health check y termina |

**Por qué este orden:** `0000` es el skill más simple y autocontenido
del catálogo (no toca datos, solo verifica conectividad). Es el primer
candidato razonable para ser el primer código real del sistema.

---

### FASE 2 — Pipeline completo del Hito 1 (Tirendaz end-to-end)

Objetivo: el pipeline `analisis_opinion_twitter.yaml` corre completo
con el dataset Tirendaz y genera un dashboard visible.

| # | Ítem | Artefacto a producir | Criterio de "completado" |
|---|---|---|---|
| 2.1 | `skill.py` + `test_skill.py` de `0001-data-ingestion` | Implementación completa | Carga el CSV Tirendaz real (22.500 filas) en PostgreSQL |
| 2.2 | `skill.py` + `test_skill.py` de `0002-data-cleanser` | Implementación completa | Produce tabla `_cleaned` verificable |
| 2.3 | `skill.py` + `test_skill.py` de `0003-data-preprocessor` | Implementación completa | Produce tabla `_processed` verificable |
| 2.4 | `skill.py` + `test_skill.py` de `0008-sentiment-analyzer` | Implementación completa con RoBERTa local | Clasifica los 22.500 tweets, distribución de clases verificable |
| 2.5 | `skill.py` + `test_skill.py` de `0011-viz-reporter` | Implementación completa, modo Plotly estático | Dashboard HTML accesible, verificado por petición real |
| 2.6 | `orchestrator.py` — DAG completo de 5 nodos | Grafo LangGraph encadenando los 5 skills | `python -m sigma run pipelines/analisis_opinion_twitter.yaml` corre sin intervención manual |
| 2.7 | Test de integración end-to-end real | `tests/integration/test_pipeline_tirendaz.py` con steps reales (no solo el `.feature`) | El test corre en CI y pasa contra datos reales |

**Este es el cierre formal del Hito 1 (SIGMA v1.0 Ejecutable).**

---

### FASE 3 — Gobernanza operativa real

Objetivo: el sistema deja de depender de que tú estés frente al PC.

| # | Ítem | Artefacto a producir | Criterio de "completado" |
|---|---|---|---|
| 3.1 | Aprovisionar VPS (Hetzner/Contabo) | Servidor activo con Docker | `ssh` funcional, Docker corriendo |
| 3.2 | `endpoints/approval_endpoint.py` — implementación real | Servidor Flask/FastAPI con autenticación TOTP | Responde a `/pending` y `/approve` con datos reales, no mock |
| 3.3 | Despliegue del Approval Endpoint en el VPS | `docker-compose.yml` específico para el VPS | Accesible desde tu móvil vía HTTPS |
| 3.4 | `policies.yaml` operativo completo | Archivo consolidado (no fragmentos dispersos) con reglas estructurales reales | El Policy Server (cuando exista, ver Fase 4) lo carga sin errores |
| 3.5 | Integración Zulip real | Webhook funcional desde el Approval Endpoint | Notificación de prueba llega a tu Zulip |

---

### FASE 4 — Policy Server y Orquestador completos

Objetivo: el sistema completo de gobernanza (ADR-003, ADR-004, ADR-005)
deja de ser especificación y se vuelve ejecutable.

| # | Ítem | Artefacto a producir | Criterio de "completado" |
|---|---|---|---|
| 4.1 | `policy_server.py` — proceso aparte | Servidor que implementa capa estructural (YAML) | Bloquea/permite llamadas reales según `policies.yaml` |
| 4.2 | Capa semántica del Policy Server | Integración con LLM juez (Ollama local, distinto del Orquestador) | Detecta un caso de prueba de credencial hardcodeada real |
| 4.3 | `orchestrator.py` — versión completa | DAG dinámico que lee cualquier pipeline YAML, no solo el de Tirendaz | Corre un segundo pipeline distinto sin modificar código |
| 4.4 | `sigma/core/langfuse_setup.py` — integración real | `CallbackHandler` conectado a Langfuse autoalojado | Las trazas de un pipeline real aparecen en el dashboard de Langfuse |
| 4.5 | Política de último recurso de Langfuse (ADR-011) | Fallback a Redis y luego a logs locales | Simular Langfuse caído y verificar que los eventos no se pierden |

---

### FASE 5 — Skills restantes del catálogo (Hito 2)

Objetivo: completar el catálogo de 16 skills con código real, no solo
especificación.

| # | Skill | Prioridad | Nota |
|---|---|---|---|
| 5.1 | `0004-statistical-validator` | Alta | Ya especificado en detalle; implementar la matriz de decisión completa |
| 5.2 | `0005-hamilton-selector` | Media | Depende de tener `ml-trainer` y `dl-trainer` para tener algo que seleccionar |
| 5.3 | `0006-ml-trainer` | Media | |
| 5.4 | `0007-dl-trainer` | Media | |
| 5.5 | `0009-cluster-analyzer` | Baja | No bloqueante para ningún hito |
| 5.6 | `0010-engagement-calculator` | Baja | No bloqueante |
| 5.7 | `0012-code-reviewer` | Media | Transversal, útil tenerlo pronto para auditar el resto del código generado |
| 5.8 | `0013-skill-discovery` | Baja | Reescribir con formato canónico (pendiente desde sesión anterior) |
| 5.9 | `0014-stride-modeling` | Baja | Reescribir con formato canónico (pendiente desde sesión anterior) |
| 5.10 | `0015-pipeline-inspector` | Media | **Rediseñar como agente separado con LLM independiente del Orquestador** — ver sección 3 |

---

### FASE 6 — Pulido y simulación de ADR-014

| # | Ítem | Criterio de "completado" |
|---|---|---|
| 6.1 | CI/CD real (reemplazar comandos fantasma) | `sigma review` y `sigma validate-policies` existen como comandos reales en `sigma/cli.py` |
| 6.2 | `USER_GUIDE.md` completo | Cubre escritura de pipeline, ejecución, interpretación de resultados |
| 6.3 | Simulación completa de ADR-014 | El Orquestador en modo Arquitecto genera un skill nuevo de principio a fin, con marca `gia_`, y pasa el ciclo de validación completo |

---

## 3. Pipeline-inspector: corrección arquitectónica pendiente

Registrado aquí para no perderlo: el `0015-pipeline-inspector` no debe
implementarse como una función que el Orquestador ejecuta sobre sí
mismo. Por el mismo principio que ADR-005 exige que el LLM juez del
Policy Server sea distinto al Orquestador (para evitar que un modelo
comprometido juzgue sus propias acciones), el pipeline-inspector debe
ser un agente separado con su propio LLM —el espejo del Orquestador:
si este usa Gemini, el inspector usa Ollama local, o viceversa— que lee
el estado desde Langfuse y el Grafo de Suposiciones de forma externa,
sin depender de la autoevaluación del Orquestador.

Este rediseño debe aplicarse antes de escribir el `SKILL.md` definitivo
del `0015` en la Fase 5.

---

## 4. Espacio reservado: arquitectura de 3 agentes orquestadores

*Pendiente de recibir la propuesta del usuario sobre una arquitectura
de tres agentes orquestadores para un sistema autónomo operable por
una sola persona. Esta sección se completará y evaluará formalmente
en cuanto el usuario comparta los detalles. Su encaje con este roadmap
—en particular con las Fases 3 y 4, donde vive el Orquestador actual—
se determinará en esa evaluación conjunta.*

---

## 5. Resumen ejecutivo de prioridades inmediatas

Si solo se pudiera trabajar en tres cosas a partir de hoy, en orden:

1. `skill.py` de `0000-system-health-check` (Fase 1.2) — el primer
   código real del sistema, el más simple posible.
2. `orchestrator.py` mínimo capaz de invocar ese único nodo (Fase 1.4).
3. Repetir el patrón con `0001-data-ingestion` cargando el CSV Tirendaz
   real (Fase 2.1).

Tres piezas de código real superan en valor a diez documentos
comparativos adicionales.
