---
id: ADR-015
titulo: Arquitectura de Análisis en Tiempo Real con Hamilton Selector
version: 1.1
estado: Propuesto
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-015 v1.0
referencias-minimas: ADR-002, ADR-008, ADR-009, ADR-010, ADR-012
hito-de-aplicacion: Hito 3
aprobado-por: Pendiente de aprobación por Prof. Marx A. García Delgado
nombre-archivo: adr-015-hamilton-selector-streaming.md
---

# ADR-015: Arquitectura de Análisis en Tiempo Real con Hamilton Selector

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

Los Hitos 1 y 2 de SIGMA operan en modo **batch**: el pipeline procesa
datasets completos (Tirendaz 22.5K → Zenodo 130K → Mendeley 28M+) en
ejecuciones discretas. Sin embargo, el caso de uso WC2026-Tweets tiene una
dimensión de tiempo real: durante los partidos, el flujo de mensajes es
continuo y el valor del análisis decae en minutos.

Sin una arquitectura de streaming, SIGMA no puede: detectar picos de
sentimiento durante eventos en vivo, alimentar dashboards reactivos, ni
priorizar qué mensajes analizar cuando el caudal supera la capacidad de
cómputo local.

El problema de priorización es central: con recursos limitados (SIGMA Full,
cómputo local), no todos los mensajes pueden analizarse en tiempo real. Se
necesita un **selector** que decida qué procesar primero.

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
- El orquestador LangGraph del Hito 1 corre en paralelo con el grafo de
  streaming — son dos modos de operación separados, no excluyentes.
- El streaming alimenta el Feature Store (ADR-001) con los mismos contratos
  de datos; el batch puede re-procesar lo que el streaming priorizó.

**Fig. 1 — Coexistencia de los dos modos de operación**

```
MODO BATCH (Hitos 1-2)                MODO STREAMING (Hito 3)
──────────────────────                ─────────────────────────
Dataset completo                      Kafka topic (flujo continuo)
      │                                     │
      ▼                                     ▼
Orquestador LangGraph                 Hamilton Selector (0016)
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
| — | El orquestador LangGraph del Hito 1 coexiste con el grafo de streaming del Hito 3 como modo de operación paralelo. *Nota de auditoría: esta fila citaba antes "ADR-011" incorrectamente — el ADR-011 real trata trazabilidad Langfuse V2, no LangGraph. La decisión formal que respalda LangGraph queda pendiente de auditoría documental (candidata a resolverse en ADR-016)* |

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
