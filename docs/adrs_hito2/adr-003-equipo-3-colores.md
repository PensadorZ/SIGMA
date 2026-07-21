---
id: ADR-003
titulo: Seguridad Automática con el Modelo Red/Blue/Green
version: 1.7
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-003 v1.4
referencias-minimas: ADR-004, ADR-005, ADR-011, ADR-017, ADR-019
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-003: Seguridad Automática con el Modelo Red/Blue/Green

## Resumen ejecutivo de cambios v1.7

Se añade la definición completa de AgBOM (Agent Bill of Materials) que
el documento usaba desde v1.0 sin explicar nunca — origen real (SBOM,
Executive Order 14028), y el ejemplo JSON ya establecido en sesiones
previas del proyecto, insertado en la sección del Blue Team donde
corresponde por primera vez.

## Resumen ejecutivo de cambios v1.5

Migración del esquema de variantes en Tab. 1: la tabla original mezclaba
costo (Full/Lite) y submodo (Dev/Runtime) sin que el costo aportara
ninguna diferencia real de comportamiento. Se simplifica a un solo eje
(submodo), aplicable uniformemente a las 4 variantes de costo actuales
(`SIGMA-FE/LE/ME/HE`). Se añaden vínculos nuevos con ADR-017
(sandboxing, redactado en esta misma sesión) y ADR-019 (Identidad de
Agentes). **Corrección de terminología (decisión de Marx, no mía):**
el término "Worker" pertenece legítimamente a ADR-019 (concepto
jerárquico-operacional, escalable) — es la unidad de cómputo paralelo
de MapReduce (ADR-002) la que necesita nombre propio, por haber estado
usando "worker" de forma genérica sin definirlo como concepto propio.
Se renombra aquí a **"nodo de cómputo"** (`ComputeNode`).

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
Cada nodo de cómputo (unidad paralela de MapReduce, ADR-002 — antes
llamado "worker" de forma genérica, sin nombre propio) emite evento
AgBOM al iniciar:
  {model_hash, dependency_hashes, compute_node_id}
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

### Tab. 1 — Aplicabilidad de los equipos por submodo

**Corregido (Hito 2, cierre de Rollout 1):** la tabla original mezclaba
variantes de costo (Full/Lite) con submodos (Dev/Runtime) en las mismas
columnas — y en la práctica, Full y Lite nunca se diferenciaban entre sí
(ambas decían "Activo" idéntico en las tres filas). El eje que
realmente determina la aplicabilidad de los 3 equipos es el **submodo**,
no el costo — se simplifica la tabla para reflejar eso, y se aclara que
aplica igual a las 4 variantes de costo (`SIGMA-FE/LE/ME/HE`).

| Equipo | Submodo Dev | Submodo Runtime |
|---|---|---|
| **Red Team** | Desactivado por defecto | Obligatorio antes de pipeline crítico |
| **Blue Team** | Opcional | Activo |
| **Green Team** | Activo | Activo |

Aplica de forma idéntica sobre cualquiera de las 4 variantes de costo
(`SIGMA-FE`, `SIGMA-LE`, `SIGMA-ME`, `SIGMA-HE`) — el submodo, no la
variante, es lo que cambia el comportamiento de seguridad.

### Blue Team — Monitorización mediante AgBOM

**¿Qué es AgBOM y de dónde viene** (definición que faltaba en versiones
anteriores de este documento — se asumía conocida, nunca se explicaba):
**AgBOM = Agent Bill of Materials**, extensión directa de **SBOM
(Software Bill of Materials)** — un inventario formal de componentes de
software (paquetes, versiones, hashes) ya establecido en la industria de
seguridad, exigido en EE. UU. por la Executive Order 14028 para cadenas
de suministro de software. SIGMA lo extiende de "Software" a "Agent":
un inventario equivalente pero de agentes — qué modelo corre, con qué
dependencias exactas, verificable por hash — en vez de solo paquetes.

**Ejemplo real de un AgBOM** (formato ya establecido desde sesiones
previas del proyecto):

```json
{
  "run_id": "sigma-20260717-a1b2c3d4",
  "agents": [
    {
      "id": "data-cleanser-compute-node-01",
      "model": "deepseek-coder:6.7b",
      "model_hash": "sha256:...",
      "dependencies": ["pandas==2.2.1", "pydantic==2.7.0"],
      "dep_hashes": {"pandas": "sha256:...", "pydantic": "sha256:..."},
      "started_at": "2026-06-01T10:00:00Z",
      "status": "running"
    }
  ]
}
```

El campo `id` identifica indistintamente un **nodo de cómputo**
(MapReduce, ADR-002) o un **Worker** (ADR-019 §2.1ter) — el Blue Team no
necesita un esquema distinto para cada uno, ya lo señalamos arriba en
esta misma versión: los trata de forma unificada.

El Blue Team no gestiona un hilo por nodo de cómputo. Cada nodo de
cómputo emite un evento AgBOM al iniciar con su `model_hash` y
`dependency_hashes`. El Blue Team verifica esos hashes contra el AgBOM
de referencia en Langfuse. El límite de nodos de cómputo que puede
manejar es el límite de eventos de Langfuse, no un límite intrínseco
del Blue Team.

**Vínculo con ADR-019 (Identidad de Agentes):** el **Worker** (ADR-019
§2.1ter — subagente efímero para tareas específicas, distinto de los
nodos de cómputo de MapReduce) emite el **mismo evento AgBOM** al
crearse, con su `agent_id` en vez de `compute_node_id`. El Blue Team
los trata de forma unificada — no hace falta un mecanismo de
monitorización distinto para Workers que para nodos de cómputo de
MapReduce.

### Green Team — Recuperación con ciclo de revisión

Todo código generado por auto-refactor pasa obligatoriamente por el skill
`code-reviewer`. Si el impacto es `LOW`, el Green Team lo aplica
automáticamente. Si el impacto es `MEDIUM` o superior, genera un Vibe Diff
con el diff exacto del código y espera aprobación según ADR-004. La cuarentena
preserva el estado forense: el snapshot pre-cuarentena nunca se borra
automáticamente.

**Vínculo con ADR-017 (Sandboxing, nuevo):** el aislamiento del Green
Team ante un fallo ("aísla agente comprometido") y el sandboxing de
ejecución de ADR-017 son mecanismos complementarios, no redundantes —
Green Team actúa *después* de detectado un fallo; ADR-017 previene que
ese fallo tenga radio de explosión *desde el principio*, para código
generado dinámicamente (ADR-014) o Agentes Efímeros (ADR-019).

---

## Consecuencias positivas

- La separación en tres roles elimina conflictos de interés.
- El modelo de pre-vuelo del Red Team garantiza que los datos reales nunca
  se contaminan con ataques simulados.
- El Blue Team escala con cualquier cantidad de nodos de cómputo vía eventos Langfuse.
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
  AgBOM en Langfuse en lugar de hilos por nodo de cómputo.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el diagrama de coordinación de los tres equipos
  respecto al DAG.
- **b** Se añadió Tab. 1 con la aplicabilidad por variante.

**Cambios en v1.5 (Hito 2, cierre de Rollout 1):**
- **a** Tab. 1 migrada del esquema de variantes viejo (Full/Lite/Dev/Runtime
  mezclados) al esquema real — el submodo (Dev/Runtime) es el único eje
  que determina aplicabilidad; se simplificó la tabla y se aclaró que
  aplica igual a las 4 variantes de costo.
- **b** Corrección de terminología (decisión de Marx): la unidad de
  cómputo paralelo de MapReduce (ADR-002), que este documento llamaba
  "worker" de forma genérica, se renombra a "nodo de cómputo" —
  "Worker" pertenece legítimamente a ADR-019 (concepto
  jerárquico-operacional), distinto del "Agente Efímero" (su definición
  epistémica).
- **c** Vínculo nuevo con ADR-017 (sandboxing, redactado en esta misma
  sesión): mecanismos complementarios, Green Team recupera después de un
  fallo, ADR-017 previene el radio de explosión desde el inicio.

**Cambios en v1.7:**
- **a** Se añadió la definición completa de AgBOM (origen SBOM/Executive
  Order 14028, ejemplo JSON real) dentro de la sección del Blue Team —
  el documento lo usaba desde v1.0 sin definirlo nunca.
