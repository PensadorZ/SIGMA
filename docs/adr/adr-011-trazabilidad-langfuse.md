---
id: ADR-011
titulo: Trazabilidad de Pipelines en Langfuse V2
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-011 v1.3
referencias-minimas: ADR-003, ADR-005, ADR-007, ADR-009
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-011: Trazabilidad de Pipelines en Langfuse V2

## Resumen ejecutivo de cambios v1.4

Se fija (pin) la imagen Docker de Langfuse a la etiqueta `:2` y se declara
la restricción `langfuse<3` en `requirements.txt` como constraints críticos:
el servidor autoalojado v2 carece de endpoint OTLP, por lo que el SDK v3
(que lo requiere) es incompatible. Hallazgo verificado durante el Hito 1.

---

## Contexto

Un sistema multiagente sin observabilidad es una caja negra. Cuando un
pipeline falla se necesita saber qué herramientas se ejecutaron, cuántos
tokens se consumieron, qué modelo ejecutó qué subtarea, en qué worker falló
y cuánto tardó cada etapa. Langfuse V2 es el backend de observabilidad
elegido por ser open source y autoalojable.

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
  └─ Span: mapreduce.worker.{n}          ← Worker individual

NIVEL 3 — Hijos de cada worker span
  ├─ Event: tool.{tool_name}
  └─ Generation: llm.{model_name}

TRANSVERSAL — Decisiones del Policy Server
  Cada decisión (permitida o bloqueada) emite un Event a NIVEL 2
  con el mismo trace_id del pipeline activo. Esto implementa la
  intención de auditoría declarada en ADR-005.
```

### Tab. 1 — Política de retención de trazas por variante

| Variante | Retención por defecto | Configurable en |
|---|---|---|
| **SIGMA Full** | 30 días | `docker-compose.yml` |
| **SIGMA Lite** | Según plan cloud de Langfuse | Configuración del proveedor |
| **SIGMA Dev** | 7 días | `docker-compose.yml` |
| **SIGMA Runtime** | 90 días mínimo | `docker-compose.yml` |

### Constraints de versión — Langfuse v2 pinned (crítico)

El despliegue autoalojado de SIGMA Full usa **Langfuse V2**, y su versión
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
OTLP (OpenTelemetry Protocol) que el servidor autoalojado v2 no expone. Usar
`:latest` en la imagen o instalar `langfuse>=3` en el cliente rompe la
trazabilidad silenciosamente. La migración a Langfuse v3 requeriría desplegar
el servidor v3 completo y queda fuera del alcance del Hito 1 y 2.

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

- Langfuse V2 requiere PostgreSQL adicional en el stack de SIGMA Full.
- En entornos con VPN o redes restringidas, la configuración del túnel puede
  ser compleja.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| LangSmith (LangChain) | Servicio de pago; no autoalojable en SIGMA Full |
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
