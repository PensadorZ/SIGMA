# tests/test_statistical_validator.feature — 0004-statistical-validator v1.0.0
# SIGMA v1.5 · Hito 2, Engineer Datos (ADR-016 Tab. 2, Rollout 1)
# Sintaxis Gherkin estricta — cada step en una sola linea.

# language: es

Característica: Validación estadística con selección de prueba, drift y leakage
  Como Engineer Datos
  Quiero seleccionar la prueba correcta, detectar drift y detectar leakage
  Para emitir un veredicto honesto sin exceder K ⊆ X

  Contexto:
    Dado que el input fue validado por 0002-data-cleanser
    Y que policies.yaml está disponible

  @happy_path @bayes_factor
  Escenario: Hipótesis explícita con evidencia insuficiente
    Dado un DataFrame validado con dos grupos y una hipótesis explícita declarada
    Y policies.yaml define un bayes_factor_min alto
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-001" en modo significancia
    Entonces la rama seleccionada es "bayes_factor"
    Y el veredicto es "INSUFFICIENT_EVIDENCE"

  @happy_path @adf_granger @strong_verdict
  Escenario: Serie temporal produce el único veredicto fuerte permitido
    Dado un DataFrame validado con índice temporal
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-002" en modo significancia
    Entonces la rama seleccionada es "adf_granger"
    Y el veredicto es "APPROVED_WITH_WARNINGS"

  @paused_hitl @permutation
  Escenario: Sin hipótesis y distribución desconocida escala a HITL si el IC es ancho
    Dado un DataFrame validado sin hipótesis y distribución desconocida
    Y policies.yaml define un permutation_ci_width_max bajo
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-003" en modo significancia
    Entonces la rama seleccionada es "permutation_bootstrap"
    Y el veredicto es "PAUSED_HITL"

  @bayesian_ab
  Escenario: Entorno vivo con pocas muestras es evidencia insuficiente
    Dado un DataFrame con feedback en vivo con menos muestras que el mínimo configurado
    Y policies.yaml define un bayesian_ab_min_samples
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-004" en modo significancia
    Entonces la rama seleccionada es "bayesian_ab"
    Y el veredicto es "INSUFFICIENT_EVIDENCE"

  @fallback
  Escenario: Ninguna condición aplica y cae al fallback descriptivo
    Dado un DataFrame validado sin hipótesis, sin índice temporal y sin feedback en vivo
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-005" en modo significancia
    Entonces la rama seleccionada es "descriptive_fallback"

  @error @policy_configuration @critical
  Escenario: Modo A sin umbral aprobado en policies.yaml falla rápido
    Dado un DataFrame validado con dos grupos y una hipótesis explícita declarada
    Y policies.yaml no define bayes_factor_min
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-006" en modo significancia
    Entonces retorna status "error"
    Y el error menciona "PolicyConfigurationError"

  @drift @ks_test @critical
  Escenario: Detección de drift usa KS-test, nunca PSI
    Dado un DataFrame actual y un DataFrame baseline con distribuciones distintas
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-007" en modo drift
    Entonces el método usado es "ks_test"
    Y el veredicto es "PAUSED_HITL"

  @leakage @rejected
  Escenario: Detección de leakage rechaza directo si la correlación supera el umbral
    Dado un DataFrame con una columna casi idéntica a la columna objetivo
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-008" en modo leakage
    Entonces la rama seleccionada es "leakage_correlation"
    Y el veredicto es "REJECTED"

  @error @non_recoverable
  Escenario: Error no recuperable por input sin validar
    Dado un estado sin la clave "df" validada por 0002-data-cleanser
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-009" en modo significancia
    Entonces retorna status "error"
    Y el error menciona "InputSchemaError"

  @error @non_recoverable
  Escenario: Error no recuperable por muestra insuficiente
    Dado un DataFrame validado con hipótesis explícita pero menos de 2 filas por grupo
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-010" en modo significancia
    Entonces retorna status "error"
    Y el error menciona "InsufficientSampleSizeError"

  @dev_mode
  Escenario: Modo Dev con datos sintéticos
    Dado un estado con sigma_variant en "Dev"
    Y un DataFrame sintético generado localmente sin infraestructura real
    Cuando se ejecuta statistical-validator con trace_id "wc-sv-011" en modo significancia
    Entonces retorna status "success"
    Y el output indica dev_mode True
