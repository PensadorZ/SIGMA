---
id: ADR-016
titulo: Orquestación Jerárquica de Tres Orquestadores (Director/Engineer/Auditor)
version: 1.3
estado: Aceptado
fecha-original: 2026-07
fecha-revision: 2026-07
supersede: ADR-016 v1.0
referencias-minimas: ADR-002, ADR-003, ADR-009, ADR-011, ADR-013
hito-de-aplicacion: Hito 2
aprobado-por: Prof. Marx A. García Delgado
nombre-archivo: adr-016-orquestacion-jerarquica.md
---

# ADR-016: Orquestación Jerárquica de Tres Orquestadores (Director/Engineer/Auditor)

## Resumen ejecutivo de cambios v1.3

Se corrige un hueco real detectado al preparar el código de Rollout 1:
`0008-sentiment-analyzer` y `0011-viz-reporter` — los dos skills con
código real y tests pasando desde Hito 1 — no aparecían asignados a
ningún Engineer en la Fig. 1 ni en la Tab. 2. Se reasignan a Engineer
Datos, que pasa a cubrir `0000-0004, 0008, 0011`. Sin esta corrección,
el Director de Rollout 1 no habría podido ejecutar análisis de
sentimiento ni generar el dashboard — el resultado visible de correr
SIGMA.

## Resumen ejecutivo de cambios v1.2

Se añade la sección 2.4 con el plan de implementación por Rollouts (1/2/3),
resolviendo la ambigüedad de secuencia que la v1.1 dejaba implícita. Cada
Rollout declara su condición de salida verificable y sus dependencias de
código real pendientes, evitando que la jerarquía completa se dé por
construida cuando en realidad solo un subgrafo existe.

## Resumen ejecutivo de cambios v1.1

Se amplía la sección de Contexto para explicar primero que este ADR
cumple una doble función — formaliza retroactivamente a LangGraph como
motor y define la gobernanza del Hito 2 — antes de entrar al detalle de
la jerarquía de tres orquestadores.

## Resumen ejecutivo

Este ADR formaliza la decisión ya aprobada en diseño (conversación "Eco
MultiAgentes Sigma 3 (Hito 1)") de que el Hito 2 adopta una **arquitectura
jerárquica de tres orquestadores** mediante subgrafos de LangGraph, bajo el
patrón Director/Engineer/Auditor. Su redacción quedó pendiente como deuda 
documental; este ADR la salda. Aprovecha además para registrar formalmente 
la decisión que ningún ADR anterior respaldaba: **LangGraph como motor de 
orquestación del ecosistema** — resolviendo la referencia pendiente detectada 
en la auditoría del ADR-015.

---

## Contexto

Este ADR cumple una doble función poco común: resuelve retroactivamente
una decisión técnica que ya estaba en uso de facto desde el Hito 1
(LangGraph como motor), y al mismo tiempo define la arquitectura de
gobernanza para el Hito 2. Es, en ese sentido, el ADR que estabiliza el
terreno bajo el resto del ecosistema — sin la formalización de LangGraph
aquí, cada ADR que menciona `interrupt()`, checkpointers o subgrafos
(ADR-004, ADR-002, ADR-015) descansaría sobre una elección de tecnología
nunca justificada por escrito.

El Hito 1 opera con un único orquestador (SupervisorAgent en LangGraph)
que gestiona un pipeline lineal de 6 skills. El Hito 2 incorpora 9
skills adicionales (0005–0007, 0009–0010, 0012–0015) que incluyen
entrenamiento ML/DL, explicabilidad, HITL avanzado e inspección —
dominios con trayectorias, tiempos de ejecución y necesidades de
supervisión radicalmente distintas.

Un orquestador único plano tendría que conocer los detalles de los 15
skills, sus dependencias cruzadas y sus políticas de reintento — un
monolito de decisión que crece cuadráticamente en complejidad con cada
skill nuevo.

Adicionalmente, la auditoría del ADR-015 detectó que ninguna decisión
formal respaldaba la elección de LangGraph: se usaba de facto desde el
Hito 1 sin ADR que la justificara. Este documento la registra.

---

## Decisión

### 2.1 — Decisión de base: LangGraph como motor de orquestación

Se formaliza LangGraph (licencia MIT, ecosistema LangChain) como el motor de
orquestación de SIGMA para todos los Hitos, con base en la evidencia del
Hito 1:

- Grafo de estados tipado (`PipelineState`) con validación en cada transición.
- Checkpointing nativo (`SqliteSaver`) que habilita el HITL por
  `interrupt()` verificado en ADR-004 v1.5.
- Bordes condicionales que implementan el circuit breaker con fallo rápido:
  el DAG se cortocircuita en cuanto `pipeline_status == 'failed'`.
- Subgrafos como mecanismo de composición — la base técnica de este ADR.

### 2.2 — Los tres orquestadores

**Fig. 1 — Jerarquía de orquestación del Hito 2**

```
                ORQUESTADOR DIRECTOR (nivel 0)
                ├─ Recibe la intención del usuario
                ├─ Descompone en fases y asigna a Engineers
                ├─ Único punto de contacto con HITL global (ADR-004)
                └─ Consolida resultados y evalúa 7D (ADR-007)
                       │
        ┌──────────────┼──────────────────┐
        ▼              ▼                  ▼
ENGINEER DATOS       ENGINEER MODELOS   ENGINEER AUDITOR
(subgrafo 1)         (subgrafo 2)       (subgrafo 3)
skills:              skills:            skills:
0000-0004, 0008,     0005-0007,         0012-0015
0011                 0009-0010          (inspector,
(pipeline batch      (trainers ML/DL,    explainability,
 core + sentimiento   HITL avanzado)     auditoría)
 + dashboard)
```

Cada Engineer es un **subgrafo LangGraph completo** con su propio
checkpointer, sus propios nodos de error y su propia política de reintentos.
El Director solo conoce el contrato de entrada/salida de cada Engineer, no
sus skills internos.

### 2.3 — Reglas de la jerarquía

**Tab. 1 — Reparto de responsabilidades**

| Responsabilidad | Director | Engineer |
|---|---|---|
| Interpretar la intención del usuario | ✅ | ⛔ |
| Conocer los skills individuales | ⛔ | ✅ (solo los suyos) |
| Escalar a HITL global | ✅ | ⛔ (escala al Director) |
| Reintentos intra-fase | ⛔ | ✅ |
| Evaluación 7D final | ✅ | ⛔ (emite métricas parciales) |
| Trazabilidad Langfuse | Trace padre | Span hijo por subgrafo (ADR-011) |

Reglas no negociables:

1. Un Engineer **nunca** invoca skills de otro Engineer. Si necesita su
   output, lo solicita al Director.
2. El fallo de un Engineer no derriba a los demás: el Director decide si
   continuar en modo degradado o abortar (coherente con el circuit breaker).
3. El equipo Red/Blue/Green (ADR-003) opera a nivel del Director; los
   Engineers emiten eventos AgBOM como cualquier worker.
4. La restricción K ⊆ X (ADR-008) y el protocolo de siete artefactos
   (ADR-009 v1.5) aplican sin excepciones dentro de cada subgrafo.

### 2.4 — Plan de implementación por Rollouts

El Director nunca conoce Engineers que aún no existen — en Rollout 1, su
lógica de enrutamiento solo contempla un destino posible. Esto evita
construir código de coordinación especulativo para Engineers que todavía
no están escritos, coherente con la restricción K⊆X (ADR-008) aplicada al
propio diseño del sistema, no solo a los datos que procesa.

**Tab. 2 — Rollouts de la jerarquía de tres orquestadores**

| Rollout | Se construye | Skills pendientes de verificar en código real | Condición de salida |
|---|---|---|---|
| **Rollout 1** | Director mínimo viable + subgrafo Engineer Datos (`0000-0004, 0008, 0011`) | `0004-statistical-validator` — spec corregida (v1.0.1), `skill.py` sin confirmar. `0000-0003, 0008, 0011` ya tienen código real y tests pasando desde Hito 1 | (a) Suite pytest-bdd de Engineer Datos en verde completa, incluyendo `0008` y `0011` · (b) 3 corridas reales consecutivas sin fallo vía Director, no solo 1 · (c) circuit breaker probado explícitamente: al menos 1 corrida con fallo no recuperable forzado, verificando fast-fail correcto · (d) traza Langfuse completa: trace padre (Director) + span hijo (Engineer Datos) verificado end-to-end, incluyendo el evento `viz-reporter.success` |
| **Rollout 2** | Se añade Engineer Modelos como segundo subgrafo | `0005-framework-selector`, `0006-ml-trainer`, `0007-dl-trainer`, `0009-cluster-analyzer`, `0010-engagement-calculator` — todos ⬜ pendientes, ninguno con código | (a) Engineer Modelos pasa su propia suite aislada, sin el Director, antes de conectarse · (b) contrato de entrada Engineer Datos → Engineer Modelos probado explícitamente (output de Datos consumible sin transformación manual) · (c) al menos 1 corrida real con los dos Engineers coordinados · (d) se verifica en vivo la regla no negociable de la sección 2.3: un fallo en Engineer Modelos no derriba a Engineer Datos |
| **Rollout 3** | Se añade Engineer Auditor, jerarquía completa | `0012-code-reviewer`, `0013-skill-discovery`, `0014-stride-modeling`, `0015-pipeline-inspector` — todos pendientes; `0015` además requiere resolver su alcance (LLM sobre Langfuse vs. query engine sobre Redis) antes de escribir su SKILL.md | (a) Engineer Auditor pasa su suite aislada · (b) los 3 Engineers coordinados producen la evaluación 7D completa (ADR-007) generada por el Director · (c) ADR-017 (sandboxing, pendiente de redactar) debe estar aprobado y aplicado a Engineer Auditor antes de esta fase, porque la auditoría es el punto con mayor probabilidad de disparar generación dinámica de skills (ADR-014) |

**Nota sobre ADR-017:** el sandboxing existía en las iteraciones previas del
proyecto (contenedores efímeros Docker/gVisor) pero no sobrevivió a la
consolidación en los 16 ADRs actuales. Se redacta como ADR nuevo, no como
extensión de ADR-003, porque su alcance — contención de la *ejecución* de
código generado — es ortogonal a la detección de amenazas que ADR-003 ya
cubre; forzarlo dentro de ADR-003 mezclaría dos responsabilidades distintas
bajo un mismo documento.

---

## Consecuencias

### Beneficios

- La complejidad de decisión crece linealmente por Engineer, no
  cuadráticamente por skill.
- Los subgrafos son testables de forma aislada — cada Engineer tiene su
  propia suite pytest-bdd.
- El patrón habilita el Hito 3: el grafo de streaming (ADR-015) se integra
  como un cuarto subgrafo par, sin tocar los otros tres.

### Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Latencia adicional por la capa de coordinación | Los contratos Director↔Engineer son síncronos y ligeros; el overhead medido debe reportarse en D4 (ADR-007) |
| El Director se vuelve un cuello de botella de decisión | El Director no procesa datos, solo coordina; su carga es proporcional a las fases, no a las filas |
| Duplicación de configuración entre subgrafos | `defaults.yaml` por skill (ADR-006) + `policies.yaml` único en la raíz |

### Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-002 | El MapReduce intra-skill opera dentro de cada Engineer sin cambios |
| ADR-003 | Red/Blue/Green opera a nivel Director; Engineers emiten AgBOM |
| ADR-009 | Los 9 skills nuevos del Hito 2 siguen el protocolo de siete artefactos |
| ADR-011 | Trace padre en el Director; un span hijo por subgrafo Engineer |
| ADR-013 | La trayectoria auditable incluye las decisiones de asignación del Director |
| ADR-015 | El grafo de streaming del Hito 3 se integrará como subgrafo par |
| ADR-017 (pendiente) | El sandboxing de ejecución se vuelve condición de entrada a Rollout 3, donde el riesgo de generación dinámica de skills (ADR-014) sin contención es más alto |

---

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Orquestador único plano con 15 skills | Complejidad de decisión cuadrática; monolito imposible de testear por partes |
| Microservicios independientes por dominio | Overhead de red y despliegue injustificado en SIGMA Full local |
| Jerarquía de dos niveles con un solo Engineer | No separa datos/modelos/calidad, que tienen políticas de reintento y HITL incompatibles entre sí |
| CrewAI u otro framework jerárquico | Introduciría un segundo framework de orquestación; LangGraph ya provee subgrafos nativos |

---

## Histórico de versiones

Este es el primer registro de este ADR. La decisión de diseño fue aprobada
verbalmente en "Eco MultiAgentes 5 Skills 3" y quedó pendiente de
formalización documental hasta esta versión.

**Cambios en v1.2:**
- **a** Se añade la sección 2.4, Plan de implementación por Rollouts
  (1/2/3), resolviendo la secuencia de construcción que v1.1 dejaba
  implícita. Cada Rollout declara condición de salida verificable y
  skills pendientes de código real.
- **b** Se añade nota cruzada a ADR-017 (sandboxing, pendiente de
  redactar), requerido como condición de entrada a Rollout 3.

**Cambios en v1.3:**
- **a** Se corrige la Fig. 1 y la Tab. 2: `0008-sentiment-analyzer` y
  `0011-viz-reporter` no estaban asignados a ningún Engineer. Se
  reasignan a Engineer Datos (`0000-0004, 0008, 0011`), preservando el
  pipeline funcional heredado de Hito 1 sin reestructurarlo.

**Nota de aprobación (sin cambio de versión):** Aprobado en firme por
Marx. Las 4 condiciones de Rollout 1 (Tab. 2) ya se verificaron en la
práctica: 65/65 tests, 4+ corridas reales, circuit breaker probado,
traza Langfuse end-to-end confirmada. Las condiciones de salida de
Rollout 2 y Rollout 3, aún no verificadas por no existir código, quedan
como estaban — la aprobación cubre el diseño, no adelanta su ejecución.
