# Contrato de output — 0004-statistical-validator

> `references/schemas.md` · SIGMA v1.5 · Hito 2, Engineer Datos
> Autor: Prof. Marx Agustín García Delgado · Versión: 1.0.0
> Referenciado por D2 (Corrección funcional) de ADR-007 y por la Capa 2
> (verificación Pydantic) de ADR-008.


```python
from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator

Verdict = Literal["INSUFFICIENT_EVIDENCE", "PAUSED_HITL", "APPROVED_WITH_WARNINGS", "REJECTED"]
Branch = Literal[
    "bayes_factor", "permutation_bootstrap", "adf_granger", "bayesian_ab",
    "descriptive_fallback", "drift_ks_test", "leakage_correlation",
]

class StatisticalValidatorOutput(BaseModel):
    verdict: Verdict
    branch: Branch
    statistic: float | None = Field(
        default=None,
        description="Estadístico crudo (BF10, KS, t, ADF, correlación...). "
                     "None solo es válido para bayesian_ab.",
    )
    p_value: float | None = Field(default=None, ge=0.0, le=1.0)
    detail: dict[str, Any] = Field(
        description="Metadatos de la rama ejecutada — nunca interpretación "
                     "narrativa del resultado, solo valores numéricos y de "
                     "configuración (ADR-008)."
    )

    @model_validator(mode="after")
    def check_approved_only_from_adf_granger(self):
        if self.verdict == "APPROVED_WITH_WARNINGS" and self.branch != "adf_granger":
            raise ValueError(
                "OUTPUT_SCHEMA_VIOLATION: APPROVED_WITH_WARNINGS solo es "
                "válido en la rama adf_granger"
            )
        return self

    @model_validator(mode="after")
    def check_rejected_only_from_leakage(self):
        if self.verdict == "REJECTED" and self.branch != "leakage_correlation":
            raise ValueError(
                "OUTPUT_SCHEMA_VIOLATION: REJECTED solo es válido en la "
                "rama leakage_correlation"
            )
        return self
```

## Regla de validación cruzada (Capa 2, ADR-008)

Dos reglas, ambas traducción directa de las propiedades LTL de `SKILL.md`:
`APPROVED_WITH_WARNINGS` solo desde `adf_granger`; `REJECTED` solo desde
`leakage_correlation`. Cualquier otra combinación es
`OUTPUT_SCHEMA_VIOLATION` y el pipeline se detiene.
