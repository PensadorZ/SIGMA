---
id: ADR-002
titulo: Paralelismo Masivo Intra-Skill mediante Plantillas MapReduce
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-002 v1.3
referencias-minimas: ADR-001, ADR-009, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-002: Paralelismo Masivo Intra-Skill mediante Plantillas MapReduce

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
completo en un único worker es inviable en tiempo y en coste. Por otro,
si se resuelve de forma manual creando nodos del DAG uno por cada
partición, el diseñador del skill queda expuesto a una explosión
combinatoria de nodos según el volumen de datos de cada corrida,
volviendo el DAG imposible de razonar o mantener a medida que el
dataset crece. A esto se suma un requisito no negociable heredado de
ADR-001: la trazabilidad debe preservarse a nivel de cada worker
individual, no solo a nivel del skill completo, de modo que un fallo
parcial permita reintentar únicamente las particiones afectadas, sin
repetir el trabajo ya completado con éxito.

---

## Decisión

Extender la especificación de skills con un campo `parallelism` en el
frontmatter YAML. Cuando este campo está presente, el Orquestador genera
automáticamente los workers según la estrategia declarada.

### Fig. 1 — Flujo de las tres estrategias de paralelismo intra-skill

```
── ESTRATEGIA map_reduce ──────────────────────────────────────────
Dataset ──→ Particionador ──→ Worker-01 (chunk 1/N) ──┐
                          ──→ Worker-02 (chunk 2/N) ──┤→ Reducer ──→ Output
                          ──→ Worker-0N (chunk N/N) ──┘
            [trace_id viaja en cada fila]

── ESTRATEGIA scatter_gather ──────────────────────────────────────
Dataset ──→ Particionador ──→ Worker-01 ──→ Resultado-01 (independiente)
                          ──→ Worker-02 ──→ Resultado-02 (independiente)
                          ──→ Worker-0N ──→ Resultado-0N (independiente)

── ESTRATEGIA chain ───────────────────────────────────────────────
Dataset ──→ Worker-1 ──→ Redis List (BLPOP) ──→ Worker-2
                                           ──→ Redis List (BLPOP) ──→ Worker-3
           [stage_1]       sigma:chain:{run_id}:{skill_id}:1
                                                               [stage_2]
```

### Tab. 1 — Comparativa de estrategias de paralelismo

| Estrategia | Patrón | Caso de uso | Consideración clave |
|---|---|---|---|
| **`map_reduce`** | N workers en paralelo + reducer final | Volúmenes > 100.000 registros | Reducer debe ser idempotente; usar operaciones conmutativas o ordenar por `trace_id` |
| **`scatter_gather`** | N workers en paralelo sin reducer | Clasificaciones con particiones autónomas | Sin coordinación entre workers |
| **`chain`** | Workers en cadena secuencial con buffer Redis | Transformaciones con pasos dependientes dentro del mismo skill | Usa `BLPOP`; en Runtime requiere confirmación en `policies.yaml` |

### Propagación del `trace_id`

Cada partición lleva un `trace_id` en cada fila a lo largo de toda la cadena
de transformación. El reducer consolida los `trace_id` de las particiones que
unifica. Esto garantiza el linaje de datos requerido por ADR-001 y ADR-008.

### Estrategia `chain` — Implementación con Redis

El worker N escribe su output en una Redis List con clave
`sigma:chain:{run_id}:{skill_id}:{stage}`. El worker N+1 ejecuta `BLPOP`
sobre esa clave y se activa cuando el dato llega, sin consumir CPU en espera
activa. En variante Runtime, la estrategia `chain` requiere confirmación
explícita del operador en `policies.yaml` por implicar workers de larga
duración. Si el volumen supera la capacidad de Redis o se necesitan garantías
de entrega más fuertes, se creará un ADR-014 de mensajería avanzada.

### Comportamiento en SIGMA Dev

El campo `parallelism.workers` se sobrescribe a `1` automáticamente para
simplificar la depuración. El resto de la especificación se mantiene intacta.

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
  vida de los workers.
- El reducer debe ser determinista e idempotente.
- Los skills con `parallelism` son más difíciles de depurar sin Langfuse
  activo.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Worker único por skill | Inviable para datasets grandes |
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
