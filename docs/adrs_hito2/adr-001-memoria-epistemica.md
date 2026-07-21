---
id: ADR-001
titulo: Memoria Epistémica basada en Feature Store y Grafo de Suposiciones
version: 1.6
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-001 v1.5
referencias-minimas: ADR-002, ADR-008, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-001: Memoria Epistémica basada en Feature Store y Grafo de Suposiciones

## Resumen ejecutivo de cambios v1.6

Dos correcciones reales (Hito 2, cierre de Rollout 1): "worker" se
renombra a "nodo de cómputo" en Fig. 1 y en el texto (consistente con
el ADR-002 de origen, ya corregido) — este documento es de los que
todavía usaba el término viejo. Tab. 1 corregida al esquema real de
variantes de costo (SIGMA-FE/LE/ME/HE) separado de submodo (Dev/Runtime).

## Resumen ejecutivo de cambios v1.5

Se amplía la sección de Contexto para establecer explícitamente qué es
la Memoria Epistémica y por qué existe dentro del ecosistema SIGMA más
amplio — específicamente, su rol como fundamento operativo de la
Contención Epistémica K ⊆ X (ADR-008) — en vez de abrir directamente
con el problema técnico. Se agrega una nota conceptual de referencia
cruzada al final de la sección Decisión, señalando un marco teórico
personal paralelo que el autor está desarrollando (Zeugmatización
epistemológica), explícitamente delimitado como fuera del alcance
técnico de este ADR.

## Resumen ejecutivo de cambios v1.4

Se declara el KS-test como **único método autorizado** de detección de drift,
documentando el rechazo formal de PSI (Population Stability Index) tras la
evaluación realizada durante el Hito 1. Cambio menor sin impacto en
compatibilidad.

---

## Contexto

## Contexto

SIGMA opera como un ecosistema de agentes autónomos que ejecutan pipelines
de forma recurrente, no como un script de una sola corrida. Para que esa
autonomía sea confiable —y no una fuente de alucinación acumulada— el
sistema necesita memoria persistente entre ejecuciones: sin ella, cada
corrida reaprendería desde cero lo que ya se sabe sobre una entidad, y no
habría forma de detectar cuándo su comportamiento cambia con el tiempo.
Esta memoria es, además, el fundamento operativo de la Contención
Epistémica K ⊆ X (ADR-008): un agente solo puede afirmar lo que puede
trazar hasta un dato observado, y eso exige un mecanismo real donde ese
dato observado quede almacenado y sea consultable.

El problema de diseño central es que existen dos categorías de
conocimiento fundamentalmente distintas, y tratarlas como si fueran una
sola introduce ambigüedad semántica real:

- **Hechos verificados:** perfiles de usuario, métricas históricas,
  características estables de entidades. Conocimiento monótono — una vez
  confirmado, solo se actualiza, nunca se refuta.
- **Suposiciones de negocio:** hipótesis sobre comportamiento, inferencias
  del modelo. Conocimiento no monótono — pueden ser refutadas por nueva
  evidencia sin que eso invalide el historial de por qué se creyeron en
  su momento.

Un almacenamiento único y homogéneo no puede servir bien a ambas
categorías a la vez: forzar suposiciones refutables dentro de la misma
estructura que hechos verificados, o viceversa, produce o bien pérdida de
trazabilidad histórica, o bien sobre-ingeniería innecesaria para datos
que nunca cambian. Un JSON plano por ejecución, la alternativa más
simple, tampoco resuelve el problema de fondo: no escala más allá de un
millón de entidades, no permite re-evaluación automática de suposiciones
antiguas, y no ofrece ninguna trazabilidad temporal de cambios de opinión.

---

## Decisión

### Fig. 1 — Arquitectura de la Memoria Epistémica

```
Entidades externas
        │
        ├─ Hechos verificados ──────→ Feature Store (PostgreSQL)
        │                              └─ entity_features
        │                                 (entity_id, feature_key,
        │                                  value, valid_from, valid_to)
        │
        └─ Creencias inferidas ─────→ Grafo de Suposiciones
                                       └─ JSON versionado + NetworkX
                                          Estados: PROPOSED → ACTIVE
                                                   → CONFLICT → KNOWN
                                                   → REFUTED

Durante pipeline paralelo (MapReduce):
  Nodo-N ──→ Redis List (sigma:graph:updates:{run_id})
                    │
                    ▼
              Nodo Serializador (Orquestador)
                    │
                    ▼
              Grafo de Suposiciones (escritura serializada FIFO)
                    │
                    ▼
              JSON versionado (persistencia al terminar el pipeline)

Modo lectura: nodos de cómputo acceden directamente al grafo (sin cola)
```

### Tab. 1 — Implementación del Feature Store por variante

**Corregido (Hito 2):** la tabla original mezclaba costo y submodo en
las mismas filas. Se separa en dos ejes reales, consistente con el resto
del proyecto.

| Variante de costo | Backend | Coste adicional | Requisito de configuración |
|---|---|---|---|
| **SIGMA-FE** | PostgreSQL con particionado temporal | Sin coste de licencia | Índice temporal manual |
| **SIGMA-LE** | PostgreSQL con particionado temporal | Sin coste de licencia | Índice temporal manual |
| **SIGMA-ME** | Bigtable o DynamoDB (adaptador `FeatureStoreClient`) | Coste por operación | Credenciales cloud |
| **SIGMA-HE** | Bigtable o DynamoDB, mayor capacidad reservada | Coste por operación, escalado | Credenciales cloud |

**Submodo Dev (cualquier variante):** PostgreSQL con datos sintéticos,
idéntico al backend de la variante activa en Runtime, sin coste
adicional. **Submodo Runtime:** backend real según la tabla de arriba.

### Componente 1 — Feature Store temporal

Almacena hechos verificados con versionado histórico. En SIGMA-FE/LE usa
PostgreSQL con tabla `entity_features` con campos `entity_id`, `feature_key`,
`value`, `valid_from`, `valid_to`. La interfaz `FeatureStoreClient` abstrae
el backend, lo que permite migrar de SIGMA-FE/LE a SIGMA-ME/HE sin modificar
los skills.

### Componente 2 — Grafo de Suposiciones

Almacena creencias inferidas con transiciones de estado explícitas.

### Fig. 2 — Ciclo de vida de una suposición

```
         evidencia disponible
PROPOSED ──────────────────→ ACTIVE ──→ KNOWN
                                │        (múltiples evidencias
                                │         independientes)
                                ▼
                            CONFLICT ──→ ACTIVE (resuelta)
                                │
                                ▼
                            REFUTED (terminal — se conserva
                                     para auditoría con fecha
                                     de refutación)
```

**En SIGMA-FE/LE:** JSON versionado por entidad más NetworkX en memoria.
**En SIGMA-ME/HE:** Neo4j AuraDB mediante adaptador `GraphClient`.

### Escritura serializada durante pipelines paralelos

Durante una ejecución activa con nodos de cómputo de MapReduce (ADR-002), los nodos encolan
peticiones en una Redis List con clave `sigma:graph:updates:{run_id}`. Un
nodo serializador único en el Orquestador consume la cola en orden FIFO y
aplica las actualizaciones. Al terminar, el grafo se persiste en JSON
versionado. Esto resuelve la condición de carrera entre ADR-001 y ADR-002.

### Linaje de datos

Cada fila procesada lleva un `trace_id` que permite rastrear su origen y
transformaciones. Sin linaje, `K ⊆ X` es verificable solo a nivel de schema,
no a nivel de dato individual. Ver ADR-008.

### Drift estadístico

Cuando el Feature Store detecta desviación en la distribución de un lote
entrante, el pipeline genera una alerta de nivel `MEDIUM` al Approval Endpoint
y registra el evento en Langfuse (ver ADR-011). El operador decide si continuar
o pausar. El skill `statistical-validator` (0004) implementa el algoritmo de
detección usando **KS-test como único método autorizado**, con umbral
configurable en `policies.yaml` (no en `defaults.yaml`). PSI (Population
Stability Index) fue evaluado durante el Hito 1 y **rechazado formalmente**:
requiere binning arbitrario que introduce sensibilidad a la elección de
intervalos, mientras que el KS-test opera sobre la distribución empírica
completa sin parámetros de discretización.

---

> **Nota conceptual (fuera del alcance técnico de este ADR):** la
> separación entre hechos verificados (Componente 1) y suposiciones de
> negocio (Componente 2) guarda un paralelismo con un marco teórico
> personal en desarrollo del autor — la Zeugmatización epistemológica —
> donde el plano Qué-Cómo (Platónico) corresponde a hechos concretos y
> el plano Qué-Por qué (Socrático) corresponde al manejo de
> incertidumbre e hipótesis. Esta nota es una referencia cruzada, no un
> requisito: el ADR es completo y verificable sin conocer ese marco, y
> su desarrollo formal vive fuera de la documentación técnica de SIGMA.

## Consecuencias positivas

- La separación de hechos y suposiciones elimina ambigüedad semántica.
- El versionado temporal permite detectar drift de comportamiento.
- El Grafo de Suposiciones preserva el razonamiento histórico del sistema.
- La interfaz abstracta permite migrar entre variantes sin modificar los skills.
- La cola Redis resuelve la concurrencia sin añadir nuevas dependencias al stack.

## Consecuencias negativas

- Dos sistemas de almacenamiento aumentan la complejidad operacional,
  independientemente de la variante de costo activa.
- Las consultas que cruzan hechos y suposiciones requieren una capa de
  orquestación adicional (`EpistemicQueryRouter`).
- El versionado en JSON tiene límites de escala más allá de 100.000 entidades.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| JSON único por workflow | No escala; no permite re-evaluación automática |
| Base de datos de documentos (MongoDB) | Sin semántica de grafo nativa |
| Memoria solo en contexto del LLM | Volátil; limitada por ventana de contexto |
| Redis como única memoria | Inadecuado para consultas temporales complejas |
| PSI (Population Stability Index) para drift | Requiere binning arbitrario; sensible a la elección de intervalos. KS-test opera sobre la distribución empírica completa. Rechazado en el Hito 1 |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se añadió modo de escritura serializada vía Redis durante
  pipelines paralelos para resolver la condición de carrera con ADR-002.
- **b.1.2** Se incorporó el linaje de datos como requisito de implementación
  de K ⊆ X.
- **c.1.2** Se añadió el mecanismo de disparo ante detección de drift
  estadístico.

**Cambios en v1.3:**
- **a.1.3** Se añadió Fig. 1 con el diagrama de arquitectura de memoria.
- **b.1.3** Se añadió Fig. 2 con el ciclo de vida de una suposición.
- **c.1.3** Se añadió Tab. 1 con la implementación por variante del Feature Store.
- **d.1.3** Se añadió referencia concreta al skill `statistical-validator`
  para la implementación del KS-test.

**Cambios en v1.4:**
- **a** Se declaró el KS-test como único método autorizado de detección de
  drift, con umbral en `policies.yaml`.
- **b** Se documentó el rechazo formal de PSI en Alternativas Consideradas,
  con la justificación técnica verificada durante el Hito 1.

**Cambios en v1.6 (Hito 2, cierre de Rollout 1):**
- **a** "worker" renombrado a "nodo de cómputo" en Fig. 1 y en el texto
  — consistente con ADR-002 (ya corregido en esta sesión).
- **b** Tab. 1 corregida a los 4 niveles reales de variante de costo,
  separados del submodo Dev/Runtime.
