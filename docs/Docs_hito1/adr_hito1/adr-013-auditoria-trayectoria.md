---
id: ADR-013
titulo: Auditoría de Trayectoria de Agentes
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-013 v1.3
referencias-minimas: ADR-003, ADR-005, ADR-008, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-013: Auditoría de Trayectoria de Agentes

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para explicar primero que este ADR
implementa la medición real de D6 (ADR-007) y complementa a K⊆X
(ADR-008) como la otra mitad de la auditabilidad de un agente. Se
corrige la referencia rota "ADR-00" del Agente Auditor a **ADR-016**,
donde se define formalmente como el tercer orquestador del patrón
Director/Engineer/Auditor.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el diagrama de los cuatro componentes de la trayectoria
completa auditable. Se añade Tab. 1 con los umbrales de adherencia y sus
consecuencias operacionales. Se incorpora el histórico de versiones.

---

## Contexto

La Auditoría de Trayectoria es el mecanismo que hace posible medir D6
(calidad de trayectoria) en la Evaluación Multidimensional de ADR-007 —
sin él, esa dimensión sería una intención sin implementación real. Usa
las trazas de Langfuse (ADR-011) como fuente de verdad, y sus hallazgos
alimentan directamente al Blue Team (ADR-003) cuando detecta
desviaciones graves. Es, junto con K⊆X (ADR-008), la otra mitad de lo
que hace a un agente de SIGMA auditable: K⊆X garantiza que lo que el
agente afirma es honesto, mientras que este ADR garantiza que el camino
que tomó para llegar ahí también es verificable.

Un agente puede producir el output correcto tomando el camino
equivocado. Puede llamar herramientas en el orden incorrecto, acceder a
tablas que no debería, o consumir diez veces más recursos y aun así
producir un resultado que supera los tests unitarios. La trayectoria es
la secuencia de herramientas, modelos y decisiones que el agente tomó
para llegar al output. Auditar la trayectoria, y no solo el output,
permite detectar comportamientos inesperados, verificar que el agente
operó dentro de los límites de K⊆X (ADR-008), e identificar ineficiencias.

---

## Decisión

El agente Auditor (Definido en ADR-00) verifica la trayectoria real de 
cada ejecución contra la trayectoria esperada declarada en el `SKILL.md` 
de ADR-009, usando las trazas de Langfuse V2 (o de cualquier otro servicio de
trazabiidad tales como...) de ADR-011 como fuente de verdad.

### Fig. 1 — Componentes de la trayectoria completa auditable

```
TRAYECTORIA COMPLETA DE UN PIPELINE
─────────────────────────────────────────────────────────────

COMPONENTE 1 — Secuencia de herramientas del skill
  read_table(tweets_cleaned)
  run_model(roberta-sentiment)
  write_table(tweets_sentiment)
  → comparada con expected_trajectory del SKILL.md

COMPONENTE 2 — Decisiones del Policy Server
  tool: read_table     → PERMITIDO  (capa estructural, regla: allowed_tables)
  tool: write_prod     → BLOQUEADO  (capa estructural, regla: denied_tables)
  → incluidas en el reporte de auditoría

COMPONENTE 3 — Vibe Diffs generados y su resultado
  vibe_diff_id: sigma-20260601-143022  → APPROVED  (operador: marxiano)
  → incluidos en el reporte de auditoría

COMPONENTE 4 — Sub-grafo del Red Team (excluido del score principal)
  red_team_probe: 3 vulnerabilidades encontradas, 0 críticas
  → registrado como componente separado, no afecta adherence_score
  del DAG principal porque usa políticas diferentes por diseño
```

### Verificaciones principales

El Auditor realiza cuatro verificaciones sobre la trayectoria real:

1. **Adherencia a la trayectoria esperada:** comparación con
   `expected_trajectory` del `SKILL.md`. Score de 0 a 1.
2. **Herramientas no autorizadas:** verificación contra `allowed-tools`
   del `SKILL.md`.
3. **Violación K⊆X en trayectoria:** verificación de que cada herramienta
   operó sobre datos dentro de X (ADR-008).
4. **Eficiencia de trayectoria:** penalización de pasos redundantes.

### Tab. 1 — Umbrales de adherencia y consecuencias

| Score | Estado | Acción |
|---|---|---|
| ≥ 0.95 | Normal | Solo registro en Langfuse |
| 0.80 – 0.94 | Desviación menor | Log en Langfuse + alerta al Orquestador |
| < 0.80 | Desviación mayor | Log + alerta al Blue Team + notificación HITL al operador |
| Herramienta no autorizada | Independiente del score | Alerta inmediata al Blue Team + al Policy Server |
| Violación K⊆X en trayectoria | Independiente del score | Alerta inmediata + posible terminación del pipeline |

El reporte de auditoría se almacena en Langfuse con los campos: `run_id`,
`skill_id`, `skill_version`, `adherence_score`, `unauthorized_tools`,
`epistemic_violations`, `efficiency_score`, `policy_decisions_audited`,
`vibe_diffs_audited` y `verdict`.

---

## Consecuencias positivas

- Los agentes son explicables: siempre se puede reconstruir qué hicieron y
  por qué.
- La incorporación de las decisiones del Policy Server y los Vibe Diffs da
  visión completa del flujo de gobernanza.
- Los scores acumulados en Langfuse permiten detectar degradación del
  comportamiento a lo largo del tiempo.

## Consecuencias negativas

- El Auditor añade overhead proporcional al número de pasos en la trayectoria.
- La `expected_trajectory` en el `SKILL.md` debe mantenerse actualizada o
  genera falsos negativos.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Solo auditoría post-mortem | Las violaciones K⊆X en tiempo real pueden causar daños irreversibles |
| Auditoría por sampling | Las violaciones de seguridad deben auditarse al 100% |
| Auditoría manual periódica | No escala; las trazas de Langfuse son el sustituto automatizado |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se incorporaron las decisiones del Policy Server como parte de
  la trayectoria auditable.
- **b.1.2** Se conectó la auditoría con el sub-grafo del Red Team
  excluyéndolo del score del DAG principal.
- **c.1.2** Se añadió la trayectoria del Vibe Diff como componente auditable.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el diagrama de los cuatro componentes de la
  trayectoria completa auditable.
- **b** Se añadió Tab. 1 con los umbrales de adherencia, sus rangos y sus
  consecuencias operacionales.
