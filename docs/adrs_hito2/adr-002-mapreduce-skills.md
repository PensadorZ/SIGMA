---
id: ADR-002
titulo: Paralelismo Masivo Intra-Skill mediante Plantillas MapReduce
version: 1.5
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-002 v1.4
referencias-minimas: ADR-001, ADR-003, ADR-009, ADR-011, ADR-017
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-002: Paralelismo Masivo Intra-Skill mediante Plantillas MapReduce

## Resumen ejecutivo de cambios v1.5

Tres correcciones reales, verificadas contra el estado actual del
proyecto (Hito 2, cierre de Rollout 1): (1) "worker" se renombra a
**"nodo de cómputo"** en todo el documento — este es el ADR de origen
del término que `ADR-003` ya tuvo que corregir por colisión con
"Worker" de `ADR-019` (subagente efímero, concepto distinto); (2)
"variante Runtime"/"SIGMA Dev" se corrigen a **submodo** — Runtime y Dev
son submodos transversales, no variantes de costo, desde la migración
de esquema ya aplicada en el resto del proyecto; (3) **colisión de
numeración real**: este documento reservaba "ADR-014" para un futuro
ADR de mensajería avanzada — ese número ya está tomado por "Generación
Dinámica de Nuevos Skills" (aprobado después). Se corrige la referencia
al siguiente número disponible.

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para abrir con qué es este mecanismo y
por qué existe en el ecosistema — como extensión de la especificación
de skills (ADR-009) — antes de entrar al problema técnico de
particionado, haciendo explícita su conexión con el requisito de
trazabilidad heredado de ADR-001.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el diagrama de flujo de las tres estrategias. Se añade
Tab. 1 con la comparativa de estrategias. Se precisa que el reducer debe
usar operaciones conmutativas o un orden explícito por `trace_id` para
garantizar determinismo. Se incorpora el histórico de versiones.

---

## Contexto

## Contexto

SIGMA ejecuta skills sobre datasets que pueden alcanzar volúmenes de más
de un millón de registros — el caso de uso de referencia (WC2026-Tweets)
es el ejemplo concreto. Sin un mecanismo de paralelización nativo en la
especificación de skills (ADR-009), cada skill que necesitara procesar
ese volumen tendría que implementar su propia lógica de particionado y
coordinación desde cero, duplicando esfuerzo entre skills y arriesgando
a que cada implementación resuelva el problema de forma distinta — o,
peor, que alguna directamente no escale y falle en producción sin
previo aviso.

El problema de diseño es doble. Por un lado, procesar el dataset
completo en un único nodo de cómputo es inviable en tiempo y en coste.
Por otro, si se resuelve de forma manual creando nodos del DAG uno por
cada partición, el diseñador del skill queda expuesto a una explosión
combinatoria de nodos según el volumen de datos de cada corrida,
volviendo el DAG imposible de razonar o mantener a medida que el
dataset crece. A esto se suma un requisito no negociable heredado de
ADR-001: la trazabilidad debe preservarse a nivel de cada nodo de
cómputo individual, no solo a nivel del skill completo, de modo que un
fallo parcial permita reintentar únicamente las particiones afectadas,
sin repetir el trabajo ya completado con éxito.

---

## Decisión

Extender la especificación de skills con un campo `parallelism` en el
frontmatter YAML. Cuando este campo está presente, el Orquestador genera
automáticamente los nodos de cómputo según la estrategia declarada.

### Fig. 1 — Flujo de las tres estrategias de paralelismo intra-skill

```
── ESTRATEGIA map_reduce ──────────────────────────────────────────
Dataset ──→ Particionador ──→ Nodo-01 (chunk 1/N) ──┐
                          ──→ Nodo-02 (chunk 2/N) ──┤→ Reducer ──→ Output
                          ──→ Nodo-0N (chunk N/N) ──┘
            [trace_id viaja en cada fila]

── ESTRATEGIA scatter_gather ──────────────────────────────────────
Dataset ──→ Particionador ──→ Nodo-01 ──→ Resultado-01 (independiente)
                          ──→ Nodo-02 ──→ Resultado-02 (independiente)
                          ──→ Nodo-0N ──→ Resultado-0N (independiente)

── ESTRATEGIA chain ───────────────────────────────────────────────
Dataset ──→ Nodo-1 ──→ Redis List (BLPOP) ──→ Nodo-2
                                        ──→ Redis List (BLPOP) ──→ Nodo-3
           [stage_1]       sigma:chain:{run_id}:{skill_id}:1
                                                               [stage_2]
```

### Tab. 1 — Comparativa de estrategias de paralelismo

| Estrategia | Patrón | Caso de uso | Consideración clave |
|---|---|---|---|
| **`map_reduce`** | N nodos de cómputo en paralelo + reducer final | Volúmenes > 100.000 registros | Reducer debe ser idempotente; usar operaciones conmutativas o ordenar por `trace_id` |
| **`scatter_gather`** | N nodos de cómputo en paralelo sin reducer | Clasificaciones con particiones autónomas | Sin coordinación entre nodos |
| **`chain`** | Nodos de cómputo en cadena secuencial con buffer Redis | Transformaciones con pasos dependientes dentro del mismo skill | Usa `BLPOP`; en submodo Runtime requiere confirmación en `policies.yaml` |

### Propagación del `trace_id`

Cada partición lleva un `trace_id` en cada fila a lo largo de toda la cadena
de transformación. El reducer consolida los `trace_id` de las particiones que
unifica. Esto garantiza el linaje de datos requerido por ADR-001 y ADR-008.

### Estrategia `chain` — Implementación con Redis

El nodo de cómputo N escribe su output en una Redis List con clave
`sigma:chain:{run_id}:{skill_id}:{stage}`. El nodo de cómputo N+1
ejecuta `BLPOP` sobre esa clave y se activa cuando el dato llega, sin
consumir CPU en espera activa. En submodo Runtime, la estrategia
`chain` requiere confirmación explícita del operador en `policies.yaml`
por implicar nodos de cómputo de larga duración. Si el volumen supera
la capacidad de Redis o se necesitan garantías de entrega más fuertes,
se creará un **ADR futuro de mensajería avanzada** — **corregido**: el
número original reservado (`ADR-014`) ya está tomado por "Generación
Dinámica de Nuevos Skills" (aprobado con posterioridad a este
documento); el próximo ADR disponible al momento de esta revisión es
`ADR-020`, pero el número definitivo se asigna cuando ese ADR se
redacte de verdad, no se reserva por adelantado otra vez — ya vimos con
este mismo error las consecuencias de reservar números sin construir.

**Vínculo con ADR-003 (AgBOM):** cada nodo de cómputo, en cualquiera de
las tres estrategias, emite el evento AgBOM al iniciar
(`{model_hash, dependency_hashes, compute_node_id}`) — mismo mecanismo
que el Blue Team ya verifica, sin distinción por estrategia de
paralelismo.

### Comportamiento en submodo Dev

El campo `parallelism.compute_nodes` (renombrado desde `parallelism.
workers` — ningún skill de Rollout 1 lo usaba todavía, cambio seguro)
se sobrescribe a `1` automáticamente para simplificar la depuración. El
resto de la especificación se mantiene intacta.

---

## Consecuencias positivas

- El diseñador escribe una sola definición y el Orquestador gestiona la
  paralelización.
- La trazabilidad granular permite reintentos quirúrgicos de solo las
  particiones fallidas.
- El campo `parallelism` es opcional: los skills sin él funcionan igual
  que antes.
- La estrategia `chain` no añade nuevas dependencias al stack porque Redis
  ya existe.

## Consecuencias negativas

- El Orquestador asume responsabilidad adicional en la gestión del ciclo de
  vida de los nodos de cómputo.
- El reducer debe ser determinista e idempotente.
- Los skills con `parallelism` son más difíciles de depurar sin Langfuse
  activo.

**Vínculo con ADR-017 (sandboxing):** los nodos de cómputo de este ADR
**no** entran en el alcance del sandboxing obligatorio — son parte de
skills de autoría humana (Rollout 1/2), no código generado dinámicamente
ni Workers efímeros (`ADR-019`). Mismo criterio que `ADR-017` §2.1 ya
establece explícitamente.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Nodo de cómputo único por skill | Inviable para datasets grandes |
| Nodos manuales por partición | Explosión combinatoria; skills imposibles de mantener |
| Celery o Ray como scheduler | Dependencias de infraestructura no justificadas |
| Kafka para la estrategia `chain` | Reservado para ADR futuro si el volumen lo exige |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se renombró la estrategia `pipeline` a `chain` para evitar
  ambigüedad con el concepto de pipeline de Data Science.
- **b.1.2** Se especificó la implementación de `chain` con `BLPOP` de Redis
  como buffer entre workers encadenados.
- **c.1.2** Se añadió la propagación del `trace_id` por fila para linaje
  de datos.
- **d.1.2** Se estableció que la estrategia `chain` en variante Runtime
  requiere confirmación explícita del operador.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el diagrama de flujo de las tres estrategias.
- **b** Se añadió Tab. 1 con la comparativa de estrategias.
- **c** Se precisó que el reducer debe usar operaciones conmutativas o un
  orden explícito por `trace_id` para garantizar determinismo.

**Cambios en v1.5 (Hito 2, cierre de Rollout 1):**
- **a** "worker" renombrado a "nodo de cómputo" en todo el documento —
  este es el ADR de origen del término, corregido para no colisionar
  con "Worker" de `ADR-019` (concepto distinto, subagente efímero).
  Campo `parallelism.workers` renombrado a `parallelism.compute_nodes`.
- **b** "variante Runtime"/"SIGMA Dev" corregidos a submodo Runtime/Dev,
  consistente con la migración de esquema de variantes ya aplicada en
  el resto del proyecto.
- **c** Corregida la colisión de numeración: el "ADR-014 de mensajería
  avanzada" que este documento reservaba ya está tomado por
  "Generación Dinámica de Nuevos Skills" — ya no se reserva un número
  por adelantado, se asignará cuando ese ADR se redacte de verdad.
- **d** Añadidos vínculos formales con ADR-003 (AgBOM, cada nodo de
  cómputo lo emite) y ADR-017 (los nodos de cómputo quedan
  explícitamente fuera del alcance del sandboxing obligatorio, por ser
  parte de skills de autoría humana).
