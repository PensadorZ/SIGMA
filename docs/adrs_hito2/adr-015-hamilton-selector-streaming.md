---
id: ADR-015
titulo: Arquitectura de Análisis en Tiempo Real con Hamilton Selector
version: 1.3
estado: Propuesto
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-015 v1.2
referencias-minimas: ADR-002, ADR-008, ADR-009, ADR-010, ADR-012
hito-de-aplicacion: Hito 3
aprobado-por: Pendiente de aprobación por Prof. Marx A. García Delgado
nombre-archivo: adr-015-hamilton-selector-streaming.md
---

# ADR-015: Arquitectura de Análisis en Tiempo Real con Hamilton Selector

## Resumen ejecutivo de cambios v1.3

Verificado contra el estado real de Hito 2 (cierre de Rollout 1): (1)
esquema de variantes corregido (`SIGMA Full` → `SIGMA-FE`); (2) el
"orquestador LangGraph del Hito 1" ya no existe como componente
monolítico — se reemplaza toda referencia por la jerarquía Director +
Engineers de `ADR-016`, coherente con que este ADR ya se describía a sí
mismo como "subgrafo par" de esa jerarquía; (3) la decisión formal sobre
LangGraph que esta ADR marcaba como "pendiente de auditoría documental"
ya fue resuelta — `ADR-016` §2.1 la formaliza explícitamente. Se retira
la nota de "pendiente".

## Resumen ejecutivo de cambios v1.2

Se amplía la sección de Contexto para explicar primero que esta
arquitectura de streaming está reservada desde ADR-009 (skills
0016-0019) y coexiste como subgrafo par del orquestador batch que
ADR-016 formaliza — antes de entrar al detalle del problema de
priorización con recursos limitados.

## Resumen ejecutivo de cambios v1.1

Migración del ADR (originado en la conversación "Eco MultiAgentes 3 (Hito 1)") 
al formato canónico aprobado del repositorio de ADRs: frontmatter
YAML completo, figuras y tablas numeradas con título, e histórico de
versiones con literales. Se conserva la corrección de la auditoría previa:
la relación que citaba erróneamente "ADR-011: LangGraph" fue eliminada — el
ADR-011 real trata la trazabilidad en Langfuse V2, no la elección de
LangGraph. La decisión formal que respalda LangGraph como motor de
orquestación queda registrada como pendiente de auditoría documental.

---

## Contexto

El Hamilton Selector y la arquitectura de streaming que define este ADR
son la extensión natural del ecosistema hacia el tiempo real —
reservada desde ADR-009 en el rango de skills `0016`-`0019`, y pensada
para **coexistir, no competir**, con el orquestador batch del Hito 1: el
mismo LangGraph que ADR-016 formaliza como motor único del ecosistema
sigue corriendo el pipeline batch mientras este grafo de streaming opera
en paralelo, como un cuarto subgrafo par.

Los Hitos 1 y 2 de SIGMA operan en modo **batch**: el pipeline procesa
datasets completos (Tirendaz 22.5K → Zenodo 130K → Mendeley 28M+) en
ejecuciones discretas. Sin embargo, el caso de uso WC2026-Tweets tiene
una dimensión de tiempo real: durante los partidos, el flujo de mensajes
es continuo y el valor del análisis decae en minutos.

Sin una arquitectura de streaming, SIGMA no puede: detectar picos de
sentimiento durante eventos en vivo, alimentar dashboards reactivos, ni
priorizar qué mensajes analizar cuando el caudal supera la capacidad de
cómputo local.

El problema de priorización es central: con recursos limitados (SIGMA-FE,
cómputo local), no todos los mensajes pueden analizarse en tiempo
real. Se necesita un **selector** que decida qué procesar primero.

---

## Decisión

### 2.1 — Hamilton Selector: priorización mediante matriz hamiltoniana

Se introduce el **Hamilton Selector** (skill `0016`): un componente de
priorización que asigna a cada mensaje entrante un score compuesto calculado
como combinación lineal ponderada de señales, inspirado en la estructura de
una matriz hamiltoniana donde los elementos diagonales representan la
"energía propia" de cada señal y la suma ponderada determina la prioridad
de procesamiento.

**Tab. 1 — Señales y pesos de la matriz de priorización**

| Señal | Peso | Descripción |
|---|---|---|
| Engagement potencial | 0.30 | Seguidores, retweets históricos del autor |
| Novedad léxica | 0.25 | Distancia a los clusters de tópicos ya conocidos |
| Velocidad del hilo | 0.25 | Tasa de respuestas/menciones por minuto |
| Relevancia de entidad | 0.20 | Presencia de entidades del dominio (equipos, jugadores) |

Los pesos suman 1.0 y son configurables en `policies.yaml`. La restricción
K ⊆ X (ADR-008) aplica: el selector solo usa señales presentes en el mensaje
y su metadata observable, nunca inferencias del entrenamiento del modelo.

### 2.2 — Stack de streaming: Kafka + Faust

| Componente | Rol |
|---|---|
| **Apache Kafka** | Broker de eventos; topics por partido/evento |
| **Faust** | Capa Python de procesamiento de streams sobre Kafka |
| **Skills 0017–0019** | Consumidores Faust especializados (análisis RT, agregación, dashboard reactivo) |

Las credenciales del broker (si las hay) se gestionan con
`get_required_env()` según ADR-010. El skill `0019` usa Netlify como opción
de despliegue del dashboard reactivo, según el hook de despliegue de
ADR-012.

### 2.3 — Coexistencia batch/streaming

La arquitectura batch de los Hitos 1 y 2 **no se modifica**:

- Los skills 0000–0015 son independientes de la decisión de streaming.
- **Corregido (Hito 2, Rollout 1):** ya no hay un "orquestador LangGraph
  del Hito 1" monolítico — fue reemplazado por la jerarquía Director +
  Engineers (Datos/Modelos/Auditor) de `ADR-016`. El grafo de streaming
  de este ADR coexiste con esa jerarquía como **subgrafo par**, tal
  como ya anticipa `ADR-016` en su propia tabla de relación con otros
  ADRs — no con un orquestador que ya no existe en esa forma.
- El streaming alimenta el Feature Store (ADR-001) con los mismos contratos
  de datos; el batch puede re-procesar lo que el streaming priorizó.

**Fig. 1 — Coexistencia de los dos modos de operación**

```
MODO BATCH (Hitos 1-2)                MODO STREAMING (Hito 3)
──────────────────────                ─────────────────────────
Dataset completo                      Kafka topic (flujo continuo)
      │                                     │
      ▼                                     ▼
Director + Engineers (ADR-016)        Hamilton Selector (0016)
  skills 0000-0015                      │ score > umbral
      │                                     ▼
      ▼                               Consumidores Faust (0017-0019)
PostgreSQL / MinIO / Langfuse               │
      ▲                                     ▼
      └────── Feature Store común ──────────┘
              (ADR-001, mismos contratos)
```

---

## Consecuencias

### Beneficios

- SIGMA gana capacidad de análisis en vivo sin tocar la arquitectura batch
  verificada del Hito 1.
- El Hamilton Selector hace viable el tiempo real con cómputo local: se
  procesa lo prioritario, no todo.
- Los skills 0016–0019 siguen el protocolo de siete artefactos de ADR-009,
  con Gherkin y LTL — sin excepciones por ser streaming.

### Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Kafka añade complejidad operacional significativa | Hito 3 no comienza hasta que Hito 1 y 2 estén validados; Kafka solo disponible en SIGMA-ME/HE (recursos de cómputo y presupuesto suficientes para el broker) |
| Los pesos de la matriz pueden sesgarse hacia contenido viral | Los pesos son configurables y auditables en `policies.yaml`; revisión periódica contra ADR-007 D1 |
| Baja confianza del clasificador en streaming | K ⊆ X aplica igual que en batch: `UNCLEAR` para baja confianza, sin excepciones (ADR-008) |

### Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-002 | El particionamiento por topics de Kafka es el análogo streaming del MapReduce batch |
| ADR-008 | K ⊆ X aplica en streaming igual que en batch. `UNCLEAR` para baja confianza, sin excepciones |
| ADR-009 | Los skills 0016–0019 siguen el protocolo de siete artefactos con Gherkin y LTL |
| ADR-010 | Las credenciales del broker (si las hay) se gestionan con `get_required_env()` |
| ADR-012 | El skill 0019 usa Netlify como opción de despliegue del dashboard reactivo |
| ADR-016 | El orquestador batch ya no es un LangGraph monolítico de Hito 1 — es la jerarquía Director + Engineers que ADR-016 v1.1+ formaliza, incluyendo la decisión base de LangGraph como motor de orquestación (§2.1, resuelta — ya no pendiente). El streaming de este ADR se integra como subgrafo par de esa jerarquía |

---

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Procesar el 100% del flujo sin selector | Inviable con cómputo local; el caudal en picos supera la capacidad |
| Muestreo aleatorio en lugar del Hamilton Selector | Pierde sistemáticamente los mensajes de mayor valor analítico |
| Redis Streams en lugar de Kafka | Suficiente para el buffer `chain` (ADR-002) pero sin las garantías de retención y particionamiento que exige un flujo de eventos de partido completo |
| Spark Structured Streaming | Overhead de infraestructura injustificado para el volumen objetivo del Hito 3 inicial |

---

## Histórico de versiones

**Cambios en v1.0:**
- **a.1.0** Redacción original en "Eco MultiAgentes 4 Skills 2" con la
  estructura Estado · Contexto · Decisión (2.1–2.3) · Consecuencias ·
  Historial.
- **b.1.0** Corrección de auditoría: eliminada la referencia falsa a
  "ADR-011: LangGraph"; el ADR-011 real trata trazabilidad Langfuse V2.

**Cambios en v1.1:**
- **a** Migración al formato canónico del repositorio de ADRs: frontmatter
  YAML completo con campo `hito-de-aplicacion`, Fig. 1 y Tab. 1 numeradas
  con título, histórico con literales.
- **b** Se añadió la sección Alternativas Consideradas, ausente en v1.0.
- **c** La decisión formal pendiente sobre LangGraph se marca como candidata
  a resolverse en ADR-016.

**Cambios en v1.3 (Hito 2, cierre de Rollout 1):**
- **a** Esquema de variantes corregido: `SIGMA Full` → `SIGMA-FE`.
- **b** Todas las referencias al "orquestador LangGraph del Hito 1"
  monolítico se actualizaron a la jerarquía Director + Engineers real
  de `ADR-016` — Fig. 1 y sección 2.3 corregidas.
- **c** Resuelta la nota de "pendiente de auditoría documental" sobre
  LangGraph — `ADR-016` §2.1 ya formaliza esa decisión, se retira la
  marca de pendiente y se cita la resolución real.
