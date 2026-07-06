# SIGMA v1.6 — Sistema Integrado para la Gestión Multiagente

> **SIGMA no es una respuesta. Es el sistema que aprende a responder.**

SIGMA es un ecosistema de agentes autónomos para analizar, diseñar, calcular
y decidir. Múltiples agentes especializados colaboran bajo una arquitectura
de orquestación central para abordar proyectos en los dominios de Ingeniería
de Datos, Data Science, Análisis de Datos, Ingeniería General, Física,
Matemática y Filosofía.

---

## Registro de cambios (Changelog)

> Los cambios de versiones anteriores se registran con literal + número de versión.
> Los cambios de esta versión usan solo literal.

### Cambios en v1.1 (base inicial)

- **a.1.1** Definición del ecosistema SIGMA con arquitectura multiagente.
- **b.1.1** Primer conjunto de ADRs (001–009).
- **c.1.1** Catálogo inicial de 7 skills sin numeración canónica.

### Cambios en v1.2

- **a.1.2** Adición de ADR-010 (secretos), ADR-011 (Langfuse), ADR-012
  (versionado), ADR-013 (auditoría de trayectoria).
- **b.1.2** Renombrado de AGENTS.md a AGENTS_CREATOR.md.
- **c.1.2** Definición formal de las cuatro variantes: Full, Lite, Dev, Runtime.

### Cambios en v1.3

- **a.1.3** Incorporación de ADR-014 (generación dinámica de skills).
- **b.1.3** Ampliación del catálogo a 13 skills con numeración canónica 0000–0012.
- **c.1.3** Documentación en profundidad del Policy Server y el Approval Endpoint.
- **d.1.3** Incorporación de Alpha Envolve como herramienta de validación externa opcional.

### Cambios en v1.3.1

- **a.1.3.1** Sección "Ciclicidad vs. Aciclicidad en la orquestación" — cómo SIGMA
  mantiene un DAG principal acíclico permitiendo subgrafos cíclicos controlados.

### Cambios en v1.4 (versión intermedia, integrada en v1.5)

- **a.1.4** Resolución de la inconsistencia Full/ZERO: "Full" permanece como nombre
  técnico canónico; "SIGMA ZERO" es el nombre comercial de la variante Full.
- **b.1.4** Corrección de la sintaxis de placeholders de [[VAR]] a ${VAR} en todos
  los pipelines y documentos.
- **c.1.4** Catálogo ampliado a 15 skills (adición de 0013, 0014, 0015).
- **d.1.4** Carpetas globales renombradas con sufijo _SIGMA para evitar colisiones
  con carpetas locales de cada skill.

### Cambios en v1.5

- **a** Incorporación de 3 nuevos skills: skill-discovery (0013), stride-modeling
  (0014), pipeline-inspector (0015) — ver catálogo completo.
- **b** Chat interactivo: endpoint chat_api.py + skill pipeline-inspector para
  consultas en lenguaje natural durante la ejecución del pipeline.
- **c** Hook de pre-commit con auto-fix (SIGMA_AUTO_FIX=true) y reglas Semgrep
  personalizadas en hooks_SIGMA/semgrep_rules/concurrency.yaml.
- **d** Comando sigma init para inicializar proyectos desde cero.
- **e** SKILL_STANDARD.md como estándar abierto de empaquetamiento de skills,
  compatible con Google Antigravity y Vercel npx skills.
- **f** Corrección de la descripción de SIGMA Lite: la diferencia con Full es el
  stack (servicios de pago), no el nivel de seguridad.
- **g** Adición del Roadmap de implementación con dos hitos concretos.
- **h** Absorción de las recomendaciones del curso de Vibecoding de Google (5 días):
  las equivalencias con Cloud Trace, Cloud Logging y BigQuery se documentan como
  opciones de SIGMA Lite; no modifican SIGMA Full.
- **i** Corrección de estado del catálogo tras la auditoría y fusión completa de
  "Eco MultiAgentes 4 Skills 2": los 6 skills del Hito 1 (0000, 0001, 0002, 0003,
  0008, 0011) quedan confirmados como Entregados. Versiones actualizadas a las
  reales post-fusión (0000-0003 → v2.0.0; 0008, 0011 → v1.1.0, no v1.2.0 como
  indicaba este documento antes de la corrección). Verificado contra 65/65
  pruebas automatizadas pasando.

### Cambios en v1.6

- **a** Se agrega `ADR-015` (Arquitectura de Análisis en Tiempo Real con
  Hamilton Selector) a la tabla de ADRs — faltaba por completo en v1.5.
- **b** Se agregan 4 filas a "Compatibilidad y estándares": Redis (caché y
  colas, base del Hito 3 de streaming), MinIO (almacenamiento de objetos),
  Zulip (notificaciones HITL/ejecución, distinto de observabilidad de trazas),
  LangGraph (motor real del orquestador).
- **c** Se retiran "Vercel npx skills" y "Google Antigravity" de la misma
  tabla, tras debate documentado (5 argumentos por postura): la compatibilidad
  dependía de `SKILL_STANDARD.md`, que nunca se completó (permanece
  `🔄 En revisión`); el origen de esa fila fue una decisión de posicionamiento
  externo confirmada en auditoría previa, no una necesidad técnica. Ver
  `docs/reportes/` para el debate completo.
- **d** `SKILL_STANDARD.md` se mantiene en `🔄 En revisión` sin fecha de
  cierre — se determina que, tal como estaba planteado (atado a compatibilidad
  con plataformas de terceros), no aporta valor de mantenimiento; `ADR-009`
  ya cubre con rigor el formato de empaquetado de skills. Su única
  justificación futura sería una publicación externa independiente de la
  gobernanza interna de ADRs, no confirmada todavía.
- **e** Conteo de ADRs actualizado de 14 a 15 en las tablas de estructura del
  repositorio y documentación adicional.

---

## Estado del ecosistema

### Documentos canónicos

| # | Documento | Versión | Estado |
|---|---|---|---|
| 01 | README.md | — | ✅ Operativo |
| 02 | AGENTS_CREATOR.md | — | ✅ Operativo |
| 03 | SIGMA_v1.6.md (este documento) | 1.6 | ✅ Operativo |
| 04 | PROJECT_FRAMEWORK.md | 1.1.0 | ✅ Operativo |
| 05 | SKILL_STANDARD.md | 1.0.0 | 🔄 En revisión |
| 06 | PIPELINES.md | — | ⬜ Pendiente |
| 07 | INSTALL.md | — | ⬜ Pendiente |

### Architecture Decision Records (ADRs)

| ADR | Título | Versión | Estado |
|---|---|---|---|
| ADR-001 | Memoria Epistémica — Feature Store + Grafo de Suposiciones | 1.3 | ✅ Aceptado |
| ADR-002 | Paralelismo Masivo Intra-Skill mediante MapReduce | 1.3 | ✅ Aceptado |
| ADR-003 | Seguridad Automática con Modelo Red/Blue/Green | 1.3 | ✅ Aceptado |
| ADR-004 | Vibe Diff Persistente y Human-in-the-Loop con MFA | 1.4 | ✅ Aceptado |
| ADR-005 | Policy Server Híbrido — Estructural + Semántico | 1.3 | ✅ Aceptado |
| ADR-006 | Higiene del Contexto con Placeholders y ContextResolver | 1.3 | ✅ Aceptado |
| ADR-007 | Evaluación Multidimensional (7 Dimensiones) con LLM-as-Judge | 1.3 | ✅ Aceptado |
| ADR-008 | Contención Epistémica Estricta (K ⊆ X) | 1.3 | ✅ Aceptado |
| ADR-009 | Especificación de Skills con Gherkin + LTL | 1.4 | ✅ Aceptado |
| ADR-010 | Directiva de Remediación de Secretos — 12-Factor | 1.3 | ✅ Aceptado |
| ADR-011 | Trazabilidad de Pipelines en Langfuse V2 | 1.3 | ✅ Aceptado |
| ADR-012 | Gestión de Versiones y Promoción de Skills | 1.3 | ✅ Aceptado |
| ADR-013 | Auditoría de Trayectoria de Agentes | 1.3 | ✅ Aceptado |
| ADR-014 | Generación Dinámica de Nuevos Skills bajo Demanda | 1.0 | 🔄 Propuesto |
| ADR-015 | Arquitectura de Análisis en Tiempo Real con Hamilton Selector | 1.0 | 🔄 Propuesto |

### Catálogo de skills (16 skills)

> ✅ Entregado · 🔄 En curso · ⬜ Pendiente · ⚠️ Requiere clarificación

| # | Skill | Responsabilidad | Estado | Milestone |
|---|---|---|---|---|
| 0000 | `system-health-check` | Verifica disponibilidad de MCPs antes del pipeline | ✅ Entregado v2.0.0 | Hito 1 |
| 0001 | `data-ingestion` | Carga datos desde CSV, API o base de datos | ✅ Entregado v2.0.0 | Hito 1 |
| 0002 | `data-cleanser` | Limpia duplicados, nulos y normaliza textos | ✅ Entregado v2.0.0 | Hito 1 |
| 0003 | `data-preprocessor` | Escala, codifica, imputa y balancea clases | ✅ Entregado v2.0.0 | Hito 1 |
| 0004 | `statistical-validator` | Detecta drift, leakage y confusores (2 modos) | ✅ Entregado v1.0.0 | Hito 2 |
| 0005 | `hamilton-selector` | Selecciona framework por energía hamiltoniana | ⬜ Pendiente | Hito 2 |
| 0006 | `ml-trainer` | Modelos clásicos sklearn con validación cruzada | ⬜ Pendiente | Hito 2 |
| 0007 | `dl-trainer` | Redes neuronales con control de gradientes | ⬜ Pendiente | Hito 2 |
| 0008 | `sentiment-analyzer` | Clasifica polaridad con RoBERTa local | ✅ Entregado v1.1.0 | Hito 1 |
| 0009 | `cluster-analyzer` | Agrupa textos con embeddings y K-Means | ⬜ Pendiente | Hito 2 |
| 0010 | `engagement-calculator` | Calcula métricas de interacción por período | ⬜ Pendiente | Hito 2 |
| 0011 | `viz-reporter` | Dashboard autónomo adaptativo según presupuesto | ✅ Entregado v1.1.0 | Hito 1 |
| 0012 | `code-reviewer` | Auditoría de código generado antes de ejecución | ⬜ Pendiente | Hito 2 |
| 0013 | `skill-discovery` | Lista dinámicamente los skills disponibles | ⬜ Pendiente | Hito 2 |
| 0014 | `stride-modeling` | Modelado de amenazas STRIDE sobre pipelines | ⬜ Pendiente | Hito 2 |
| 0015 | `pipeline-inspector` | Consultas interactivas del estado del pipeline | ⚠️ Pendiente clarif. | Hito 2 |

> **Nota sobre 0015-pipeline-inspector:** se necesita definir si opera como LLM
> que lee el estado del DAG desde Langfuse, o como query engine sobre Redis.
> Esta decisión afecta a su expected_trajectory y output_schema. Se clarificará
> antes de escribir su SKILL.md.

---

## Filosofía de diseño

**Multiagente por diseño.** Cada responsabilidad — limpiar, calcular, validar,
visualizar — la asume un agente especializado que colabora con los demás a
través de interfaces explícitas y contratos Gherkin + LTL verificables.

**Seguridad y gobernanza integradas.** No como complemento posterior, sino
como capa estructural que envuelve cada paso: pre-commit hooks, Policy Server,
equipos Red/Blue/Green, STRIDE modeling antes de implementar.

**Evaluación continua en 7 dimensiones.** Un resultado correcto no es
suficiente: también debe ser eficiente, reproducible y fiel a la intención
real del usuario, con pruebas avanzadas para alta incertidumbre.

**Stack adaptable.** SIGMA puede ejecutarse con un stack 100% gratuito y
local (variante Full, nombre comercial "SIGMA ZERO") o integrar servicios
cloud de pago según las necesidades y presupuesto (variantes Lite/Runtime).

**Contención epistémica K⊆X.** Todo agente solo puede afirmar lo que puede
trazar hasta un dato observado. Ninguna alucinación puede filtrarse al output.

---

## Dominios de aplicación

| Dominio | Capacidades principales |
|---|---|
| Ingeniería de Datos | Pipelines de ingesta, transformación, almacenamiento y orquestación a escala |
| Data Science | Modelado ML/DL, validación de hipótesis, pruebas estadísticas avanzadas |
| Análisis de Datos | Exploración, visualización, cuadros de mando interactivos |
| Ingeniería General | Simulación de sistemas, optimización de procesos, automatización |
| Física | Modelado numérico, simulaciones, análisis de series temporales |
| Matemática | Sistemas axiomáticos, cálculo simbólico, prueba asistida de teoremas |
| Filosofía | Análisis de consistencia argumentativa, Zeugmatización epistemológica |

---

## Variantes del sistema

> La variante activa se configura con `SIGMA_VARIANT` en `.env`.
> El valor de la variable siempre usa el nombre técnico canónico.

```bash
SIGMA_VARIANT=Full     # nombre técnico (canónico en ADRs y SKILL.md)
# "SIGMA ZERO" es el nombre comercial de la variante Full
```

### Tabla comparativa de variantes

| Criterio | SIGMA Full (ZERO) | SIGMA Lite | SIGMA Dev | SIGMA Runtime |
|---|---|---|---|---|
| **Objetivo** | Producción sin coste | Capacidad máxima con pago | Desarrollo y depuración | Full con datos reales |
| **Coste operativo** | $0 | Variable | $0 | Variable |
| **Esfuerzo de setup** | Alto | Bajo | Medio | Depende de la base |
| **Policy Server completo** | ✅ Sí | ✅ Sí | ⚠️ Solo estructural | ✅ Sí |
| **Equipos Red/Blue/Green** | ✅ Sí | ✅ Sí | ❌ No | ✅ Sí |
| **HITL con Approval Endpoint** | ✅ MFA con token | ✅ MFA con TOTP | ❌ Desactivado | ✅ MFA con TOTP |
| **Generación dinámica (ADR-014)** | ✅ Nivel LOW sin aprobación | ✅ Ciclo completo | ❌ Desactivada | ✅ Aprobación siempre |
| **Langfuse** | ✅ Autoalojado | ⚠️ LangSmith o Cloud | ⚠️ Opcional | ✅ Autoalojado |
| **Orquestador LLM** | Gemini API free tier | Gemini Pro / Vertex AI | Ollama local | Gemini API o Pro |
| **Almacenamiento** | MinIO local | GCS / S3 | MinIO (opcional) | MinIO o GCS |
| **Modelos locales** | Ollama (deepseek, mistral) | Opcional | Ollama (opcional) | Ollama |
| **Workers (modo Dev)** | — | — | Forzado a 1 | — |
| **SMOTE** | ✅ Activo | ✅ Activo | ❌ class_weight | ✅ Activo |

### Descripción narrativa de cada variante

**SIGMA Full (nombre comercial: SIGMA ZERO)**
La variante canónica de referencia. Todos los ADRs activos, todos los
equipos de seguridad, Policy Server híbrido completo (estructural + semántico),
evaluación 7D, HITL con Approval Endpoint local y generación dinámica de skills.
Stack 100% gratuito y autoalojado. Requiere configuración manual de todos los
componentes. Se usa para producción, staging y demostraciones sin coste recurrente.
El nombre "SIGMA ZERO" comunica que el coste operativo es cero.

**SIGMA Lite**
Misma arquitectura de seguridad y gobernanza que Full. La diferencia está en
el stack, no en el nivel de protección: permite sustituir componentes gratuitos
por servicios de pago cuando el equipo requiere menor fricción operativa o mayor
escala. Langfuse puede reemplazarse por LangSmith o Google Cloud Logging; MinIO
por GCS o S3; Ollama por Gemini Pro o Vertex AI. Pensada para organizaciones que
ya tienen contratos cloud activos y quieren aprovechar esos créditos.

**SIGMA Dev**
Entorno de desarrollo con restricciones relajadas para no interrumpir la
depuración. Workers forzados a 1 (ADR-002), SMOTE reemplazado por class_weight,
equipos Red/Blue/Green desactivados, HITL desactivado, Policy Server solo
estructural. Los datos son sintéticos o de prueba. Nunca se usa en producción.

**SIGMA Runtime**
Una instancia concreta de SIGMA Full desplegada sobre un entorno de producción
real con parámetros inyectados via variables de entorno. Es el modo en que SIGMA
ejecuta pipelines reales con datos reales. Requiere MFA con TOTP en el Approval
Endpoint. Cualquier generación dinámica de skills requiere aprobación del
operador independientemente del nivel de impacto.

---

## Arquitectura general

```text
┌─────────────────────────────────────────────────────────────────┐
│         Usuario / CLI / Chat interactivo / Dashboard A2UI       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│          Orquestador (LangGraph + Gemini API / Ollama)          │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Skills (MCP)   │  │  Agentes A2A    │  │  Policy Server │  │
│  │  0000 → 0015    │  │  Auditor        │  │  Estructural   │  │
│  │                 │  │  Red Team       │  │  + Semántico   │  │
│  │                 │  │  Blue Team      │  │  (LLM juez ≠   │  │
│  │                 │  │  Green Team     │  │  Orquestador)  │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ Memoria         │  │ Evaluación 7D   │  │ Approval       │  │
│  │ Epistémica      │  │ Intención       │  │ Endpoint       │  │
│  │ Feature Store   │  │ Corrección      │  │ (HITL local    │  │
│  │ + Grafo de      │  │ Coste · Código  │  │ puerto 8765)   │  │
│  │ Suposiciones    │  │ Trayectoria     │  │                │  │
│  │ (ADR-001)       │  │ Autoreparación  │  │                │  │
│  │                 │  │ Visual (ADR-007)│  │                │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Chat API        │  │ Langfuse V2     │                      │
│  │ /chat/status    │  │ Trazabilidad    │                      │
│  │ /chat/ask       │  │ completa        │                      │
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            Infraestructura (por variante)                       │
│  PostgreSQL · Redis · MinIO · Ollama · Docker + WSL2            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flujo de ejecución completo

```text
1. ENTRADA
   Usuario envía prompt o selecciona pipeline YAML
   └─ Orquestador interpreta la solicitud

2. PLANIFICACIÓN
   Orquestador construye DAG dinámico
   └─ Lee frontmatter de cada skill (ADR-009)

3. PRE-VUELO DE SEGURIDAD [Solo Full / Runtime]
   Red Team ejecuta sub-grafo clonado con datos de prueba
   └─ Detecta vulnerabilidades antes de tocar datos reales (ADR-003)

4. EJECUCIÓN
   DAG se ejecuta nodo a nodo
   ├─ Policy Server intercepta cada llamada a herramienta
   ├─ ContextResolver resuelve ${VAR} antes de cada skill
   └─ Workers MapReduce / chain según configuración

5. EVALUACIÓN CONTINUA
   Al finalizar cada skill:
   ├─ Evaluador rápido determinista → 100% de ejecuciones
   └─ LLM-as-Judge → 5% de ejecuciones (+ anomalías)

6. APROBACIÓN HITL [Si nivel ≥ MEDIUM]
   Orquestador pausa el DAG
   ├─ Genera Vibe Diff en MinIO (WORM)
   └─ Espera respuesta en Approval Endpoint (timeout 300s)

7. FINALIZACIÓN
   Output producido
   ├─ Todos los eventos trazados en Langfuse (ADR-011)
   └─ Resultado almacenado en MinIO
```

---

## Ciclicidad vs. Aciclicidad en la orquestación

El DAG principal de SIGMA es acíclico por diseño. Esto garantiza terminación,
trazabilidad y restricción epistémica K⊆X. Sin embargo, SIGMA permite ciclos
controlados dentro de subgrafos específicos.

**¿Por qué el DAG principal es acíclico?**

Un ciclo en el DAG principal podría provocar bucles infinitos, dificultar la
correlación de trazas en Langfuse y reintroducir datos no observados en el
conjunto X, violando ADR-008.

**¿Dónde se permiten ciclos controlados?**

| Mecanismo | Implementación | Condición de salida |
|---|---|---|
| Reintentos MapReduce (ADR-002) | Loop dentro del nodo skill | Contador máximo (policies.yaml); si excede → Green Team |
| Green Team auto-refactor (ADR-003) | Subgrafo: diagnóstico → corrección → re-ejecución | Máximo 2 iteraciones; si no recupera → HITL |
| Approval Endpoint (ADR-004) | Polling a Redis cada 5 segundos | Timeout configurable (default 300s) |
| Actualización del Grafo (ADR-001) | Workers encolan en Redis; serializador FIFO | No hay ciclo de ejecución; es asíncrono |

**Ejemplo: Fallo durante análisis estadístico**

```text
DAG principal (acíclico):
Ingesta → Limpieza → Análisis → Evaluación → Fin
                         │
                         ▼ (fallo)
              ┌──────────────────────┐
              │  Sub-grafo Green Team│
              │  ┌────────────────┐  │
              │  │  Diagnóstico   │  │
              │  │  Corrección    │  │
              │  │  Re-ejecución  │  │
              │  └────────────────┘  │
              │  (máximo 2 veces)    │
              └──────────────────────┘
                         │
              ¿Corregido? → Sí → DAG continúa
                       No → HITL
```

---

## Seguridad en profundidad

### Policy Server — Interceptor de herramientas

Intercepta **todas** las llamadas a herramientas antes de que se ejecuten.

| Capa | Mecanismo | Latencia | Cobertura |
|---|---|---|---|
| Estructural (YAML) | Reglas deterministas por entorno y rol | < 5 ms | ~95% de llamadas |
| Semántica (LLM juez) | Modelo diferente al Orquestador | Variable | ~5% de llamadas (casos ambiguos) |

El LLM juez es siempre un modelo distinto al Orquestador (ADR-005). Si ambos
fueran el mismo modelo, un modelo comprometido podría juzgar sus propias acciones.

**Disponibilidad por variante:**

| Variante | Capa estructural | Capa semántica |
|---|---|---|
| Full / Runtime | ✅ Activa | ✅ Activa |
| Lite | ✅ Activa | ✅ Activa |
| Dev | ✅ Activa | ⚠️ Opcional |

### Approval Endpoint — HITL local

Servidor HTTP ligero en puerto 8765. No depende de servicios externos.

| Nivel | Criterio | Vibe Diff | Aprobación |
|---|---|---|---|
| LOW | Reversible, < 1000 filas | No requerido | Automática |
| MEDIUM | Reversible, > 1000 filas o PII | Requerido | Approval Endpoint |
| HIGH | Irreversible o impacto en _prod | Requerido + WORM | Endpoint + MFA |
| CRITICAL | Despliegue o borrado masivo | Requerido + máx. retención | Endpoint + MFA hardware |

### STRIDE Modeling (skill 0014)

Antes de implementar cualquier pipeline de producción, el skill stride-modeling
analiza el diseño del sistema e identifica amenazas en seis categorías:
Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service
y Elevation of Privilege. El resultado es un informe de amenazas que alimenta
la sección "Límites de Seguridad y Aserciones" del PROJECT_FRAMEWORK.md.

### Pre-commit hook con auto-fix

```bash
# Instalar hook
cp hooks_SIGMA/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Con corrección automática
SIGMA_AUTO_FIX=true git commit -m "feat: nuevo skill"
```

El hook ejecuta reglas Semgrep personalizadas (hooks_SIGMA/semgrep_rules/)
que detectan condiciones de carrera y claves API hardcodeadas en
inicializaciones de modelos.

---

## Evaluación: 7 dimensiones + pruebas estadísticas avanzadas

### Las 7 dimensiones (ADR-007)

| # | Dimensión | Método | Coste de tokens |
|---|---|---|---|
| D1 | Intención del usuario | LLM-as-Judge (5% de ejecuciones) | Bajo |
| D2 | Corrección funcional | Tests deterministas + Pydantic | Cero |
| D3 | Corrección visual | Validación de schema HTML/dashboard | Cero |
| D4 | Coste y eficiencia | Métricas Langfuse | Cero |
| D5 | Calidad del código | Análisis estático (pylint, bandit) | Cero |
| D6 | Calidad de trayectoria | Comparación con expected_trajectory | Cero |
| D7 | Autoreparación | Ratio de reintentos exitosos vs HITL | Cero |

### Pruebas avanzadas bajo incertidumbre (skill 0004)

| Condición del proyecto | Método aplicado | Veredicto si evidencia débil |
|---|---|---|
| Hipótesis explícita declarada | Factor de Bayes (prior uniforme por defecto) | INSUFFICIENT_EVIDENCE (BF < 3) |
| Sin hipótesis, distribución desconocida | Prueba de Permutación + Bootstrapping | PAUSED_HITL si IC demasiado ancho |
| Datos con índice temporal | Test ADF + Causalidad de Granger | APPROVED_WITH_WARNINGS si no estacionaria |
| Entorno vivo con feedback inmediato | A/B Testing Bayesiano (Multi-Armed Bandits) | INSUFFICIENT_EVIDENCE si pocas muestras |
| Ninguna condición anterior | Descriptivos básicos (nulos, varianza, duplicados) | PAUSED_HITL si superan umbrales |

---

## Canales de interacción

| Canal | Propósito | Activo por defecto | Variante |
|---|---|---|---|
| CLI (python -m sigma run) | Ejecución de pipelines | ✅ Sí | Todas |
| Approval Endpoint (puerto 8765) | HITL para acciones críticas | ✅ Sí | Full / Runtime |
| Chat API (/chat/ask) | Consultas durante ejecución | ✅ Sí | Todas |
| Zulip | Notificaciones y aprobaciones vía chat | ⚠️ Opcional | Todas |
| BurntToast (Windows) | Alertas de escritorio | ⚠️ Opcional | Todas |
| Dashboard A2UI | Visualización de resultados | ✅ Sí (viz-reporter) | Todas |

---

## Componentes del ecosistema

| Componente | Función principal | ADR | Variante |
|---|---|---|---|
| Orquestador (LangGraph) | Construye y ejecuta el DAG | ADR-002, ADR-009 | Todas |
| Agente Auditor | Verifica trayectoria, K⊆X y calidad | ADR-013 | Todas |
| Red Team | Ataque simulado en pre-vuelo | ADR-003 | Full / Runtime |
| Blue Team | Monitorización de modelos (AgBOM) | ADR-003 | Full / Runtime / Lite |
| Green Team | Recuperación y rollback automáticos | ADR-003 | Todas |
| Memoria Epistémica | Feature Store + Grafo de Suposiciones | ADR-001, ADR-008 | Todas |
| Evaluación 7D | Evaluación multidimensional continua | ADR-007 | Todas |
| ContextResolver | Resuelve ${VAR} y sanitiza inputs | ADR-006 | Todas |
| Policy Server | Intercepta herramientas antes de ejecución | ADR-005 | Todas |
| Langfuse V2 | Trazabilidad centralizada de todos los eventos | ADR-011 | Todas |
| Gestión de secretos | .env + get_required_env() | ADR-010 | Todas |
| Versionado de skills | SemVer + promoción Dev→Staging→Prod | ADR-012 | Todas |
| Approval Endpoint | HITL local con Vibe Diff persistente | ADR-004 | Full / Runtime |
| Chat API | Consultas interactivas del estado del pipeline | — | Todas |

---

## Requisitos previos por variante

> ✅ Obligatorio · ⚠️ Opcional · ❌ No aplica · (*) Reemplazable por servicio de pago

| Componente | Full | Lite | Dev | Runtime | Versión mínima |
|---|:---:|:---:|:---:|:---:|---|
| Python | ✅ | ✅ | ✅ | ✅ | 3.12.4 |
| Docker Desktop / Podman | ✅ | ✅ | ✅ | ✅ | 4.x |
| PostgreSQL | ✅ | ✅ | ✅ | ✅ | 14+ |
| Redis | ✅ | ✅ | ✅ | ✅ | 7+ |
| MinIO | ✅ | (*) | ⚠️ | ✅ | última |
| Ollama | ✅ | (*) | ⚠️ | ✅ | última |
| Langfuse V2 (autoalojado) | ✅ | (*) | ⚠️ | ✅ | V2 |
| Gemini API (free tier) | ✅ | (*) | ⚠️ | ✅ | — |
| Gemini Pro / Vertex AI | ❌ | (*) | (*) | (*) | — |
| GCS / S3 | ❌ | (*) | (*) | (*) | — |
| BigQuery / AWS Athena | ❌ | (*) | (*) | (*) | — |
| LangSmith | ❌ | (*) | (*) | (*) | — |
| Neo4j Aura | ❌ | (*) | (*) | (*) | — |
| Alpha Envolve (validación ext.) | ❌ | (*) | (*) | (*) | — |
| RAM mínima | 16 GB | 8 GB | 8 GB | 32 GB | — |
| RAM recomendada | 32 GB | 16 GB | 16 GB | 64 GB | — |

---

## Estructura del repositorio

```text
/
├── AGENTS_CREATOR.md           # Acta fundacional — define todos los agentes
├── README.md                   # Punto de entrada del repositorio
├── SIGMA_v1.6.md               # Este documento — Plan Maestro
├── PROJECT_FRAMEWORK.md        # Ciclo de vida de proyectos en SIGMA
├── SKILL_STANDARD.md           # Estándar abierto de empaquetamiento de skills
├── policies.yaml               # Políticas de herramientas por entorno y rol
│
├── pipelines/                  # Pipelines YAML predefinidos
│   └── analisis_opinion_twitter.yaml
│
├── specs/                      # Especificaciones de proyectos
│
├── skills/                     # 16 skills (0000–0015)
│   ├── 0000-system-health-check/
│   ├── 0001-data-ingestion/
│   ├── 0002-data-cleanser/
│   ├── 0003-data-preprocessor/    # ✅ Entregado v2.0.0
│   ├── 0004-statistical-validator/ # ✅ Entregado v1.0.0
│   ├── 0005-hamilton-selector/
│   ├── ...
│   └── 0015-pipeline-inspector/
│
├── agent_cards/                # Identidad de los agentes externos
│   ├── orchestrator.yaml
│   ├── auditor.yaml
│   ├── red_team.yaml
│   ├── blue_team.yaml
│   └── green_team.yaml
│
├── hooks_SIGMA/                # Scripts deterministas transversales
│   ├── pre-commit.sh
│   └── semgrep_rules/
│       └── concurrency.yaml
│
├── endpoints/                  # APIs del ecosistema
│   ├── approval_endpoint.py
│   ├── chat_api.py
│   ├── dashboard_api.py
│   └── zulip_adapter.py
│
├── evals_SIGMA/                # Evaluaciones transversales de todo SIGMA
├── assets_SIGMA/               # Assets globales compartidos
├── references_SIGMA/           # Referencias globales del ecosistema
├── outputs/                    # Resultados, informes y checkpoints
│
└── docs/
    └── adr/                    # 15 Architecture Decision Records
        ├── adr-README.md
        ├── adr-001-memoria-epistemica.md
        └── ... (adr-002 a adr-014)
```

> **Convención de nomenclatura:** las carpetas con sufijo `_SIGMA` son recursos
> transversales de todo el ecosistema. Las carpetas sin sufijo dentro de cada
> skill (tests/, evals/, references/) son recursos locales de ese skill.
> Esta distinción evita colisiones y permite identificar de inmediato la
> pertenencia de cualquier recurso.

---

## Roadmap de implementación

### Hito 1 — SIGMA v1.0 Ejecutable

**Objetivo:** pipeline funcional de extremo a extremo con dataset real.

**Skills necesarios (5):**

| Skill | Estado |
|---|---|
| 0000-system-health-check | ✅ Entregado v2.0.0 |
| 0001-data-ingestion | ✅ Entregado v2.0.0 |
| 0002-data-cleanser | ✅ Entregado v2.0.0 |
| 0003-data-preprocessor | ✅ Entregado v2.0.0 |
| 0008-sentiment-analyzer | ✅ Entregado v1.1.0 |
| 0011-viz-reporter | ✅ Entregado v1.1.0 |

**Dataset:** Tirendaz Twitter Sentiment (22.500 tweets)

**Entregable:** pipeline analisis_opinion_twitter.yaml ejecutándose de extremo
a extremo, generando un dashboard HTML con análisis de sentimiento visible.

**Criterio de éxito:** un humano puede ejecutar `python -m sigma run pipelines/analisis_opinion_twitter.yaml` y ver el dashboard en el navegador sin errores.

### Hito 2 — SIGMA v1.5 Completo

**Objetivo:** ecosistema completo con los 16 skills, pruebas estadísticas
avanzadas, seguridad STRIDE, chat interactivo y generación dinámica de skills.

**Dataset:** WC2026-Tweets (objetivo: 130K–28M tweets)

**Entregable:** SIGMA en plena capacidad de producción, documentado, testeado
y desplegable en un solo comando.

---

## Inicio rápido

```bash
# 1. Inicializar un proyecto SIGMA (nuevo en v1.5)
sigma init mi-proyecto
cd mi-proyecto

# 2. Configurar variables de entorno
cp .env.example .env
# Variables obligatorias: GEMINI_API_KEY, SIGMA_VARIANT=Full

# 3. Levantar servicios base
docker compose up -d

# 4. Verificar que el sistema está operativo
python -m sigma status

# 5. Ejecutar tu primer pipeline
python -m sigma run pipelines/analisis_opinion_twitter.yaml
```

---

## Ejemplos de uso

### Análisis de sentimiento de tweets

```bash
python -m sigma run pipelines/analisis_opinion_twitter.yaml \
  --input data/tweets_raw.parquet \
  --workers 50 \
  --output outputs/opinion_dashboard.html
```

### Modelado de amenazas STRIDE antes de implementar

```bash
python -m sigma run pipelines/stride_analysis.yaml \
  --target pipelines/analisis_opinion_twitter.yaml \
  --output outputs/stride_report.md
```

### Consulta interactiva durante ejecución

```bash
# En otra terminal mientras el pipeline corre:
curl -X POST http://localhost:8080/chat/ask \
  -d '{"question": "¿Qué hipótesis has detectado hasta ahora?"}'
```

---

## Compatibilidad y estándares

| Estándar / Plataforma | SIGMA equivalente | Notas |
|---|---|---|
| Google Cloud Trace | Langfuse V2 (autoalojado) | Exportable a Cloud Trace en SIGMA Lite |
| Google Cloud Logging | Langfuse + logs locales | Fallback a Redis y archivos (ADR-011) |
| BigQuery | PostgreSQL + DuckDB | Reemplazable por BigQuery en SIGMA Lite |
| Google Agent Registry | skill-discovery (0013) | SIGMA implementa su propio registro |
| Redis (caché y colas) | Redis con persistencia AOF | Base del futuro streaming (ADR-015); usado por MapReduce (ADR-002) |
| MinIO | MinIO (S3-compatible, autoalojado) | Almacenamiento de objetos — dashboards, artefactos, WORM para Vibe Diff |
| Zulip (observabilidad de notificaciones) | Zulip con topics separados (RUNS/HITL) | Notificaciones HITL y de ejecución, no observabilidad de trazas — eso es Langfuse |
| LangGraph | LangGraph (orquestador de grafos) | Motor real del DAG de skills; circuit breaker con fallo rápido |

> **Nota v1.6 — Vercel npx skills y Google Antigravity retiradas de esta
> tabla.** Estaban presentes desde v1.5 con la nota "Compatible por
> diseño", condicionadas a `SKILL_STANDARD.md` — documento que nunca se
> completó (permanece `🔄 En revisión`). El origen de esa fila fue una
> decisión de posicionamiento externo, no una necesidad de mantenimiento
> del ecosistema. Se retira porque la afirmación de compatibilidad no
> tenía sustento verificable, y mezclarla con equivalentes reales
> (Langfuse, PostgreSQL+DuckDB) diluía la credibilidad de esta tabla.
> Ver `docs/reportes/` para el debate completo que sustenta esta decisión.

---

## Documentación adicional

| Documento | Descripción |
|---|---|
| AGENTS_CREATOR.md | Acta fundacional — define y crea todos los agentes |
| PROJECT_FRAMEWORK.md | Ciclo de vida de proyectos, fases y mitigaciones |
| SKILL_STANDARD.md | Estándar abierto de empaquetamiento de skills |
| PIPELINES.md | Guía de creación y ejecución de pipelines |
| INSTALL.md | Guía detallada de instalación paso a paso |
| docs/adr/ | 15 Architecture Decision Records |

---

## Licencia

[MIT](LICENSE)

---

> **SIGMA** no es un producto cerrado: es un marco de trabajo vivo.
> Si entiendes este documento, entiendes el punto de entrada del ecosistema.
