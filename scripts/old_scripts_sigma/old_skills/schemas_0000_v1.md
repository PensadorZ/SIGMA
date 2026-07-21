# schemas.md — Skill 0000: system-health-check

**NOTA:** este archivo reemplaza uno heredado de "Eco MultiAgentes 3 Skills
1" que describía un `skill.py` distinto. Documenta el contrato real de la
v2.0.0 fusionada, presente en este proyecto.

## ServiceStatus (Pydantic)

```python
class ServiceStatus(BaseModel):
    service: str
    available: bool
    critical: bool
    latency_ms: int
    error: str | None = None
```

## HealthCheckOutput (Pydantic)

```python
class HealthCheckOutput(BaseModel):
    trace_id: str
    run_id: str
    sigma_variant: Literal["Full", "Lite", "Dev", "Runtime"]
    verdict: Literal["HEALTHY", "DEGRADED", "BLOCKED"]
    verdict_reason: str
    services: list[ServiceStatus]
    critical_services_down: list[str]
    optional_services_down: list[str]
    duration_ms: int
```

`HealthCheckOutput.model_dump()` es lo que efectivamente viaja dentro de
`SkillResult.output` — no se expone el objeto Pydantic directamente al
resto del pipeline, para mantener el contrato genérico `SkillResult` sin
acoplar a los demás skills a un tipo específico de este.

## Traducción a SkillResult

| `verdict` | `SkillResult.status` | `output` |
|---|---|---|
| `HEALTHY` | `success` | `HealthCheckOutput.model_dump()` completo |
| `DEGRADED` | `success_with_warnings` | Igual, más `warnings=['degraded:{servicio}', ...]` |
| `BLOCKED` | `error` | **Vacío** (`{}`) — el detalle va en `error_detail`, no en `output`. Este es el contrato general de `make_error()` en todo el proyecto, no una excepción de este skill. |

## Excepciones

```python
class ConfigurationError(Exception):
    """Variable de entorno crítica ausente, o PostgreSQL inalcanzable
    en el chequeo previo a la construcción del veredicto formal."""

class InfrastructureBlockedError(Exception):
    """Al menos un servicio crítico (PostgreSQL o MinIO) no responde.
    El detalle de qué servicio(s) y por qué va en error_detail,
    construido a partir de HealthCheckOutput.verdict_reason."""
```

## Campo de compatibilidad

`output_dict["health_status"]` se mantiene como alias de `verdict` por si
algún consumidor externo (evals, dashboards) todavía lee ese nombre de
campo de una versión anterior. Pendiente de auditar si algo lo usa
realmente antes de removerlo en una versión futura.
