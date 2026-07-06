---
id: ADR-016
titulo: Orquestación Jerárquica de Tres Orquestadores (Patrón Director/Engineer)
version: 1.0
estado: Propuesto
fecha-original: 2026-07
fecha-revision: 2026-07
supersede: Ninguno
referencias-minimas: ADR-002, ADR-003, ADR-009, ADR-011, ADR-013
hito-de-aplicacion: Hito 2
aprobado-por: Pendiente de aprobación por Prof. Marx A. García Delgado
nombre-archivo: adr-016-orquestacion-jerarquica.md
---

# ADR-016: Orquestación Jerárquica de Tres Orquestadores (Patrón Director/Engineer)

## Resumen ejecutivo

Este ADR formaliza la decisión ya aprobada en diseño (conversación "Eco
MultiAgentes 5 Skills 3") de que el Hito 2 adopta una **arquitectura
jerárquica de tres orquestadores** mediante subgrafos de LangGraph, bajo el
patrón Director/Engineer. Su redacción quedó pendiente como deuda documental;
este ADR la salda. Aprovecha además para registrar formalmente la decisión
que ningún ADR anterior respaldaba: **LangGraph como motor de orquestación
del ecosistema** — resolviendo la referencia pendiente detectada en la
auditoría del ADR-015.

---

## Contexto

El Hito 1 opera con un único orquestador (SupervisorAgent en LangGraph) que
gestiona un pipeline lineal de 6 skills. El Hito 2 incorpora 9 skills
adicionales (0005–0007, 0009–0010, 0012–0015) que incluyen entrenamiento
ML/DL, explicabilidad, HITL avanzado e inspección — dominios con
trayectorias, tiempos de ejecución y necesidades de supervisión radicalmente
distintas.

Un orquestador único plano tendría que conocer los detalles de los 15 skills,
sus dependencias cruzadas y sus políticas de reintento — un monolito de
decisión que crece cuadráticamente en complejidad con cada skill nuevo.

Adicionalmente, la auditoría del ADR-015 detectó que ninguna decisión formal
respaldaba la elección de LangGraph: se usaba de facto desde el Hito 1 sin
ADR que la justificara. Este documento la registra.

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
ENGINEER DATOS   ENGINEER MODELOS   ENGINEER CALIDAD
(subgrafo 1)     (subgrafo 2)       (subgrafo 3)
skills:          skills:            skills:
0000-0004        0005-0007,         0012-0015
(pipeline        0009-0010          (inspector,
 batch core)     (trainers ML/DL,    explainability,
                  HITL avanzado)     auditoría)
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
