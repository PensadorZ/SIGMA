---
id: ADR-README
titulo: Índice de Architecture Decision Records — SIGMA
version: 1.6
estado: Activo
fecha-revision: 2026-07
aprobado-por: Prof. Marx A. García Delgado
---

# Índice de Architecture Decision Records — SIGMA

Este documento es el punto de entrada al sistema de decisiones
arquitectónicas de SIGMA. No contiene decisiones propias: organiza,
describe y relaciona los 16 ADRs del ecosistema, mostrando cómo se
conectan entre sí y en qué variantes y submodos aplica cada uno. Todo
agente, desarrollador u operador que necesite entender por qué el
sistema funciona como funciona — y no de otra manera — debe comenzar
aquí, antes de tocar código o proponer un cambio de diseño.

---

## Cómo leer los ADRs

Cada ADR tiene cinco secciones obligatorias: frontmatter con metadatos,
resumen ejecutivo que explica los cambios de esa versión, contexto, decisión
y consecuencias. Todos incluyen un **histórico de versiones** al final: los
cambios de versiones anteriores llevan literales con número (ej. `a.1.2`,
`b.1.3`) y los de la versión vigente llevan literales sin número (`a`, `b`).
Los ADRs de Hitos futuros incluyen el campo `hito-de-aplicacion` en el
frontmatter.

---

## Regla de referencias

Cada ADR referencia un mínimo de tres ADRs anteriores. Esto garantiza que las
decisiones no sean islas y que cualquier cambio en un ADR active una revisión
de los que dependen de él.

---

## Estados posibles

| Estado | Significado |
|---|---|
| ✅ **Aceptado** | Decisión vigente, implementada o en implementación |
| 🟡 **Propuesto** | En revisión, pendiente de aprobación |
| 🔄 **Supersedido** | Reemplazado por un ADR posterior. El ADR antiguo se mantiene con su estado actualizado y enlace al sucesor |
| ⛔ **Obsoleto** | Retirado sin reemplazo directo |



## Tab. 1 — Registro completo de ADRs

| ADR | Archivo | Título | Estado | Versión |
|---|---|---|---|---|
| ADR-001 | [adr-001-memoria-epistemica.md](adr-001-memoria-epistemica.md) | Memoria Epistémica — Feature Store y Grafo de Suposiciones | ✅ Aceptado | **1.5** |
| ADR-002 | [adr-002-mapreduce-skills.md](adr-002-mapreduce-skills.md) | Paralelismo Masivo Intra-Skill mediante MapReduce | ✅ Aceptado | **1.4** |
| ADR-003 | [adr-003-equipo-3-colores.md](adr-003-equipo-3-colores.md) | Seguridad Automática con Modelo Red/Blue/Green | ✅ Aceptado | **1.4** |
| ADR-004 | [adr-004-vibe-diff-mfa.md](adr-004-vibe-diff-mfa.md) | Vibe Diff Persistente y Human-in-the-Loop con MFA | ✅ Aceptado | **1.6** |
| ADR-005 | [adr-005-policy-server.md](adr-005-policy-server.md) | Policy Server Híbrido — Estructural y Semántico | ✅ Aceptado | **1.4** |
| ADR-006 | [adr-006-context-placeholders.md](adr-006-context-placeholders.md) | Higiene del Contexto con Placeholders y ContextResolver | ✅ Aceptado | **1.4** |
| ADR-007 | [adr-007-evaluacion-multidimensional.md](adr-007-evaluacion-multidimensional.md) | Evaluación Multidimensional (7D) con LLM-as-Judge | ✅ Aceptado | **1.4** |
| ADR-008 | [adr-008-restriccion-epistemica.md](adr-008-restriccion-epistemica.md) | Contención Epistémica Estricta (K ⊆ X) | ✅ Aceptado | **1.4** |
| ADR-009 | [adr-009-especificacion-skills.md](adr-009-especificacion-skills.md) | Especificación de Skills — Gherkin, LTL y Estructura Granular | ✅ Aceptado | **1.7** |
| ADR-010 | [adr-010-gestion-secretos.md](adr-010-gestion-secretos.md) | Directiva de Remediación de Secretos — 12-Factor | ✅ Aceptado | **1.4** |
| ADR-011 | [adr-011-trazabilidad-langfuse.md](adr-011-trazabilidad-langfuse.md) | Trazabilidad de Pipelines en Langfuse V2 | ✅ Aceptado | **1.5** |
| ADR-012 | [adr-012-versionado-skills.md](adr-012-versionado-skills.md) | Gestión de Versiones y Promoción de Skills | ✅ Aceptado | **1.4** |
| ADR-013 | [adr-013-auditoria-trayectoria.md](adr-013-auditoria-trayectoria.md) | Auditoría de Trayectoria de Agentes | ✅ Aceptado | **1.4** |
| ADR-014 | [adr-014-generacion-dinamica-skills.md](adr-014-generacion-dinamica-skills.md) | Generación Dinámica de Nuevos Skills bajo Demanda | 🟡 Propuesto | **1.1** |
| ADR-015 | [adr-015-hamilton-selector-streaming.md](adr-015-hamilton-selector-streaming.md) | Arquitectura de Análisis en Tiempo Real con Hamilton Selector | 🟡 Propuesto | **1.2** |
| ADR-016 | [adr-016-orquestacion-jerarquica.md](adr-016-orquestacion-jerarquica.md) | Orquestación Jerárquica de Tres Orquestadores (Director/Engineer/Auditor) | 🟡 Propuesto | **1.1** |

---

## Tab. 2 — Mapa de dependencias entre ADRs

| ADR | Depende de | Es leído por |
|---|---|---|
| ADR-001 | — | ADR-007, ADR-008, ADR-015 |
| ADR-002 | ADR-001 | ADR-008, ADR-009, ADR-015, ADR-016 |
| ADR-003 | ADR-004, ADR-005 | ADR-011, ADR-013, ADR-016 |
| ADR-004 | ADR-003, ADR-005, ADR-010 | ADR-003, ADR-013, ADR-014 |
| ADR-005 | ADR-006, ADR-010 | ADR-003, ADR-004, ADR-011, ADR-013 |
| ADR-006 | ADR-005, ADR-010 | ADR-009 |
| ADR-007 | ADR-001, ADR-008, ADR-011 | ADR-016 |
| ADR-008 | ADR-001, ADR-002 | ADR-007, ADR-013, ADR-015, ADR-016 |
| ADR-009 | ADR-002, ADR-006 | ADR-011, ADR-012, ADR-014, ADR-015, ADR-016 |
| ADR-010 | ADR-004, ADR-005, ADR-006 | ADR-012, ADR-015 |
| ADR-011 | ADR-003, ADR-005, ADR-007, ADR-009 | ADR-012, ADR-013, ADR-016 |
| ADR-012 | ADR-009, ADR-010, ADR-011 | ADR-014, ADR-015 |
| ADR-013 | ADR-003, ADR-005, ADR-008, ADR-011 | ADR-016 |
| ADR-014 | ADR-003, ADR-004, ADR-009, ADR-012 | — |
| ADR-015 | ADR-002, ADR-008, ADR-009, ADR-010, ADR-012 | ADR-016 |
| ADR-016 | ADR-002, ADR-003, ADR-009, ADR-011, ADR-013 | — |

---

### Tab. 3 — Aplicabilidad por variante y submodo

| ADR | Variantes de costo (FE/LE/ME/HE) | Dev (transversal) | Runtime (transversal) |
|---|---|---|---|
| ADR-001 | Obligatorio | Parcial | Obligatorio |
| ADR-002 | Obligatorio | Parcial | Obligatorio |
| ADR-003 | Obligatorio | No aplica | Obligatorio |
| ADR-004 | Obligatorio | Relajado | Obligatorio |
| ADR-005 | Obligatorio | Solo estructural | Obligatorio |
| ADR-006 | Obligatorio | Obligatorio | Obligatorio |
| ADR-007 | Obligatorio | Parcial | Obligatorio |
| ADR-008 | Obligatorio | Obligatorio | Obligatorio |
| ADR-009 | Obligatorio | Obligatorio | Obligatorio |
| ADR-010 | Obligatorio | Obligatorio | Obligatorio |
| ADR-011 | Ver nota (*) | Opcional | Obligatorio (autoalojado) |
| ADR-012 | Obligatorio | Parcial | Obligatorio |
| ADR-013 | Obligatorio | Opcional | Obligatorio |
| ADR-014 | Obligatorio | No aplica | Con aprobación |
| ADR-015 | Hito 3 | No aplica | Hito 3 con aprobación |
| ADR-016 | Hito 2 | Parcial | Hito 2 |

(*) ADR-011 es la única excepción real: varía según el costo del stack, no
según la gobernanza. SIGMA-FE y SIGMA-LE usan Langfuse autoalojado;
SIGMA-ME y SIGMA-HE usan Langfuse Cloud / LangSmith (ver SIGMA_v1.7.md,
tabla comparativa por costo).

---

## Protocolo de modificación

Los ADRs son inmutables una vez aceptados. Si una decisión cambia, se crea
una nueva versión del mismo ADR. El histórico nunca se borra. Un cambio en un
ADR obliga a revisar todos los ADRs que lo referencian como dependencia directa.

---

## Notas de revisión por tabla

- **ADR-001 → v1.5:** Contexto ampliado con el rol de fundamento de K⊆X. Nota conceptual de Zeugmatización agregada.
- **ADR-002 → v1.4:** Contexto ampliado explicando su rol como extensión de ADR-009.
- **ADR-003 → v1.4:** Contexto ampliado con las tres fases de riesgo que cubre.
- **ADR-004 → v1.6:** Contexto ampliado como cierre de la autonomía de ADR-001/002. Literales de v1.5 renumerados.
- **ADR-005 → v1.4:** Contexto ampliado como intercepción previa a Vibe Diff y Red/Blue/Green.
- **ADR-006 → v1.4:** Contexto ampliado como mecanismo de portabilidad entre variantes.
- **ADR-007 → v1.4:** Contexto ampliado distinguiendo honestidad (K⊆X) de calidad (7D).
- **ADR-008 → v1.4:** Contexto ampliado como ley epistémica central de la que dependen ADR-001/002/007.
- **ADR-009 → v1.7:** Contexto ampliado como contrato del que dependen ADR-002/006/011.
- **ADR-010 → v1.4:** Contexto ampliado como fundamento de ADR-004/005/006.
- **ADR-011 → v1.5:** Contexto ampliado como correlación común de ADR-003/005/007. Literales de v1.4 renumerados.
- **ADR-012 → v1.4:** Contexto ampliado como proceso operativo de la obligatoriedad de tests/ (ADR-009).
- **ADR-013 → v1.4:** Contexto ampliado como implementación real de D6 (ADR-007). Corregida referencia rota "ADR-00" a **ADR-016**.
- **ADR-014 → v1.1:** Contexto ampliado como escenario de mayor riesgo del ecosistema.
- **ADR-015 → v1.2:** Contexto ampliado como extensión reservada desde ADR-009, coexistente con ADR-016.
- **ADR-016 → v1.1:** Contexto ampliado explicando su doble función: formalizar LangGraph y gobernar el Hito 2.

## Notas de la revisión de julio 2026 (v1.5 del índice)

- **ADR-001 → v1.5:** Contexto ampliado para explicar qué es la Memoria
  Epistémica y por qué existe en el ecosistema (fundamento operativo de
  K ⊆ X, ADR-008) antes de entrar al problema técnico. Se agrega nota
  conceptual de referencia cruzada a la Zeugmatización epistemológica,
  explícitamente delimitada como fuera del alcance técnico del ADR.
- **ADR-004 → v1.5:** el mecanismo HITL se actualizó al verificado en el
  Hito 1 (LangGraph `interrupt()` + SqliteSaver); el polling a Redis pasó
  a alternativa descartada.
- **ADR-009 → v1.5:** protocolo de siete artefactos canónicos obligatorios,
  verificado contra 65/65 tests; catálogo extendido a 20 skills (0000–0019).
- **ADR-001 → v1.4 y ADR-011 → v1.4:** ajustes menores verificados en el
  Hito 1 (KS-test único método / pin Langfuse `:2` + `langfuse<3`).
- **ADR-015 → v1.1:** migrado al formato canónico desde "Eco MultiAgentes 4
  Skills 2", conservando la corrección de la referencia falsa a ADR-011.
- **ADR-016 → v1.0 (nuevo):** salda la deuda documental del Hito 2
  (jerarquía de tres orquestadores) y registra formalmente LangGraph como
  motor de orquestación — la decisión que ningún ADR anterior respaldaba.
- **Tab. 3 → v1.6:** Colapsada de cuatro columnas (Full/Lite/Dev/Runtime) a
  una sola columna de variantes de costo (FE/LE/ME/HE) + dos columnas
  transversales (Dev/Runtime), reflejando la renominación aplicada en
  SIGMA_v1.7.md. Única excepción real es ADR-011 (Langfuse autoalojado vs.
  Cloud), documentada en nota al pie. 
