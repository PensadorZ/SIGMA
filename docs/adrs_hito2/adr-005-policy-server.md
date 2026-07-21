---
id: ADR-005
titulo: Policy Server Híbrido — Estructural y Semántico
version: 1.5
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-005 v1.4
referencias-minimas: ADR-003, ADR-004, ADR-006, ADR-010, ADR-011, ADR-017, ADR-019
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-005: Policy Server Híbrido — Estructural y Semántico

## Resumen ejecutivo de cambios v1.5

Tab. 1 corregida al esquema real de variantes (antes mezclaba costo y
submodo, y nunca cubrió `SIGMA-ME`/`HE`). Se añaden dos vínculos nuevos,
verificados contra ADRs redactados en esta misma sesión: `ADR-017`
extiende la capa estructural de este documento al momento de arranque
de un contenedor sandbox (Zero Ambient Authority / JIT downscoping);
`ADR-019` §2.7 usa esta misma capa estructural para validar qué
servidores MCP puede declarar un Worker en su Agent Card.

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para explicar primero qué es el Policy
Server y por qué existe como punto de intercepción previo — antes de que
un Vibe Diff (ADR-004) se genere o el Red/Blue/Green Team (ADR-003)
necesite intervenir — antes de entrar al detalle de las dos capas de
restricción.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el flujo de intercepción completo. Se añade Tab. 1 con la
asignación de modelos LLM por variante. Se incorpora el histórico de versiones.

---

## Contexto

El Policy Server es el mecanismo que decide, en el instante mismo en que
un agente solicita usar una herramienta, si esa llamada puede proceder
— antes de que siquiera llegue a generarse un Vibe Diff (ADR-004) o a
que el Red/Blue/Green Team (ADR-003) necesite intervenir. Sin esta capa
de intercepción en el punto de entrada, cualquier control posterior
(aprobación humana, auditoría, equipos de seguridad) actuaría siempre
después del hecho, nunca antes de que la acción ya se haya ejecutado.

Cada herramienta que SIGMA puede ejecutar representa un vector de riesgo
real. Las restricciones necesarias para gobernar ese riesgo son de dos
tipos fundamentalmente distintos: estructurales (reglas deterministas,
verificables sin ambigüedad — ¿este rol puede tocar este recurso en este
entorno?) y semánticas (requieren comprensión real del contexto — ¿esta
llamada, aunque técnicamente permitida, expone datos sensibles o se
desvía de la intención original del usuario?). Una capa única no puede
resolver ambas eficientemente: forzar todo por evaluación semántica
sería prohibitivo en latencia y coste para el 95% de llamadas que son
triviales de resolver por regla, mientras que resolver todo por regla
estructural dejaría pasar violaciones que solo un juicio contextual
puede detectar.
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
  Excepción: submodo Dev puede configurar fail-open en policies.yaml
```

### Tab. 1 — Asignación del modelo LLM juez por variante de costo

El juez semántico es **siempre un modelo diferente al Orquestador** para
evitar el conflicto de interés donde un modelo comprometido juzga sus propias
acciones. **Corregido (Hito 2):** la tabla original mezclaba costo
(Full/Lite) y submodo (Dev/Runtime) en las mismas filas, y nunca cubrió
`SIGMA-ME`/`SIGMA-HE` explícitamente — se corrige a las 4 variantes
reales, consistente con el mapeo ya usado en el resto del proyecto
(Orquestador: `SIGMA-FE`=Ollama/Gemini free, `SIGMA-LE`=Gemini free,
`SIGMA-ME`=Gemini Pro, `SIGMA-HE`=Vertex AI).

| Variante | Modelo del Orquestador | Modelo del juez semántico |
|---|---|---|
| **SIGMA-FE** (opción A) | Gemini API (free tier) | `mistral` local vía Ollama |
| **SIGMA-FE** (opción B) | Ollama local | Gemini API (free tier) |
| **SIGMA-LE** | Gemini API (free tier) | `mistral`/`llama3.2` local vía Ollama |
| **SIGMA-ME** | Gemini Pro | Gemini Flash (menor coste, mismo proveedor evitado como juez único) |
| **SIGMA-HE** | Vertex AI (enterprise) | Gemini Pro o modelo enterprise distinto al del Orquestador |

**Submodo Dev (cualquier variante):** capa semántica desactivada por
completo — solo estructural, sin importar qué modelos use la variante
activa en submodo Runtime. **Submodo Runtime:** misma lógica de la tabla
de arriba, sin cambios adicionales por submodo.

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

### Vínculos nuevos (Hito 2)

**Con ADR-017 (sandboxing):** la capa estructural de este documento no
se limita a llamadas a herramientas en tiempo de ejecución — `ADR-017`
§2.3 la extiende al momento de arranque de un contenedor efímero: el
Policy Server lee el `defaults.yaml` del skill/Worker generado y emite
la credencial de vida ultra-corta (Zero Ambient Authority). Es el mismo
mecanismo, aplicado un momento antes.

**Con ADR-019 (MCP declarativo):** cuando un Worker declara
`mcp_servers` en su Agent Card (`ADR-019` §2.7), es esta misma capa
estructural quien valida esa lista contra lo que el mandato del
Director autorizó — no un mecanismo de validación distinto.

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
  excepción configurable en submodo Dev.
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

**Cambios en v1.5 (Hito 2, cierre de Rollout 1):**
- **a** Tab. 1 corregida al esquema real de 4 variantes de costo
  (`SIGMA-FE/LE/ME/HE`), separado del submodo (Dev/Runtime) — la
  versión anterior nunca cubrió ME/HE explícitamente.
- **b** Añadidos vínculos con ADR-017 (JIT downscoping como extensión
  de esta capa estructural) y ADR-019 (validación de `mcp_servers`
  declarados por Workers).
