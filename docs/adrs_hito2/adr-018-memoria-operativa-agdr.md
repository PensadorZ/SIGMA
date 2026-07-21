---
id: ADR-018
title: Memoria Operativa entre Corridas (Ag-DR) y Formalización de la Lógica de Decisión del Director
version: 1.2
status: Aceptado
original-date: 2026-07
revision-date: 2026-07
supersedes: ninguno
minimum-references: ADR-001, ADR-006, ADR-008, ADR-009, ADR-011, ADR-016, ADR-019
milestone-of-application: Hito 2 (diseño) / Hito 3 (implementación completa, a confirmar)
approved-by: Prof. Marx A. García Delgado
file-name: adr-018-memoria-operativa-agdr.md
---

# ADR-018: Memoria Operativa entre Corridas (Ag-DR) y Formalización de la Lógica de Decisión del Director

## Resumen ejecutivo

Este ADR nace de un hueco identificado al comparar SIGMA contra un framework
externo de gestión de agentes (Agents.md/Context.md/Skills.md/Memory.md):
SIGMA no tiene ningún mecanismo por el cual el sistema acumule experiencia
operativa de una corrida a la siguiente. Se define aquí el **Ag-DR**
(Agent Decision Record) — un registro que cada orquestador genera sobre
sus propias decisiones reales, distinto de un ADR (que documenta
arquitectura, no ejecución). Se formaliza también, a petición explícita
de Marx, que la lógica de decisión del Director se especifique con el
mismo rigor que ya exige ADR-009 a los skills: esquemas + Gherkin.

---

## Contexto

`ADR-001` (memoria epistémica) separa hechos verificados de hipótesis
**dentro de una misma corrida** — no acumula nada entre corridas. Ningún
componente de SIGMA hoy "recuerda" nada de ejecuciones anteriores; cada
corrida del Director es una hoja en blanco. Esto es una decisión de
diseño válida para gobernanza dentro de una corrida, pero dejó
completamente sin resolver la pregunta de crecimiento operativo: cómo
SIGMA podría, por ejemplo, notar que cierto tipo de dataset dispara
`PAUSED_HITL` en `0004` con frecuencia inusual, sin que un humano tenga
que revisar Langfuse manualmente cada vez.

El riesgo central que este ADR debe resolver, no ignorar: cualquier
mecanismo de memoria que un LLM redacte libremente (el Director, vía
Gemini/Ollama) es una superficie nueva de violación de K⊆X (`ADR-008`)
— un Ag-DR mal diseñado podría convertirse en narrativa plausible pero
no verificable, exactamente lo que K⊆X existe para prohibir.

---

## Decisión

### 2.1 — Definición de Ag-DR

Un **Ag-DR** (Agent Decision Record) es un registro estructurado que un
orquestador (Director, Engineer Datos, Engineer Modelos, Engineer
Auditor) genera al finalizar una corrida, documentando **qué decisiones
tomó y sobre qué evidencia**, no arquitectura del sistema. Es al Director
lo que un ADR es al proyecto: un ADR dice "por qué elegimos LangGraph";
un Ag-DR dice "en la corrida `sigma-20260713-a1b2c3d4`, Engineer Datos
seleccionó la rama `descriptive_fallback` en `0004` porque no había
`hypothesis` ni `datetime_index` en el estado".

**Regla no negociable (vínculo con ADR-008):** un Ag-DR se construye
**exclusivamente** a partir de los campos ya estructurados que cada
skill emite vía `emit_trace_event()` (`branch_selected`, `verdict`,
`duration_ms`, `error_type`, etc.) — **nunca** a partir de texto libre
generado por el LLM del Orquestador. El LLM puede, como mucho, *dar
formato de lectura* a datos ya verificados — nunca *inventar* el
contenido del registro. Esta es la traducción operativa de K⊆X a este
nuevo artefacto.

### 2.2 — Estructura de carpetas

```
sigma/
└── memory/
    ├── director/
    │   └── {trace_id}.agdr.md
    ├── engineer_datos/
    │   └── {trace_id}.agdr.md
    ├── engineer_modelos/       ← vacío hasta Rollout 2
    │   └── {trace_id}.agdr.md
    └── engineer_auditor/       ← vacío hasta Rollout 3
        └── {trace_id}.agdr.md
```

Una carpeta propia por Engineer, tal como propuso Marx — cada Engineer
escribe únicamente en la suya, nunca en la de otro (misma regla de
aislamiento que ya rige ADR-016 §2.3, "un Engineer nunca invoca skills
de otro Engineer").

**Engineer Datos genera el Ag-DR más detallado de los cuatro** — es
quien maneja los datos de entrada, y por tanto el que más contexto
tiene para registrar (schema del dataset, resultado de `0004`, si hubo
pausa HITL y por qué).

### 2.3 — Formato: YAML (frontmatter) + Markdown

Mismo patrón ya establecido en `SKILL.md` y en los propios ADR — metadata
estructurada, parseable por código, seguida de una sección legible por
humano y, especialmente, **por el propio Director** (que necesita poder
leer sus Ag-DR anteriores sin tener que parsear Langfuse crudo):

```markdown
---
trace_id: sigma-20260713-a1b2c3d4
engineer: engineer_datos
pipeline_run_id: run-20260713-a1b2c3d4
sigma_variant: SIGMA-FE
sigma_submode: Dev
skills_ejecutados: ["0000","0001","0002","0003","0004","0008","0011"]
verdicts:
  "0004": {branch: descriptive_fallback, verdict: INSUFFICIENT_EVIDENCE}
  "0008": {pct_unclear: 12.4}
pipeline_status: success
hitl_disparado: false
operador_id: marx-001   # campo abierto, ver §2.4 — no hardcodeado a un único valor
duration_total_ms: 48210
---

## Resumen de la corrida

Engineer Datos procesó el dataset en `data/tirendaz.csv` sin incidentes.
`0004-statistical-validator` cayó en `descriptive_fallback` (sin
hipótesis, índice temporal ni feedback en vivo disponibles) y no
encontró nulos ni duplicados por encima del umbral. `0008` clasificó con
12.4% de filas `UNCLEAR`, por debajo del umbral de pausa HITL (30%).
```

La sección "Resumen de la corrida" **sí puede ser redactada por un LLM**
— pero únicamente como paráfrasis del frontmatter ya estructurado que la
precede, nunca añadiendo información que no esté en él. Esto es
verificable mecánicamente (D3 de `ADR-007`, o un chequeo nuevo de
adherencia): ningún sustantivo propio en la prosa que no aparezca también
en el YAML.

### 2.4 — Autoría, incluyendo al operador humano

Cada Ag-DR registra qué agente lo generó y bajo la autorización de qué
operador humano (campo `operador_id`). **Corrección tras revisión con
Marx:** este campo es abierto por diseño, no un valor único hardcodeado
— SIGMA es un proyecto de código abierto (GitHub, LinkedIn) y cualquier
persona que clone el repositorio corre su propia instancia como
operador único de esa instancia. `operador_id` no reabre la arquitectura
multi-operador de una sola instancia (que sigue rechazada,
`AGENTS_CREATOR.md` §1) — simplemente evita hardcodear un valor que
solo tendría sentido para la instancia de Marx.

### 2.5 — Aprobación humana como puerta antes de que un Ag-DR sea memoria confiable

**Resuelve la pregunta 2 de la Sección 6 original.** Mismo patrón que
Vibe Diff + HITL (`ADR-004`): un Ag-DR se **genera automáticamente**
tras cada corrida, pero permanece en estado `pendiente_revision` hasta
que el operador lo audite y apruebe explícitamente. Solo un Ag-DR en
estado `aprobado` puede, en el futuro, ser consultado por el Director
para informar una decisión — nunca uno `pendiente_revision`. Esto evita
que el sistema "aprenda" de una corrida defectuosa sin que un humano lo
haya validado primero.

```yaml
estado_revision: pendiente_revision   # pendiente_revision | aprobado | rechazado
revisado_por: null                    # operador_id una vez revisado
fecha_revision: null
```

### 2.6 — Lógica de decisión del Director, formalizada

A petición explícita de Marx: la lógica de enrutamiento del Director
(hoy implícita en `edge_after_engineer_datos` y funciones similares en
`director.py`) se especifica con el mismo rigor que ADR-009 exige a los
skills — **esquemas + Gherkin**, no solo código Python:

```gherkin
# language: es
Característica: Enrutamiento del Director entre Engineers

  Escenario: Rollout 1 — solo Engineer Datos existe
    Dado que el Director recibe una intención de usuario
    Y que solo Engineer Datos está registrado en Rollout 1
    Cuando el Director decide a qué Engineer delegar
    Entonces delega en Engineer Datos
    Y no considera ningún otro Engineer (ADR-016 §2.4)

  Escenario: Engineer Datos pausado en HITL
    Dado que Engineer Datos devuelve "__interrupt__"
    Cuando el Director recibe ese resultado
    Entonces propaga el interrupt sin generar un Ag-DR todavía
    Y el Ag-DR se genera solo al reanudar con una decisión definitiva
```

Más las propiedades LTL correspondientes (Safety/Liveness), mismo
patrón que cada `SKILL.md`. Este `.feature` viviría en
`sigma/core/tests/test_director_routing.feature` — pendiente de
construir cuando se redacte la versión aprobada de este ADR.

### 2.7 — Agent Cards de Workers embebidas al desincorporarse

Vínculo nuevo con ADR-019 §2.1ter: cuando un Worker (subagente efímero
para tarea específica, distinto de los Engineers permanentes) termina
su vida útil, su Agent Card completo se embebe dentro del Ag-DR de
quien lo creó — normalmente el Director. Esto es lo único que permite
auditar después *cómo y por qué* se concibió ese Worker específico; un
Worker sin este rastro no debería poder haber existido.

```yaml
workers_creados:
  - agent_card: {agent_id: worker-calculador-financiero-a1b2c3, ...}
    razon_de_creacion: "Tarea puntual sin skill existente que la cubriera"
```

Campo opcional en el frontmatter del Ag-DR — vacío en la gran mayoría
de corridas de Rollout 1, ya que el mecanismo real de creación de
Workers no está implementado todavía (ver nota de alcance en ADR-019).

### 2.8 — Enriquecimiento por juicio automático (Rollout 3), nunca sustitución del HITL determinista

Vínculo nuevo con el mecanismo de juicio automático que Engineer
Auditor construirá en Rollout 3 (candidato de diseño interno de
`0012`/`0015`, sin ADR propio todavía — se referencia aquí como
consumidor del Ag-DR, no como decisión ya tomada sobre su forma final).

**Regla no negociable:** un veredicto de juicio automático puede
**enriquecer** un Ag-DR — se adjunta como campo adicional del
frontmatter, con la misma restricción de K⊆X que ya rige el resto del
documento (2.1): el juez responde con una afirmación, si está
respaldada por el contexto, y la cita textual que lo prueba — nunca
narrativa libre sobre por qué. Un veredicto de juicio automático
**nunca puede suprimir** un disparador HITL determinista ya definido en
otro punto del sistema (el umbral de `0008`, el de `0004`, o cualquier
futuro equivalente en Engineer Modelos). Esto preserva el mismo
principio de fail-safe que ya rige el circuit breaker de
`skill_runner.py`: un mecanismo de enriquecimiento no puede degradar
una protección ya existente, solo puede añadir información para que el
operador revise más rápido.

```yaml
juicio_automatico:                  # opcional, vacío hasta Rollout 3
  veredicto: null                   # aprobado | rechazado | sin_evaluar
  afirmaciones_verificadas:
    - afirmacion: null
      respaldado: null              # true | false
      cita: null                    # fragmento textual exacto de la fuente
  suprime_hitl: false               # SIEMPRE false — campo de solo lectura,
                                     # nunca escribible por el juez mismo
```

Este campo no cambia el `estado_revision` de 2.5 — un Ag-DR con
`juicio_automatico.veredicto: aprobado` sigue naciendo en
`pendiente_revision` como cualquier otro, y sigue necesitando tu
aprobación humana explícita antes de poder informar una decisión
futura. El juez acelera tu revisión, no la reemplaza.

---

## Consecuencias

### Beneficios
- SIGMA deja de "olvidar" cada corrida — abre la puerta a detectar
  patrones (ej. "`0004` cae en `PAUSED_HITL` con frecuencia inusual con
  datasets de cierto tamaño") sin revisión manual de Langfuse.
- La lógica de decisión del Director queda auditable de la misma forma
  que cualquier skill, cerrando una inconsistencia real: hoy los skills
  tienen Gherkin obligatorio y el Director no.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Ag-DR se convierte en superficie de alucinación | Regla 2.1: construcción exclusiva desde eventos Langfuse ya estructurados |
| Acumulación sin límite de archivos `.agdr.md` | Política de retención — fuera de alcance de este borrador, pendiente de definir |
| El Director empieza a "decidir distinto" basado en Ag-DR pasados sin que eso esté auditado | Resuelto por §2.5 — solo un Ag-DR en estado `aprobado` (revisado por el operador) puede eventualmente informar una decisión futura; uno `pendiente_revision` nunca influye nada |

---

## Alternativas consideradas

| Alternativa | Por qué se descarta (por ahora) |
|---|---|
| Que el LLM del Director redacte el Ag-DR libremente | Viola K⊆X directamente — es narrativa no verificable |
| Un solo Ag-DR global, no por Engineer | Rompe el aislamiento ya establecido en ADR-016 §2.3 |
| Guardar memoria solo en Langfuse, sin archivo propio | Langfuse no está pensado para lectura humana/del Director de forma natural — motivó este ADR |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-001 | Memoria epistémica *intra*-corrida; Ag-DR es memoria *entre* corridas — complementarios, no redundantes |
| ADR-008 | K⊆X gobierna la Regla 2.1 sin excepción |
| ADR-009 | El patrón Gherkin+LTL de los skills se extiende aquí a la lógica del Director |
| ADR-011 | Ag-DR se construye a partir de los mismos eventos que Langfuse ya recibe |
| ADR-016 | Estructura de carpetas por Engineer respeta el aislamiento de la jerarquía |
| ADR-019 | El formato de "Identidad" de cada orquestador (basado en CLOE) es un ADR hermano, separado deliberadamente — ciclos de vida opuestos: Ag-DR se genera solo en cada corrida, Identidad la redacta un humano una vez y rara vez cambia |

---

## Historial de versiones

v0.1 — Primer borrador, generado a petición de Marx. No aprobado.
Pendiente de resolver 2 preguntas abiertas.

**Cambios en v1.0:**
- **a** Resuelta la pregunta de `operador_id`: campo abierto por diseño
  (proyecto de código abierto, cada clon es su propia instancia con su
  propio operador único), no reabre `AGENTS_CREATOR.md` §1.
- **b** Resuelta la pregunta de si los Ag-DR influyen decisiones
  futuras: sí, pero solo tras aprobación humana explícita (§2.5),
  mismo patrón que Vibe Diff + HITL (ADR-004).
- **c** El formato de "Identidad" por agente se separa a su propio
  ADR-019 (ciclos de vida distintos — ver tabla de relación con otros
  ADRs). Se retira la Sección 6 de este documento.
- **d** Ejemplo de frontmatter corregido al esquema de variantes
  migrado (`SIGMA-FE` + `sigma_submode`, no el `Full` heredado).
- Estado: **Propuesto**, pendiente de aprobación formal de Marx.

**Cambios en v1.1:**
- **a** Añadida la sección 2.7 — Agent Cards de Workers embebidas en el
  Ag-DR de quien los creó al desincorporarse (vínculo bidireccional con
  ADR-019 §2.1ter, agregado a petición de Marx).

**Cambios en v1.2:**
- **a** Aprobado en firme por Marx.
- **b** Añadida la sección 2.8 — regla de interacción entre el futuro
  mecanismo de juicio automático de Engineer Auditor (Rollout 3) y el
  Ag-DR: puede enriquecer, nunca puede suprimir un disparador HITL
  determinista. Decidido en la sesión de análisis de herramientas de
  producción LLM (Capital One), antes de que el mecanismo de juicio
  tenga forma de código o de ADR propio.
