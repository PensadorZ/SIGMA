---
id: ADR-004
titulo: Vibe Diff Persistente y Human-in-the-Loop con MFA
version: 1.5
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-004 v1.4
referencias-minimas: ADR-003, ADR-005, ADR-010, ADR-011
aprobado-por: Prof. Marx A. García Delgado
nombre-archivo: adr-004-vibe-diff-mfa.md
---

# ADR-004: Vibe Diff Persistente y Human-in-the-Loop con MFA

## Resumen ejecutivo de cambios v1.5

El mecanismo primario de pausa/reanudación HITL se actualiza al verificado
en el Hito 1: **LangGraph `interrupt()` + checkpointer `SqliteSaver`**, con
`webhook_receiver.py` invocando `resume_pipeline()` por `trace_id`. El
polling a Redis del diseño v1.4 queda documentado como fallback histórico:
la implementación real demostró que el enfoque de polling era
arquitectónicamente inferior al checkpointing nativo de LangGraph. Se
documenta la separación de topics de Zulip (`RUNS`/`HITL`) y el disparador
automático de HITL cuando `pct_unclear > 30%`. Se completa el Apéndice A,
que pasa de comparativa teórica a estado de implementación verificado.

---

## Contexto

Un sistema que puede ejecutar código, modificar bases de datos y desplegar
modelos representa un riesgo real si una acción destructiva se ejecuta sin
supervisión humana. Los riesgos concretos son: un LLM que sobreestima su
confianza y ejecuta una acción irreversible, un prompt malicioso que suplanta
la intención del usuario, y la ausencia de cadena de custodia que imposibilita
la auditoría posterior.

El Hito 1 aportó evidencia de implementación real: el mecanismo de pausa
por polling especificado en v1.4 fue construido, evaluado y reemplazado por
el mecanismo nativo de LangGraph, que resultó más simple, más robusto y sin
consumo de CPU en espera.

---

## Decisión

### Fig. 1 — Flujo canónico de aprobación para acciones de nivel MEDIUM o superior

```
Skill solicita acción
        │
        ▼
Policy Server estructural ──→ [BLOQUEA] ──→ Registro Langfuse → FIN
        │ PERMITE
        ▼
Policy Server semántico ──→ [BLOQUEA] ──→ Registro Langfuse → FIN
        │ PERMITE
        ▼
Orquestador genera Vibe Diff (JSON) → persiste en MinIO (WORM)
        │
        ▼
Nodo node_hitl_wait ejecuta interrupt()          ← MECANISMO v1.5
  └─ LangGraph pausa el grafo
  └─ SqliteSaver persiste el estado completo con el trace_id
  └─ Notificación al operador vía Zulip (topic HITL)
        │
        ▼
Operador responde (Zulip / HTTP POST al webhook)
        │
        ▼
webhook_receiver.py → resume_pipeline(trace_id, decision)
  └─ LangGraph restaura el estado desde el checkpoint
  └─ El grafo continúa exactamente donde se pausó
        │
        ├─ [RECHAZA] → Vibe Diff marcado REJECTED → FIN
        │
        ▼
¿Políticas cambiaron desde la aprobación?
        ├─ [SÍ] → Vibe Diff marcado STALE → volver al inicio
        ▼
Ejecución de la acción
```

### Mecanismo de pausa/reanudación — LangGraph `interrupt()` + SqliteSaver

**Este es el mecanismo primario verificado en el Hito 1** (65/65 tests, HITL
funcional confirmado). Componentes:

- `core/checkpointer.py` — configura el `SqliteSaver` como checkpointer del
  grafo. El estado completo del pipeline se persiste en SQLite en cada paso.
- `node_hitl_wait` en `orchestrator.py` — nodo del grafo que ejecuta
  `interrupt()` cuando una acción requiere aprobación. El proceso puede
  incluso terminar: el estado sobrevive en el checkpoint.
- `webhook_receiver.py` — proceso HTTP ligero que recibe la decisión del
  operador y llama `resume_pipeline(trace_id, decision)` para reanudar el
  grafo pausado desde su checkpoint exacto.

**Por qué reemplaza al polling a Redis (diseño v1.4):** el polling mantenía
al Orquestador vivo consumiendo un hilo, no sobrevivía a reinicios del
proceso, y duplicaba estado que LangGraph ya gestiona nativamente. El
`interrupt()` + checkpointer no consume recursos durante la espera, sobrevive
a reinicios, y usa el mecanismo idiomático del framework. Redis conserva sus
otros roles (colas del Grafo de Suposiciones ADR-001, buffer `chain` ADR-002,
cola de eventos Langfuse ADR-011).

### Notificaciones — Zulip con topics separados

| Topic (variable en `.env`) | Contenido |
|---|---|
| `ZULIP_TOPIC_RUNS` | Eventos de ejecución: inicio, fin, fallos de pipeline |
| `ZULIP_TOPIC_HITL` | Solicitudes de aprobación pendientes de respuesta humana |

La separación evita que las solicitudes de aprobación se pierdan entre el
ruido de los eventos de ejecución. `zulip_notifier.py` opera en modo
silencioso si las variables no están configuradas y degrada a log local sin
interrumpir el pipeline.

### Disparador automático de HITL por calidad

Cuando el skill `0008-sentiment-analyzer` reporta `pct_unclear > 30%` en un
lote, el Orquestador dispara automáticamente una alerta HITL vía Zulip: un
porcentaje tan alto de clasificaciones `UNCLEAR` (ADR-008) indica datos fuera
de la distribución esperada y requiere decisión humana antes de continuar.

### Tab. 1 — Niveles de aprobación

| Nivel | Criterio | Vibe Diff | Aprobación requerida |
|---|---|---|---|
| **LOW** | Reversible, sin impacto en `_prod` | No requerido | Enter en consola |
| **MEDIUM** | Reversible, >1.000 filas o con PII | Requerido | HITL vía `interrupt()` |
| **HIGH** | Irreversible o impacto en `_prod` | Requerido + persistente | HITL + MFA |
| **CRITICAL** | Despliegue o borrado masivo | Requerido + máxima retención | HITL + MFA hardware (recomendado) |

### Tab. 2 — Autenticación del canal de aprobación por variante

| Variante | Autenticación |
|---|---|
| **SIGMA Full** | Token estático `APPROVAL_TOKEN` en `.env` |
| **SIGMA Lite** | TOTP o mecanismo del proveedor cloud |
| **SIGMA Dev** | Sin autenticación, confirmación en consola |
| **SIGMA Runtime** | TOTP con semilla cifrada mediante Fernet (ADR-010) |

El timeout de espera se configura con `APPROVAL_TIMEOUT_SECONDS` (por defecto
`300`). Con el checkpointer, un timeout expirado cancela la acción pero el
estado pausado se conserva para auditoría.

### Vibe Diff STALE

Si el Policy Server detecta que las políticas cambiaron entre la aprobación
y la ejecución: bloquea la ejecución, marca el Vibe Diff como `STALE` en
MinIO, notifica al operador con el motivo, y exige un nuevo ciclo completo.

### Integración con el Green Team

Las acciones de recuperación del Green Team de impacto `MEDIUM` o superior
generan su propio Vibe Diff con el diff exacto del código. Las de impacto
`LOW` se aplican automáticamente sin Vibe Diff.

### Ciclo de vida de un pipeline fallido

Los resultados parciales se conservan en MinIO marcados como `PARTIAL`. Con
el checkpointer `SqliteSaver`, la reanudación desde el último checkpoint es
nativa: `resume_pipeline(trace_id)`. Si no hay acción en siete días, el
pipeline se archiva automáticamente.

---

## Consecuencias positivas

- La cadena de custodia de Vibe Diffs en MinIO permite auditoría completa.
- El mecanismo `interrupt()` + checkpointer no consume recursos durante la
  espera y sobrevive a reinicios del proceso — verificado en el Hito 1.
- Los niveles diferenciados evitan la fatiga de alertas.
- La separación de topics Zulip evita que las aprobaciones se pierdan entre
  eventos de ejecución.

## Consecuencias negativas

- Las acciones HIGH y CRITICAL bloquean el pipeline hasta que el operador
  responde.
- El checkpointer SQLite añade un archivo de estado local que debe excluirse
  del repositorio (`.gitignore`).
- Si `webhook_receiver.py` no está activo, las decisiones del operador no
  llegan al grafo pausado; el sistema notifica `WEBHOOK_RECEIVER_UNAVAILABLE`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Polling a Redis cada 5 s (diseño v1.4) | Consume un hilo permanente; no sobrevive a reinicios; duplica estado que LangGraph gestiona nativamente. Reemplazado tras verificación en el Hito 1 |
| Aprobación solo vía consola | No genera cadena de custodia auditable |
| Umbral de confianza del LLM | Un LLM suplantado puede sobreestimar su confianza |
| Solo notificaciones por email | No garantiza latencia baja |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se declaró el orden canónico: Policy Server → Vibe Diff →
  aprobación → ejecución.
- **b.1.2** Se especificó el comportamiento ante Vibe Diff `STALE`.
- **c.1.2** Se integró el Green Team en el flujo de aprobación.
- **d.1.2** Se especificó el Approval Endpoint como proceso separado con
  polling a Redis.
- **e.1.2** Se añadió la gestión de MFA mediante TOTP con semilla cifrada.
- **f.1.2** Se añadió el ciclo de vida de un pipeline fallido.

**Cambios en v1.3:**
- **a.1.3** Se añadió Fig. 1 con el flujo canónico completo.
- **b.1.3** Se añadió Tab. 1 con los niveles de aprobación.
- **c.1.3** Se añadió Tab. 2 con la autenticación por variante.
- **d.1.3** Se hizo configurable el timeout mediante `APPROVAL_TIMEOUT_SECONDS`.

**Cambios en v1.4:**
- **a.1.4** Se añadió el Apéndice A con la comparativa polling versus
  webhooks.

**Cambios en v1.5:**
- **a** Se actualizó el mecanismo primario de HITL al verificado en el
  Hito 1: LangGraph `interrupt()` + `SqliteSaver`, con `webhook_receiver.py`
  y `resume_pipeline()` por `trace_id`. El polling a Redis pasa a
  Alternativas Consideradas con la justificación del reemplazo.
- **b** Se actualizó Fig. 1 con el flujo real de pausa/reanudación.
- **c** Se documentó la separación de topics Zulip (`ZULIP_TOPIC_RUNS` /
  `ZULIP_TOPIC_HITL`).
- **d** Se añadió el disparador automático de HITL cuando
  `pct_unclear > 30%` en el skill 0008.
- **e** Se completó el Apéndice A con el bloque de configuración íntegro y
  el estado de implementación real de cada mecanismo.

---

## Apéndice A — Mecanismos de notificación y reanudación (estado verificado)

En v1.4 este apéndice comparaba polling a Redis contra webhooks como
alternativas teóricas. Tras el Hito 1, el estado es de implementación
verificada.

### Tab. A.1 — Mecanismos: estado de implementación tras el Hito 1

| Mecanismo | Estado | Rol actual |
|---|---|---|
| **LangGraph `interrupt()` + SqliteSaver** | ✅ Implementado y verificado | Mecanismo primario de pausa/reanudación del grafo |
| **Webhook (`webhook_receiver.py`)** | ✅ Implementado y verificado | Canal de entrada de la decisión del operador; invoca `resume_pipeline(trace_id)` |
| **Zulip (topics RUNS/HITL)** | ✅ Implementado (`zulip_notifier.py`) | Notificación al operador; degrada a log local si no está configurado |
| **Polling a Redis** | ⛔ Reemplazado | Descartado como mecanismo HITL; Redis conserva sus otros roles (ADR-001, ADR-002, ADR-011) |

### Configuración del canal de aprobación

```yaml
# policies.yaml
approval:
  notification_mechanism: webhook       # webhook (default desde v1.5) | zulip_only
  webhook_url: http://localhost:8765/approve-webhook
  webhook_timeout_ms: 2000
  webhook_retries: 3
  zulip_topic_runs: ${ZULIP_TOPIC_RUNS}
  zulip_topic_hitl: ${ZULIP_TOPIC_HITL}
  approval_timeout_seconds: ${APPROVAL_TIMEOUT_SECONDS}   # default: 300
  auto_hitl_unclear_threshold: 0.30     # pct_unclear > 30% dispara HITL
```

### Condiciones de operación

- `webhook_receiver.py` debe estar activo antes de ejecutar pipelines con
  acciones de nivel MEDIUM o superior. El script de arranque de INSTALL.md
  lo inicia junto con la infraestructura Docker. Aunque en el Hito 1 dichas 
  activaciones se hacen manualmente. 
- La autenticación del webhook usa el `APPROVAL_TOKEN` (Full) o TOTP
  (Runtime) según Tab. 2.
- En entornos con firewall o VPN, el webhook opera en localhost sin
  exposición externa: el operador responde vía Zulip y el conector de Zulip
  local reenvía al webhook.
