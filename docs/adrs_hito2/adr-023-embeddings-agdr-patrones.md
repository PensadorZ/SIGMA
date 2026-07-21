---
id: ADR-023
titulo: Memoria Operativa Consultable — Embeddings sobre Ag-DR para Detección de Patrones
version: 1.0
estado: Aceptado
fecha-original: 2026-07
fecha-revision: 2026-07
supersede: ninguno
referencias-minimas: ADR-008, ADR-016, ADR-018, ADR-022
milestone-de-aplicacion: Hito 3 (prospectiva) — implementación fuera del alcance de Rollout 2/3
aprobado-por: Prof. Marx A. García Delgado
nombre-archivo: adr-023-embeddings-agdr-patrones.md
---

# ADR-023: Memoria Operativa Consultable — Embeddings sobre Ag-DR para Detección de Patrones

## Resumen ejecutivo

Extensión funcional de `ADR-018`, no una decisión suelta: construye el
mecanismo que `ADR-018` prometió desde su primer borrador y nunca
implementó — *"abre la puerta a detectar patrones (ej. `0004` cae en
`PAUSED_HITL` con frecuencia inusual con datasets de cierto tamaño) sin
revisión manual de Langfuse"*. A diferencia de `ADR-022` (RAG del
Director, consumo humano vía conversación), este índice es
**agente-facing** — lo consultan Director y Engineer Auditor, no tú
directamente.

---

## Contexto

Hoy, si `0004` empieza a caer en `PAUSED_HITL` con más frecuencia de lo
normal para cierto tipo de dataset, la única forma de notarlo es que tú
lo detectes revisando Langfuse manualmente — exactamente lo que
`ADR-018` identificó como el problema a resolver, sin construir nunca
el mecanismo. Los Ag-DR ya contienen la información estructurada
necesaria (`verdicts`, `hitl_disparado`, `skills_ejecutados`); falta la
capa de búsqueda por similitud que permita encontrar "situaciones
parecidas a esta" en vez de solo "el Ag-DR con este `trace_id` exacto".

---

## Decisión

### 2.1 — Ubicación del módulo, separado de ADR-022 por consumidor y por dato

```
sigma/
└── memory/
    ├── rag/                  # ADR-022, humano-facing, documentos estáticos
    └── agdr_index/           # este ADR, agente-facing, Ag-DR dinámicos
        ├── indexer.py        # corre tras cada Ag-DR aprobado
        ├── pattern_query.py  # interfaz de consulta para Director/Engineer Auditor
        └── chroma_data/
```

Mismo stack técnico que `ADR-022` (Chroma + `sentence-transformers`
local, $0 en `SIGMA-FE`) — pero consumidor y ciclo de actualización
distintos, por eso es un módulo separado, no una carpeta compartida.

### 2.2 — Regla dura: solo se indexa un Ag-DR en estado `aprobado`

**No negociable, hereda directamente de `ADR-018` §2.5.** `indexer.py`
se dispara únicamente cuando un Ag-DR pasa de `pendiente_revision` a
`aprobado` — nunca antes. Indexar un Ag-DR sin tu revisión sería
exactamente el escenario que `ADR-018` §2.5 existe para prevenir: el
sistema "aprendiendo" de una corrida que nadie validó.

```yaml
# Disparador de indexer.py
on_agdr_state_change:
  from: pendiente_revision
  to: aprobado
  action: index_embedding
# cualquier otra transición (a rechazado, o ya indexado) no dispara nada
```

### 2.3 — Quién consulta, y para qué

| Consumidor | Uso |
|---|---|
| Director | `pattern_query.py` durante `research_mode` (`ADR-019` §2.9) — "¿esta situación ya ocurrió antes bajo condiciones parecidas?" |
| Engineer Auditor (Rollout 3) | Candidata a herramienta del futuro mecanismo de juicio automático (`ADR-018` §2.8) — el juez puede consultar precedentes antes de emitir un veredicto, sin que eso implique que este ADR define el juez mismo |

El Juez no tiene ADR propio a la fecha de este documento — este índice
es una herramienta disponible por referencia cruzada, no una fusión de
alcance.

### 2.4 — Cumplimiento de K⊆X

Igual que en `ADR-022`: cualquier síntesis que Director o Engineer
Auditor generen a partir de resultados de este índice debe citar
`trace_id` y campos concretos de los Ag-DR recuperados — nunca una
narrativa agregada sin anclaje verificable. Un patrón detectado
("`0004` pausa con frecuencia inusual") debe poder señalarse a una
lista concreta de `trace_id`, no a una impresión general del modelo.

---

## Consecuencias

### Beneficios
- Cierra el hueco funcional que `ADR-018` dejó abierto desde su primer
  borrador — con mecanismo real, no solo la intención declarada.
- Reusa infraestructura ya aprobada en `ADR-022` (mismo stack) sin
  mezclar responsabilidades de consumidor.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| El índice crece sin límite con el tiempo | Misma política de retención pendiente de definir que `ADR-018` ya dejó como riesgo abierto — no se resuelve aquí, se hereda |
| Un patrón falso positivo (similitud vectorial sin relación causal real) | 2.4 — cualquier patrón debe anclarse a `trace_id` concretos, verificables por un humano, nunca aceptarse solo por score de similitud |

---

## Alternativas consideradas

| Alternativa | Por qué se descarta |
|---|---|
| Fusionar este módulo con `ADR-022` | Mezclaría consumidor humano-facing con agente-facing, y dato estático con dinámico — dos responsabilidades distintas |
| Dar al Juez su propio ADR ya, incluyendo este índice como parte de él | Prematuro — el Juez todavía no tiene forma de código; se decide su ADR (si lo necesita) cuando Rollout 3 lo construya de verdad |
| Indexar también Ag-DR `pendiente_revision`, con flag de baja confianza | Rechazada — cualquier grado de influencia de un Ag-DR no aprobado contradice `ADR-018` §2.5 sin excepción |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-008 | K⊆X gobierna la Regla 2.4 sin excepción |
| ADR-016 | Engineer Auditor es consumidor previsto, sin invadir el aislamiento Engineer↔Engineer |
| ADR-018 | Extensión funcional directa — este ADR construye lo que 018 dejó como beneficio prometido, no implementado |
| ADR-022 | ADR hermano — mismo stack técnico, consumidor y ciclo de dato distintos |

---

## Historial de versiones

v1.0 — Primera versión, aprobada por Marx en la misma sesión en que se
propuso, junto con `ADR-022`. Alcance de implementación explícitamente
prospectivo (Hito 3) — el diseño se acepta ahora, el código no se
construye antes de que Rollout 3 cierre.
