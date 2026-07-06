# tests/test_skill.feature — 0000-system-health-check v1.0.0

Feature: Verificación de salud de la infraestructura antes del pipeline

  Background:
    Given el entorno SIGMA está inicializado
    And las variables de entorno están cargadas desde .env

  Scenario: Todos los servicios UP — veredicto HEALTHY
    Given PostgreSQL responde en 120 ms
    And Redis responde en 8 ms
    And MinIO responde en 95 ms
    And Langfuse responde en 210 ms
    And Ollama responde en 340 ms
    When el skill system-health-check se ejecuta con run_id "hc-t001" y trace_id "tr-hc-001"
    Then el veredicto es "HEALTHY"
    And el informe lista 5 servicios con status "UP"
    And critical_services_down está vacío
    And el evento "health_check.completed" fue emitido con verdict: "HEALTHY"
    And el pipeline puede continuar

  Scenario: Ollama caído sin impacto en el pipeline — DEGRADED
    Given PostgreSQL, Redis, MinIO y Langfuse responden correctamente
    And Ollama NO responde (timeout a los 5000 ms)
    And el pipeline YAML no requiere skills con modelos Ollama
    When el skill system-health-check se ejecuta con run_id "hc-t002" y trace_id "tr-hc-002"
    Then el veredicto es "DEGRADED"
    And el informe muestra ollama con status: "DOWN"
    And affected_skills está vacío
    And el evento "health_check.service_degraded" fue emitido con service: "ollama"
    And el pipeline continúa

  Scenario: PostgreSQL caído — BLOCKED
    Given PostgreSQL NO responde después de 2 reintentos
    And Redis y MinIO responden correctamente
    When el skill system-health-check se ejecuta con run_id "hc-t003" y trace_id "tr-hc-003"
    Then el veredicto es "BLOCKED"
    And critical_services_down contiene "postgresql"
    And se emite "health_check.blocked" con trace_id: "tr-hc-003"
    And se dispara notificación BurntToast -Tipo "alerta"
    And el pipeline NO continúa

  Scenario: Modo Dev — MinIO y Langfuse opcionales
    Given SIGMA_ENV es "Dev"
    And PostgreSQL y Redis responden correctamente
    And MinIO NO responde
    And Langfuse NO responde
    When el skill system-health-check se ejecuta con run_id "hc-t004" y trace_id "tr-hc-004"
    Then el veredicto es "HEALTHY"
    And el informe indica que MinIO y Langfuse son opcionales en Dev
    And el pipeline continúa normalmente

  Scenario: Variable de entorno faltante
    Given POSTGRES_URL no está definida en .env
    When el skill system-health-check se ejecuta con run_id "hc-t005"
    Then el skill termina con MissingConfigurationError
    And el mensaje indica variable faltante: "POSTGRES_URL"
    And se emite "health_check.configuration_error"
