# references/schemas.md — 0000-system-health-check v1.0.0

## HealthCheckOutput

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional


class ServiceStatus(BaseModel):
    name: str
    category: Literal["critical", "conditional_critical", "optional"]
    status: Literal["UP", "DOWN", "SKIPPED"]
    response_ms: Optional[int] = None
    error: Optional[str] = None
    affected_skills: list[str] = Field(default_factory=list)
    available_alternative: Optional[str] = None
    remediation_step: Optional[str] = None


class HealthCheckOutput(BaseModel):
    """
    Schema de validación del output de system-health-check.
    El Orquestador lee el campo verdict para decidir si el
    pipeline puede arrancar.
    """
    trace_id: str
    run_id: str
    sigma_variant: Literal["Full", "Lite", "Dev", "Runtime"]
    verdict: Literal["HEALTHY", "DEGRADED", "BLOCKED"]
    verdict_reason: str

    services: list[ServiceStatus]
    critical_services_up: list[str]
    critical_services_down: list[str]
    optional_services_down: list[str]
    affected_skills: list[str] = Field(default_factory=list)

    duration_ms: int

    @field_validator("critical_services_down")
    @classmethod
    def blocked_if_critical_down(cls, v, values):
        if v and values.data.get("verdict") != "BLOCKED":
            raise ValueError(
                "Si hay servicios críticos caídos, el veredicto debe ser BLOCKED"
            )
        return v
```

## Uso en el Orquestador

```python
from skills.system_health_check.references.schemas import HealthCheckOutput

report = HealthCheckOutput.model_validate(raw)

if report.verdict == "BLOCKED":
    graph.stop_pipeline(reason=report.verdict_reason)
elif report.verdict == "DEGRADED":
    graph.continue_with_warnings(degraded_services=report.optional_services_down)
else:
    graph.continue_pipeline()
```
