---
id: ADR-005
titulo: Policy Server Híbrido — Estructural y Semántico
version: 1.3
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-005 v1.2
referencias-minimas: ADR-003, ADR-004, ADR-006, ADR-010, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-005: Policy Server Híbrido — Estructural y Semántico

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el flujo de intercepción completo. Se añade Tab. 1 con la
asignación de modelos LLM por variante. Se incorpora el histórico de versiones.

---

## Contexto

Cada herramienta que SIGMA puede ejecutar representa un vector de riesgo. Las
restricciones necesarias son de dos tipos: estructurales (reglas deterministas)
y semánticas (requieren comprensión del contexto). Una capa única no puede
resolver ambas eficientemente.

---

## Decisión

Implementar un Policy Server en dos capas secuenciales. Toda llamada a
herramienta pasa por la capa estructural primero. Solo si supera esa capa y
existe ambigüedad pasa a la capa semántica.

### Fig. 1 — Flujo de intercepción del Policy Server

```
Agente solicita herramienta
        │
        ▼
¿Hash de policies.yaml cambió? ──SÍ──→ Recarga en caliente (sin reinicio)
        │ NO (o tras recarga)
        ▼
CAPA ESTRUCTURAL (policies.yaml)
  Verifica: rol, entorno, recurso
  Latencia: < 5 ms
  Cubre: 95% de llamadas
        │
        ├─ BLOQUEA ──→ Evento Langfuse (trace_id) → FIN
        │
        ├─ PERMITE (caso determinista) ──→ Evento Langfuse → Ejecución
        │
        └─ AMBIGUO ──→ CAPA SEMÁNTICA
                              │
                        LLM juez (modelo ≠ Orquestador)
                        Detecta: PII, credenciales, desviación de intención
                        Veredicto: {verdict, confidence, reason, evidence}
                              │
                              ├─ confidence < 0.7 ──→ Escalar a HITL (ADR-004)
                              ├─ BLOQUEA ──→ Evento Langfuse → FIN
                              └─ PERMITE ──→ Evento Langfuse → Ejecución

¿Policy Server no responde en 100 ms? ──→ FAIL-CLOSED
  Bloqueo automático + POLICY_SERVER_TIMEOUT en Langfuse
  Excepción: SIGMA Dev puede configurar fail-open en policies.yaml
```

### Tab. 1 — Asignación del modelo LLM juez por variante y Orquestador

El juez semántico es **siempre un modelo diferente al Orquestador** para
evitar el conflicto de interés donde un modelo comprometido juzga sus propias
acciones.

| Variante | Modelo del Orquestador | Modelo del juez semántico |
|---|---|---|
| **SIGMA Full** (opción A) | Gemini API (free tier) | `mistral` local vía Ollama |
| **SIGMA Full** (opción B) | Ollama local | Gemini API (free tier) |
| **SIGMA Lite** | Gemini Pro | Gemini Flash u otro modelo de menor coste |
| **SIGMA Dev** | Cualquiera | Capa semántica desactivada (solo estructural) |
| **SIGMA Runtime** | Según entorno | Misma lógica que Full o Lite |

### Contexto de políticas para el sub-grafo del Red Team

Cuando el Policy Server detecta el tag `red_team_probe` en el contexto de
LangGraph, aplica `red_team_policies.yaml` en lugar de `policies.yaml`. Esto
permite al Red Team inyectar dependencias maliciosas simuladas sin ser bloqueado.

### Recarga en caliente

El Policy Server verifica el hash SHA-256 de `policies.yaml` en cada
evaluación estructural. Si cambió, recarga el archivo completo sin reiniciar.
`allowed_packages.yaml` sigue el mismo mecanismo. Los cambios son efectivos
inmediatamente en nuevas llamadas sin afectar evaluaciones en curso.

### Prevención de slopsquatting

Cualquier solicitud de instalación de paquete no presente en
`allowed_packages.yaml` es bloqueada por la capa estructural sin evaluación
semántica.

---

## Consecuencias positivas

- El 95% de llamadas se resuelven con latencia mínima.
- La separación de modelos elimina el conflicto de interés.
- El `fail-closed` garantiza que un Policy Server caído no abre el sistema.
- La recarga en caliente evita interrupciones por cambios de política.
- La auditoría en Langfuse permite reconstruir cualquier decisión de gobernanza.

## Consecuencias negativas

- `policies.yaml` debe mantenerse actualizado cuando se añaden nuevas
  herramientas o roles.
- La recarga en caliente puede introducir inconsistencias mínimas si el
  archivo cambia mientras hay evaluaciones en curso (improbable dado que
  las evaluaciones estructurales duran < 5 ms).

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Solo capa estructural | No detecta violaciones semánticas |
| Solo capa semántica en todas las llamadas | Latencia y coste prohibitivos |
| Validación solo en input del Orquestador | No intercepta herramientas de subagentes |
| WAF externo | Dependencias fuera del ecosistema SIGMA |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se declaró que el LLM juez debe ser un modelo diferente al
  Orquestador.
- **b.1.2** Se estableció `fail-closed` como comportamiento por defecto con
  excepción configurable en SIGMA Dev.
- **c.1.2** Se añadió auditoría de decisiones en Langfuse con el `trace_id`
  activo.
- **d.1.2** Se especificó el contexto de políticas relajadas para el sub-grafo
  del Red Team mediante `red_team_policies.yaml`.
- **e.1.2** Se añadió recarga en caliente de `policies.yaml` y
  `allowed_packages.yaml` mediante hash SHA-256.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el flujo completo de intercepción incluyendo
  el `fail-closed` y la recarga en caliente.
- **b** Se añadió Tab. 1 con la asignación de modelos LLM juez por variante
  y modelo de Orquestador.
