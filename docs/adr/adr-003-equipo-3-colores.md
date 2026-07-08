---
id: ADR-003
titulo: Seguridad Automática con el Modelo Red/Blue/Green
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-003 v1.3
referencias-minimas: ADR-004, ADR-005, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-003: Seguridad Automática con el Modelo Red/Blue/Green

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para explicar primero qué es el modelo
Red/Blue/Green y por qué existe en el ecosistema — como el mecanismo que
cubre las tres fases de riesgo (antes, durante, después de la ejecución)
que ningún control puramente preventivo como el Policy Server (ADR-005)
puede cubrir por sí solo — antes de entrar a la clasificación de las
tres clases de amenaza.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el diagrama de coordinación de los tres equipos respecto
al DAG. Se añade Tab. 1 con la aplicabilidad por variante. Se incorpora el
histórico de versiones.

---

## Contexto

## Contexto

SIGMA delega en LLMs la generación de código, la interpretación de
prompts, y decisiones que se ejecutan contra datos e infraestructura
reales. Esa delegación es justamente lo que hace posible la autonomía
del sistema descrita en el resto del ecosistema (ADR-001, ADR-002), pero
también abre una superficie de riesgo que ningún mecanismo de gobernanza
puramente preventivo (como el Policy Server de ADR-005) puede cubrir por
sí solo: un LLM puede comportarse de forma correcta en el momento de la
validación estructural y aun así degradarse, ser manipulado, o fallar a
mitad de una ejecución larga. SIGMA necesita, por tanto, un mecanismo de
seguridad que no solo valide antes de actuar, sino que vigile durante la
ejecución y sepa recuperarse después de un fallo — las tres fases que
ningún control estático cubre.

Un sistema multiagente que ejecuta código generado por LLMs y accede a
datos externos es vulnerable a tres clases de amenaza distintas, cada
una con una ventana temporal distinta:

- **Amenazas activas:** prompt injection, slopsquatting, código
  malicioso — ocurren en el momento de la generación o ejecución.
- **Amenazas pasivas:** drift silencioso en el comportamiento de los
  agentes, dependencias no auditadas — se acumulan con el tiempo, sin
  un evento único que las dispare.
- **Fallos de recuperación:** un agente que falla a mitad del pipeline
  puede corromper el estado parcial sin posibilidad de rollback limpio
  — ocurren después del hecho, cuando ya es tarde para prevenir.

Un único auditor al final de la ejecución no puede detectar ni prevenir
estas tres amenazas en tiempo real, porque para cuando revisa el
resultado, las tres ventanas temporales ya se cerraron.

---

## Decisión

Implementar tres agentes de seguridad especializados que corren en paralelo
al DAG principal durante toda la ejecución.

### Fig. 1 — Coordinación de los equipos Red/Blue/Green respecto al DAG

```
FASE PRE-VUELO (antes del DAG real):
─────────────────────────────────────
Orquestador crea checkpoint del estado inicial
        │
        ▼
Sub-grafo temporal (datos clonados, políticas relajadas de ADR-005)
        │
        ├─ Red Team opera sobre el sub-grafo
        │    └─ Inyecta prompts adversariales, dependencias simuladas
        │    └─ Emite reporte inmutable → MinIO
        │
        ▼
Sub-grafo destruido → DAG real comienza

DURANTE EL DAG REAL:
─────────────────────────────────────
Cada worker emite evento AgBOM al iniciar:
  {model_hash, dependency_hashes, worker_id}
        │
        ▼
Blue Team verifica hashes vs. AgBOM de referencia en Langfuse
  └─ Desviación detectada → alerta al Orquestador

ANTE UN FALLO:
─────────────────────────────────────
Fallo detectado (excepción o alerta Blue Team)
        │
        ▼
Green Team: snapshot del estado → aísla agente comprometido
        │
        ▼
code-reviewer evalúa el código de refactor
        │
        ├─ Impacto LOW  → Green Team aplica automáticamente
        └─ Impacto MEDIUM/HIGH → Vibe Diff → Approval Endpoint (ADR-004)
```

### Red Team — Modelo de pre-vuelo

El Red Team no opera durante el pipeline de producción sobre datos reales.
Opera en una fase de pre-vuelo antes de que el DAG real comience. Los
hallazgos son reportes inmutables almacenados en MinIO, no mutaciones del
estado real.

### Tab. 1 — Aplicabilidad de los equipos por variante

| Equipo | SIGMA Full | SIGMA Lite | SIGMA Dev | SIGMA Runtime |
|---|---|---|---|---|
| **Red Team** | Activo | Activo | Desactivado por defecto | Obligatorio antes de pipeline crítico |
| **Blue Team** | Activo | Activo | Opcional | Activo |
| **Green Team** | Activo | Activo | Activo | Activo |

### Blue Team — Monitorización mediante AgBOM

El Blue Team no gestiona un hilo por worker. Cada worker emite un evento
AgBOM al iniciar con su `model_hash` y `dependency_hashes`. El Blue Team
verifica esos hashes contra el AgBOM de referencia en Langfuse. El límite
de workers que puede manejar es el límite de eventos de Langfuse, no un
límite intrínseco del Blue Team.

### Green Team — Recuperación con ciclo de revisión

Todo código generado por auto-refactor pasa obligatoriamente por el skill
`code-reviewer`. Si el impacto es `LOW`, el Green Team lo aplica
automáticamente. Si el impacto es `MEDIUM` o superior, genera un Vibe Diff
con el diff exacto del código y espera aprobación según ADR-004. La cuarentena
preserva el estado forense: el snapshot pre-cuarentena nunca se borra
automáticamente.

---

## Consecuencias positivas

- La separación en tres roles elimina conflictos de interés.
- El modelo de pre-vuelo del Red Team garantiza que los datos reales nunca
  se contaminan con ataques simulados.
- El Blue Team escala con cualquier cantidad de workers vía eventos Langfuse.
- El ciclo `code-reviewer` + Vibe Diff garantiza que el código de recuperación
  es auditado antes de aplicarse.

## Consecuencias negativas

- El pre-vuelo del Red Team añade latencia antes de cada pipeline crítico.
- El Green Team requiere acceso de escritura a checkpoints en almacenamiento
  local rápido.
- La coordinación entre los tres equipos añade complejidad al Orquestador.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Auditor único post-ejecución | El daño está hecho al terminar |
| Solo validación de inputs y outputs | No detecta compromisos durante la ejecución |
| SIEM externo | Dependencias fuera del ecosistema SIGMA |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se redefinió el Red Team para operar en modelo de pre-vuelo
  sobre un sub-grafo clonado, eliminando el riesgo de contaminación de datos
  reales.
- **b.1.2** Se añadió el ciclo de recuperación del Green Team con integración
  de `code-reviewer` y Vibe Diff.
- **c.1.2** Se especificó la escalabilidad del Blue Team mediante eventos
  AgBOM en Langfuse en lugar de hilos por worker.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el diagrama de coordinación de los tres equipos
  respecto al DAG.
- **b** Se añadió Tab. 1 con la aplicabilidad por variante.
