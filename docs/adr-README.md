# Índice de Architecture Decision Records — SIGMA

**Versión de este índice:** 2.1 (Hito 2, cierre de Rollout 1)
**Reemplaza a:** `adr-README-v2.0.md` (archivado en `docs/Docs_hito1/`, corresponde al estado de auditoría intermedia de Rollout 1)

Este índice cubre los **23 ADR** vigentes del proyecto al cierre de
Rollout 1 de Hito 2. Respecto a v2.0: `ADR-016`, `017`, `018` (v1.2),
`019` pasan de "Pre-aprobado"/"Candidato" a **Aceptado** en firme. Se
suman tres ADRs nuevos redactados en la sesión de análisis de
alineación de gobernanza: `021`, `022`, `023`.

## Cómo leer la columna "Estado"

- **Aceptado** — aprobado en firme por Marx, sin condiciones pendientes
  de aprobación (puede seguir teniendo trabajo de implementación
  pendiente — eso se indica aparte, no cambia el estado de aprobación).
- **Sin cambios en esta sesión** — se verificó y no necesitó corrección.

*(La categoría "Pre-aprobado" se retira de este índice — todos los
ADRs vigentes están Aceptados; ninguno queda en aprobación condicional.)*

---

## Bloque 1 — Memoria y conocimiento

| ADR | Título | Versión | Estado |
|---|---|---|---|
| [ADR-001](adr-001-memoria-epistemica.md) | Memoria Epistémica (Feature Store + Grafo de Suposiciones) | 1.6 | Aceptado |
| [ADR-008](adr-008-restriccion-epistemica.md) | Contención Epistémica Estricta (K ⊆ X) | 1.4 | Aceptado — sin cambios en esta sesión |
| [ADR-018](adr-018-memoria-operativa-agdr.md) | Memoria Operativa entre Corridas (Ag-DR) | 1.2 | Aceptado — §2.8 nueva (regla Juez↔HITL) |
| [ADR-022](adr-022-rag-director-documentacion.md) | RAG del Director sobre Documentación Interna (ChromaDB) | 1.0 | Aceptado — implementación prospectiva, Hito 3 |
| [ADR-023](adr-023-embeddings-agdr-patrones.md) | Embeddings sobre Ag-DR para Detección de Patrones | 1.0 | Aceptado — implementación prospectiva, Hito 3 |

## Bloque 2 — Seguridad

| ADR | Título | Versión | Estado |
|---|---|---|---|
| [ADR-003](adr-003-equipo-3-colores.md) | Seguridad Automática Red/Blue/Green | 1.7 | Aceptado |
| [ADR-004](adr-004-vibe-diff-mfa.md) | Vibe Diff Persistente y HITL con MFA | 1.6 | Aceptado |
| [ADR-005](adr-005-policy-server.md) | Policy Server Híbrido (Estructural + Semántico) | 1.5 | Aceptado |
| [ADR-010](adr-010-gestion-secretos.md) | Directiva de Remediación de Secretos (12-Factor) | 1.5 | Aceptado |
| [ADR-017](adr-017-sandboxing-ejecucion.md) | Sandboxing de Ejecución (código dinámico y Workers) | 1.3 | Aceptado — condición de entrada a Rollout 3 sigue pendiente de verificación en código |

## Bloque 3 — Especificación y calidad

| ADR | Título | Versión | Estado |
|---|---|---|---|
| [ADR-002](adr-002-mapreduce-skills.md) | Paralelismo Masivo Intra-Skill (MapReduce) | 1.5 | Aceptado |
| [ADR-007](adr-007-evaluacion-multidimensional.md) | Evaluación Multidimensional (7D) con LLM-as-Judge | 1.4 | Aceptado — sin cambios en esta sesión |
| [ADR-009](adr-009-especificacion-skills.md) | Especificación de Skills (Gherkin, LTL, 7 artefactos) | 1.8 | Aceptado |
| [ADR-012](adr-012-versionado-skills.md) | Gestión de Versiones y Promoción de Skills | 1.5 | Aceptado |
| [ADR-013](adr-013-auditoria-trayectoria.md) | Auditoría de Trayectoria de Agentes | 1.5 | Aceptado |
| [ADR-014](adr-014-generacion-dinamica-skills.md) | Generación Dinámica de Skills bajo Demanda | 1.2 | Aceptado |

## Bloque 4 — Trazabilidad e infraestructura

| ADR | Título | Versión | Estado |
|---|---|---|---|
| [ADR-006](adr-006-context-placeholders.md) | Higiene del Contexto (Placeholders + ContextResolver) | 1.5 | Aceptado |
| [ADR-011](adr-011-trazabilidad-langfuse.md) | Trazabilidad de Pipelines en Langfuse V2 | 1.6 | Aceptado |

## Bloque 5 — Orquestación jerárquica e identidad

| ADR | Título | Versión | Estado |
|---|---|---|---|
| [ADR-015](adr-015-hamilton-selector-streaming.md) | Análisis en Tiempo Real (Hamilton Selector, Hito 3) | 1.3 | Aceptado (diseño) — aplicación en Hito 3 |
| [ADR-016](adr-016-orquestacion-jerarquica.md) | Orquestación Jerárquica (Director/Engineer/Auditor) | 1.3 | Aceptado — 4 condiciones de Rollout 1 verificadas en la práctica |
| [ADR-019](adr-019-identidad-agentes-cloe.md) | Formato de Identidad por Agente (CLOE, Workers, A2A/MCP) | 1.6 | Aceptado |

## Bloque 6 — Gobernanza externa (nuevo)

| ADR | Título | Versión | Estado |
|---|---|---|---|
| [ADR-021](adr-021-alineacion-sr2602.md) | Alineación Voluntaria con SR 26-02 (Gestión de Riesgo de Modelos) | 1.0 | Aceptado — documental, sin reclamo de cumplimiento |

*(`ADR-020`, mensajería avanzada, sigue sin redactar — número reservado, se activa si `chain` de ADR-002 supera la capacidad de Redis/Kafka.)*

---

## Resumen de cambios de esta auditoría (Hito 2, cierre de Rollout 1)

- **`ADR-016`, `017`, `018` (v1.2), `019`** pasan de aprobación
  condicional a **Aceptado en firme**. `018` incorpora §2.8 (regla de
  interacción Juez↔HITL, nunca supresión de un disparador determinista).
- **Tres ADRs nuevos:** `021` (alineación de principios con SR 26-02,
  con dos vacíos reales documentados sin resolver: rigor proporcional a
  materialidad, validación de modelos de terceros), `022` (RAG del
  Director sobre documentación interna), `023` (embeddings sobre Ag-DR,
  extensión funcional de `018`). Los tres con implementación
  prospectiva — diseño aceptado, código pendiente de Hito 3.
- **Trabajo de implementación pendiente que la aprobación NO cierra:**
  `ADR-017` sigue necesitando verificación en código real antes de
  Rollout 3 (`ADR-016` Tab. 2 condición c) — aprobar el diseño no
  adelanta esa verificación.

## Próxima actualización de este índice

Al cierre de Rollout 2 (Engineer Modelos) o Rollout 3 (Engineer
Auditor, gateado por `ADR-017` real), lo que ocurra primero.
