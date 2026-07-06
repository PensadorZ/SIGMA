# AGENTS_CREATOR.md — Contrato Global de Agentes

**SIGMA v1.5 — Sistema Integrado para la Gestión Multiagente**
Autor: Prof. Marx Agustín García Delgado
Versión: 1.0.0 (primera generación como archivo)
Repositorio: `sigma` (documentación) — este archivo NO vive en `sigma-hito1` (código)

---

## Propósito de este documento

`AGENTS_CREATOR.md` es el acta fundacional que define el contrato que todo
agente del ecosistema SIGMA debe cumplir — humano coordinando IAs, IA
generando código, o IA revisando el trabajo de otra. Es la referencia que
cualquier conversación nueva (Claude, DeepSeek, o cualquier otro asistente)
debe leer primero.

**Nunca se llama `AGENTS.md`** — ese nombre pertenece a una convención de
versiones anteriores del proyecto, ya retirada.

---

## 1. Identidad del proyecto

SIGMA es un ecosistema multiagente para análisis de Big Data, construido
100% sobre stack open-source y gratuito en su variante `Full`. El operador
único del proyecto es Marx Agustín García Delgado — la arquitectura
multi-operador fue evaluada y explícitamente rechazada.

**Variantes reconocidas:**

| Variante | Significado |
|---|---|
| `Full` | 100% self-hosted, sin servicios de pago — variante canónica del Hito 1 |
| `Lite` | Servicios de pago (pendiente créditos Google Cloud) |
| `Dev` | Local, datos sintéticos, sin infraestructura real |
| `Runtime` | Despliegue mixto (futuro, VPS Hetzner) |

`SIGMA_VARIANT` es el nombre de variable de entorno canónico. Nunca
`SIGMA_ENV` — se evaluó y rechazó explícitamente adoptar ese nombre de una
línea de trabajo paralela, porque el costo de propagar el renombrado por
todo el proyecto no se justificaba frente al beneficio cosmético.

---

## 2. Protocolo de trabajo — no negociable

Todo agente que trabaje en SIGMA sigue este orden, sin excepción:

1. **Auditar antes de generar.** Buscar en conversaciones previas y en el
   proyecto si algo similar ya existe, antes de proponer algo nuevo. Nunca
   afirmar que un archivo existe sin haberlo verificado.
2. **Proponer estructura, no código, primero.** Presentar los archivos que
   se van a generar y las decisiones abiertas que requieren confirmación
   del operador, antes de escribir una sola línea.
3. **Texto completo antes de archivo.** El contenido completo se muestra en
   la conversación para revisión antes de crear el archivo físico.
4. **Verificar después de generar.** Correr pruebas, `grep`, conteos —
   cualquier verificación mecánica disponible — antes de dar por cerrada
   una entrega.

Este protocolo existe porque su ausencia ya causó un problema real y
documentado: dos líneas de trabajo distintas ("Eco MultiAgentes 3 Skills 1"
y "Eco MultiAgentes 4 Skills 2") construyeron los mismos 6 skills del
Hito 1 en paralelo, sin que ninguna supiera de la otra, generando trabajo
duplicado que costó una sesión completa de auditoría reconciliar.

---

## 3. Convenciones de nomenclatura de artefactos

**Skill vs. skill.py.** `Skill` (mayúscula, o `SKILL.md`) se refiere
exclusivamente a la especificación — el documento que describe qué hace el
skill. `skill.py`, siempre en minúscula, es el código ejecutable. No se usa
"Skill.py" con mayúscula bajo ninguna circunstancia — la forma de
escribirlo debe ser inequívoca sobre a cuál de los dos se refiere.

**Versionado — nunca se sobrescribe, siempre se preserva.** Todo script,
skill o artefacto conserva su número de versión en el nombre de archivo
cuando corresponde archivarse (ej. `0000_skill_v2.py` en `old_scripts/`).
Nunca se sugiere sobrescribir o renombrar un archivo versionado — cada
versión se conserva para trazabilidad.

**`old_scripts/` es de solo lectura conceptual.** Contiene versiones
históricas reemplazadas en el árbol activo. Ningún archivo ahí se ejecuta
ni se importa desde el pipeline. Marcado explícitamente "NO TOCAR" en su
propio `README.md`.

---

## 4. Protocolo de centralización de artefactos

Antes de entregar cualquier conjunto de archivos, el agente declara
explícitamente el alcance de la entrega, y pregunta si no está claro:

- **Un script puntual** — un solo archivo.
- **Un grupo de scripts** — varios archivos relacionados, delimitados
  explícitamente por el operador.
- **Un Skill completo** — los 7 artefactos canónicos de esa carpeta
  específica (ver ADR-009), entregados juntos, no repartidos en mensajes
  distintos.

Nunca se asume el alcance más conveniente para el agente — se pregunta
cuando no es inequívoco.

---

## 5. Contrato técnico de cada skill

Ver **ADR-009** para el detalle completo. Resumen: 7 archivos canónicos
por skill (`SKILL.md`, `defaults.yaml`, `skill.py`, `references/schemas.md`,
`evals/eval_adherencia.yaml`, `tests/test_{nombre}.feature`,
`tests/test_000X_{nombre}.py`), `skill.py` cargado dinámicamente por ruta
(`skills/_loader.py`) por el problema de identificadores Python inválidos
en carpetas con guion, y ninguna constante hardcodeada que `defaults.yaml`
ya declare como configurable.

Todo output exitoso de un skill incluye `run_id` y `trace_id` de forma
explícita, sin excepción.

---

## 6. Restricción epistémica K ⊆ X (ADR-008)

Ningún skill infiere, imputa o completa información más allá de lo que sus
datos de entrada u observación determinista permiten. La detección de
columnas objetivo, idioma, o cualquier característica estructural es
siempre estructural (¿existe la clave?), nunca semántica (¿qué significa
la clave?).

---

## 7. Límites de seguridad — no negociables, sin excepción

Cualquier línea de trabajo futura de SIGMA relacionada con pentesting,
protocolos anti-hackers, o análisis de vulnerabilidades de sistemas de
terceros, opera exclusivamente bajo estas condiciones: sistemas propios del
operador, sistemas de clientes con contrato firmado, o programas de bug
bounty con autorización explícita (HackerOne, Bugcrowd, Intigriti).
Escanear o acceder a un sistema sin autorización previa del propietario
queda fuera de alcance sin excepción, independientemente de si la
organización es lucrativa o no, de si el fallo encontrado es real, o de si
la intención final es comercialmente beneficiosa para esa organización.

---

## 8. Numeración de hitos — vigente

| Hito | Contenido |
|---|---|
| Hito 1 | Pipeline lineal LangGraph, 6 skills (0000-0003, 0008, 0011) |
| Hito 2 | Arquitectura de 3 orquestadores con subgrafos (patrón supervisor jerárquico), contexto inyectado de solo lectura al arrancar (nunca memoria mutable compartida en vivo) |
| Hito 3 | Streaming en tiempo real (ADR-015), Hamilton Selector entre Kafka/Redis Streams/Faust |
| Hitos futuros (sin numerar) | Análisis financiero de tarjetahabientes (datos anonimizados/pseudonimizados), análisis de video/imagen, línea de seguridad bajo los límites de la sección 7 |

---

## 9. Historial de cambios

| Versión | Fecha | Cambio |
|---|---|---|
| 1.0.0 | Eco MultiAgentes 4 Skills 2, Julio 2026 | Primera generación como archivo real. Anteriormente solo se referenciaba, nunca se había materializado. Consolida decisiones ya tomadas a lo largo de múltiples conversaciones. |
