---
id: ADR-011
titulo: Trazabilidad de Pipelines en Langfuse V2
version: 1.6
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-011 v1.5
referencias-minimas: ADR-003, ADR-005, ADR-007, ADR-009
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-011: Trazabilidad de Pipelines en Langfuse V2

## Resumen ejecutivo de cambios v1.6

Tres correcciones (Hito 2, cierre de Rollout 1): "worker" renombrado a
"nodo de cómputo" en Fig. 1 y contexto; Tab. 1 corregida al esquema
real de variantes de costo separado de submodo; y una nota de
implementación verificada — un bug real encontrado con evidencia de
base de datos (`client.event()` sin `client.trace()` previo deja
`observations` huérfanas de su `trace` correspondiente), ya corregido
en `tracing.py`.

## Resumen ejecutivo de cambios v1.5

Se amplía la sección de Contexto para explicar primero que esta
trazabilidad es lo que permite correlacionar las decisiones del Policy
Server (ADR-005), las verificaciones del Blue Team (ADR-003) y las
evaluaciones 7D (ADR-007) bajo un mismo `trace_id` — antes de entrar al
detalle de la jerarquía de trazas.

## Resumen ejecutivo de cambios v1.4

Se fija (pin) la imagen Docker de Langfuse a la etiqueta `:2` y se declara
la restricción `langfuse<3` en `requirements.txt` como constraints críticos:
el servidor autoalojado v2 carece de endpoint OTLP (OpenTelemetry Protocol), 
por lo que el SDK v3 (que lo requiere) es incompatible. Hallazgo verificado 
durante el Hito 1.

---

## Contexto

La trazabilidad en Langfuse es el ojo común que permite auditar todo lo
demás: sin ella, las decisiones del Policy Server (ADR-005), las
verificaciones AgBOM del Blue Team (ADR-003) y las evaluaciones de las
7 dimensiones (ADR-007) existirían como eventos aislados, sin forma de
correlacionarlos entre sí bajo un mismo `trace_id`, ni de reconstruir
después qué pasó realmente durante una ejecución. Es, en ese sentido, la
capa de memoria de auditoría a corto plazo que complementa a la Memoria
Epistémica de largo plazo (ADR-001).

Un sistema multiagente sin observabilidad es una caja negra. Cuando un
pipeline falla se necesita saber qué herramientas se ejecutaron, cuántos
tokens se consumieron, qué modelo ejecutó qué subtarea, en qué nodo de
cómputo falló y cuánto tardó cada etapa. Langfuse V2 es el backend de
observabilidad elegido por ser open source y autoalojable.

---

## Decisión

Toda ejecución emite trazas estructuradas a Langfuse V2 siguiendo una
jerarquía consistente y predecible.

### Fig. 1 — Jerarquía completa de trazas en Langfuse

```
NIVEL 0 — Trace padre (pipeline completo)
  └─ id: {run_id}
  └─ tags: [sigma_variant, sigma_env]
  └─ session_id: {pipeline_run_id}

NIVEL 1 — Spans hijos del trace padre
  ├─ Span: orchestrator.plan
  ├─ Span: skill.{skill_id}              ← Un span por skill
  ├─ Span: red_team_probe                ← Sub-grafo del Red Team
  └─ Artefactos: evaluaciones 7D (ADR-007)

NIVEL 2 — Hijos de cada skill span
  ├─ Generation: llm.{model_name}        ← Llamada al LLM
  ├─ Event: tool.{tool_name}             ← Llamada a herramienta
  ├─ Event: policy_server.decision       ← Decisión del Policy Server
  │    └─ payload: {verdict, layer, rule, timestamp}
  ├─ Span: blue_team_agbom               ← Verificación AgBOM
  │    └─ payload: {model_hash, dep_hashes, result}
  └─ Span: mapreduce.compute_node.{n}     ← Nodo de cómputo individual

NIVEL 3 — Hijos de cada span de nodo de cómputo
  ├─ Event: tool.{tool_name}
  └─ Generation: llm.{model_name}

TRANSVERSAL — Decisiones del Policy Server
  Cada decisión (permitida o bloqueada) emite un Event a NIVEL 2
  con el mismo trace_id del pipeline activo. Esto implementa la
  intención de auditoría declarada en ADR-005.
```

### Tab. 1 — Política de retención de trazas por variante

**Corregido (Hito 2):** separado en los dos ejes reales — variante de
costo y submodo, antes mezclados en las mismas filas.

| Variante de costo | Retención por defecto | Configurable en |
|---|---|---|
| **SIGMA-FE** | 30 días | `docker-compose.yml` |
| **SIGMA-LE** | 30 días | `docker-compose.yml` |
| **SIGMA-ME** | Según plan cloud de Langfuse | Configuración del proveedor |
| **SIGMA-HE** | Según plan cloud de Langfuse | Configuración del proveedor |

**Submodo Dev (cualquier variante):** 7 días. **Submodo Runtime:**
90 días mínimo, sin importar la variante de costo activa.

### Constraints de versión — Langfuse v2 pinned (crítico)

El despliegue autoalojado (SIGMA-FE/LE) usa **Langfuse V2**, y su versión
debe estar fijada explícitamente en ambos extremos:

```yaml
# docker-compose.yml — NUNCA usar :latest
services:
  langfuse:
    image: langfuse/langfuse:2        # pin explícito a la serie v2
```

```text
# requirements.txt — constraint crítico
langfuse<3
```

**Razón verificada en el Hito 1:** el SDK de Langfuse v3 exige un endpoint
OTLP que el servidor autoalojado v2 no expone. Usar
`:latest` en la imagen o instalar `langfuse>=3` en el cliente rompe la
trazabilidad silenciosamente. La migración a Langfuse v3 requeriría desplegar
el servidor v3 completo y queda fuera del alcance del Hito 1 y 2.

### Nota de implementación verificada (Hito 2, cierre de Rollout 1)

Se detectó, con evidencia directa de base de datos (360 `observations`
guardadas, solo 6 `traces`), que llamar a `client.event(trace_id=...)`
directamente sobre el cliente Langfuse v2 **sin haber creado antes el
trace vía `client.trace(id=...)`** guarda el evento pero deja huérfana
la fila correspondiente en la tabla `traces` — la UI de Langfuse lista
desde `traces`, no desde `observations`, así que nada aparecía visible
pese a que los datos sí llegaban. Corregido en `tracing.py`:
`client.trace(id=trace_id)` (upsert) antes de `.event()` sobre ese
objeto, en cada emisión. La jerarquía de Fig. 1 describe el diseño
correcto; este hallazgo documenta que el código no lo cumplía hasta
esta corrección.

### Política de último recurso ante caída simultánea

Si Langfuse no está disponible, los eventos se encolan en Redis. Si Redis
tampoco está disponible, los eventos se escriben en archivos de log local
con rotación diaria y retención de 7 días en el directorio `sigma_fallback_logs`.
El script `scripts/reconcile_logs.py` puede ejecutarse manualmente para
reenviar los logs a Langfuse cuando los servicios se restauren. El pipeline
**no falla** por indisponibilidad de Langfuse.

---

## Consecuencias positivas

- La jerarquía predecible hace la depuración sistemática: siempre se sabe
  dónde buscar cada tipo de información.
- La degradación elegante garantiza que los pipelines no fallan por problemas
  de conectividad con Langfuse.
- La auditoría del Policy Server y del Blue Team en el mismo sistema facilita
  la correlación de eventos.

## Consecuencias negativas

- Langfuse V2 requiere PostgreSQL adicional en el stack, en cualquier
  variante autoalojada.
- En entornos con VPN o redes restringidas, la configuración del túnel puede
  ser compleja.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| LangSmith (LangChain) | Servicio de pago; no autoalojable en ninguna variante |
| OpenTelemetry + Jaeger | Requiere más configuración para casos de uso de LLMs |
| Logs planos en archivos | No permite consultas ni correlación de trazas |
| W&B Weave | Menos adecuado para trazas de agentes y herramientas |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se añadió que las decisiones del Policy Server se trazan como
  eventos con el `trace_id` del pipeline activo.
- **b.1.2** Se especificó la estructura de trazas para el sub-grafo del Red
  Team con tag `red_team_probe`.
- **c.1.2** Se especificó la estructura de trazas para el Blue Team con tag
  `blue_team_agbom`.
- **d.1.2** Se añadió la política de último recurso con log local cuando
  Langfuse y Redis están caídos simultáneamente.

**Cambios en v1.3:**
- **a.1.3** Se añadió Fig. 1 con la jerarquía completa de trazas en Langfuse
  detallando todos los niveles.
- **b.1.3** Se añadió Tab. 1 con la política de retención de trazas por
  variante.

**Cambios en v1.4:**
- **a** Se fijó la imagen Docker de Langfuse a la etiqueta `:2` (nunca
  `:latest`) y se declaró la restricción `langfuse<3` en `requirements.txt`,
  por la incompatibilidad OTLP del SDK v3 con el servidor autoalojado v2.
  Hallazgo verificado durante el Hito 1.

**Cambios en v1.6 (Hito 2, cierre de Rollout 1):**
- **a** "worker" renombrado a "nodo de cómputo" — consistente con
  ADR-002 (ya corregido en esta sesión).
- **b** Tab. 1 corregida a los 4 niveles reales de variante de costo,
  separados del submodo Dev/Runtime.
- **c** Añadida nota de implementación verificada sobre el bug real de
  `client.event()` sin `client.trace()` previo (observations huérfanas),
  ya corregido en `tracing.py`.
