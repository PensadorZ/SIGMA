---
skill_id: "0000"
name: system-health-check
version: "2.0.0"
sigma_variant: "Full"
status: active
description: |
  Verifica el estado real de los 5 servicios de infraestructura antes de
  que cualquier otro skill del pipeline se ejecute: PostgreSQL, Redis,
  MinIO, Langfuse y Ollama. Produce un veredicto formal validado con
  Pydantic (HEALTHY/DEGRADED/BLOCKED) junto con run_id y trace_id.
  PostgreSQL y MinIO son críticos — su caída bloquea el pipeline antes
  de gastar cómputo en los skills siguientes. Redis, Langfuse y Ollama
  son opcionales — su caída degrada el veredicto pero nunca bloquea.
activation_keywords:
  - "salud del sistema"
  - "health check"
  - "verificar servicios"
  - "system health"
excluded_from:
  - "ingesta"
  - "limpieza"
  - "análisis de sentimiento"
allowed_tools:
  - Read
max_budget_usd: 0.00
parallelism: none
privacy_mode: relaxed
preconditions: []
input_table: null
output_table: null
langfuse_trace_prefix: "system-health-check"
adr_references:
  - ADR-005
  - ADR-006
  - ADR-007
  - ADR-008
  - ADR-009
  - ADR-010
---

# Skill 0000 — system-health-check

## 1. Propósito

`system-health-check` es el primer skill del pipeline del Hito 1. Corre antes
que cualquier otro y decide si el pipeline debe continuar, continuar con
advertencia, o detenerse de inmediato — sin gastar cómputo en `0001-0011`
cuando la infraestructura no está en condiciones de soportarlos.

**Versión 2.0.0 — Fusión (Opción C, política por defecto):** incorpora sobre
la base ya verificada de esta línea de trabajo (LangGraph, circuit breaker)
el contrato más riguroso de "Eco MultiAgentes 3 Skills 1": veredicto formal
validado con Pydantic, `run_id` además de `trace_id`, y verificación real
—no solo de variables de entorno— de los 5 servicios. Antes de esta fusión,
solo PostgreSQL se verificaba de verdad; Redis, MinIO y Langfuse solo se
comprobaba que sus variables de entorno existieran, no que el servicio
respondiera.

## 2. Clasificación crítico / opcional — decisión de diseño de esta fusión

Ninguna de las dos líneas de trabajo originales tenía esta distinción
explícita. Se definió en el momento de la fusión:

| Servicio | Clasificación | Razón |
|---|---|---|
| PostgreSQL | Crítico — bloquea | Lo usan los 6 skills del Hito 1 |
| MinIO | Crítico — bloquea | Lo usa `0011` al final; bloquear temprano en `0000` evita gastar cómputo en `0001-0008` para fallar recién al final |
| Redis | Opcional — degrada | Ningún skill del Hito 1 lo usa todavía (reservado para el Hito 3 de streaming) |
| Langfuse | Opcional — degrada | `orchestrator.py` ya tiene degradación graceful diseñada (try/except silencioso) |
| Ollama | Opcional — degrada | `0011` tiene fallback (`summary_provider: none`) si no responde |

## 3. Comportamiento — Gherkin

Ver `tests/test_system_health_check.feature`. Cubre: todos los servicios
arriba (HEALTHY), un servicio crítico caído (BLOCKED), servicios opcionales
caídos individualmente y en conjunto (DEGRADED, nunca bloquea), consistencia
interna del veredicto, servicios lentos que no deben colgar el arranque, y
modo Dev que nunca debe tocar infraestructura real.

## 4. Propiedades LTL

```text
-- [Safety-1] Un servicio crítico caído siempre produce BLOCKED.
G (algun_critico_caido → verdict = BLOCKED)

-- [Safety-2] Solo servicios opcionales caídos nunca produce BLOCKED.
G (solo_opcionales_caidos → verdict ≠ BLOCKED)

-- [Consistency] El veredicto nunca es HEALTHY si algo está caído.
G (algo_caido → verdict ≠ HEALTHY)

-- [Liveness-1] Cada verificación de servicio tiene timeout — nunca
--              se cuelga esperando una respuesta que no llega.
G (verificar_servicio → F (respuesta_recibida ∨ timeout_alcanzado))

-- [Isolation] En modo Dev, ningún check real de infraestructura se invoca.
G (sigma_variant = Dev → ¬invocar_check_real)
```

## 5. Restricciones epistémicas (K ⊆ X)

El veredicto se construye exclusivamente a partir de las respuestas reales
de los 5 servicios verificados. No se infiere el estado de un servicio no
verificado, ni se asume disponibilidad por ausencia de error explícito —
cada `ServiceCheckResult` requiere una respuesta positiva confirmada
(`ping`, `list_buckets`, HTTP 200) para marcarse `available=True`.

## 6. Trazabilidad Langfuse

| Evento | Momento | Campos obligatorios |
|---|---|---|
| `system-health-check.start` | Inicio | trace_id, run_id, sigma_variant |
| `system-health-check.success` | Cierre HEALTHY/DEGRADED | verdict, services, duration_ms |
| `system-health-check.error` | Cierre BLOCKED | verdict_reason, critical_services_down |

## 7. ADRs aplicables

| ADR | Aplicación |
|---|---|
| ADR-005 | Policy Server: `0000` es el punto de entrada que decide si el resto del pipeline puede tocar infraestructura |
| ADR-006 | `trace_id` y `run_id` resueltos por ContextResolver |
| ADR-007 | `verdict` y la clasificación crítico/opcional son la Dimensión 1 aplicada a nivel de infraestructura |
| ADR-008 | K ⊆ X: el veredicto solo refleja respuestas reales verificadas |
| ADR-009 | Este archivo sigue el formato canónico de 5+ archivos |
| ADR-010 | Variables críticas vía `get_required_env()`, fallo inmediato si faltan |

## 8. Historial de resolución

**v2.0.0 (fusión inicial):** la clasificación crítico/opcional quedó
hardcodeada en `skill.py`, documentada solo referencialmente en
`defaults.yaml`. **v2.0.1 (este cierre):** la clasificación ahora se
resuelve realmente desde `defaults.yaml` (`services.critical` /
`services.optional`) en tiempo de ejecución — cambiar qué servicio es
crítico ya no requiere tocar código, solo configuración.
