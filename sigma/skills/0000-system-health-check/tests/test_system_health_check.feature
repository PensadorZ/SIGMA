# tests/test_system_health_check.feature — 0000-system-health-check v2.0.0
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2 — fusión Opción C
# Reemplaza test_skill.feature heredado de otra línea de trabajo, que
# describía un skill.py distinto. Sintaxis Gherkin estricta.

# language: es

Característica: Veredicto de salud del sistema con verificación real de 5 servicios
  Como Orquestador de SIGMA
  Quiero un veredicto HEALTHY/DEGRADED/BLOCKED antes de correr el resto del pipeline
  Para no gastar cómputo en skills posteriores si la infraestructura no responde

  Contexto:
    Dado que el entorno tiene SIGMA_VARIANT configurado
    Y que las variables de entorno críticas están presentes

  @happy_path @hito1
  Escenario: Todos los servicios responden — veredicto HEALTHY
    Dado que los 5 servicios responden correctamente
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca system-health-check con trace_id "wc-hc-001"
    Entonces el veredicto es "HEALTHY"
    Y retorna status "success"
    Y el output incluye run_id y trace_id

  @blocked @critical
  Escenario: PostgreSQL caído bloquea el pipeline
    Dado que PostgreSQL no responde
    Y que los demás servicios responden correctamente
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca system-health-check con trace_id "wc-hc-002"
    Entonces el veredicto es "BLOCKED"
    Y retorna status "error"
    Y el error menciona "postgres"

  @blocked @critical
  Escenario: MinIO caído bloquea el pipeline
    Dado que MinIO no responde
    Y que los demás servicios responden correctamente
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca system-health-check con trace_id "wc-hc-003"
    Entonces el veredicto es "BLOCKED"
    Y retorna status "error"
    Y el error menciona "minio"

  @degraded @optional
  Escenario: Redis caído solo degrada, nunca bloquea
    Dado que Redis no responde
    Y que los demás servicios responden correctamente
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca system-health-check con trace_id "wc-hc-004"
    Entonces el veredicto es "DEGRADED"
    Y retorna status "success_with_warnings"

  @degraded @optional
  Escenario: Todos los opcionales caídos a la vez siguen sin bloquear
    Dado que Redis no responde
    Y que Langfuse no responde
    Y que Ollama no responde
    Y que PostgreSQL y MinIO responden correctamente
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca system-health-check con trace_id "wc-hc-005"
    Entonces el veredicto es "DEGRADED"
    Y retorna status "success_with_warnings"

  @dev_mode
  Escenario: Modo Dev nunca toca infraestructura real
    Dado que SIGMA_VARIANT es "Dev"
    Cuando el Orquestador invoca system-health-check con trace_id "wc-hc-006"
    Entonces el veredicto es "HEALTHY"
    Y el output indica dev_mode True
    Y ningún chequeo real de infraestructura fue invocado
