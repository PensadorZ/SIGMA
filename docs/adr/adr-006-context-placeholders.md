---
id: ADR-006
titulo: Higiene del Contexto con Placeholders y ContextResolver
version: 1.3
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-006 v1.2
referencias-minimas: ADR-005, ADR-010, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-006: Higiene del Contexto con Placeholders y ContextResolver

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con la jerarquía de resolución del ContextResolver. Se añade
Tab. 1 con la separación explícita entre tipos de configuración y tipos de
secretos. Se incorpora el histórico de versiones.

---

## Contexto

Los skills contienen prompts, rutas y parámetros que varían entre entornos y
entre ejecuciones. Si estos valores se escriben directamente en el código ocurren
hardcodeo de secretos, acoplamiento de entorno y fallos silenciosos cuando una
variable no está definida.

---

## Decisión

Usar la sintaxis `${VARIABLE}` para todos los valores dependientes de entorno
o ejecución. Un middleware centralizado `context_resolver.py` reemplaza estos
placeholders en tiempo de ejecución antes de que el prompt llegue al LLM.

### Fig. 1 — Jerarquía de resolución del ContextResolver

```
Skill con placeholder ${OUTPUT_TABLE}
        │
        ▼
ContextResolver busca en:
  1. override_state  ← Mayor prioridad (inyectado por el Orquestador en runtime)
        │ ¿Encontrado?
        ├─ SÍ → Sanitización → ¿Pasa? → Sustituir → Registrar fuente en Langfuse
        └─ NO ↓
  2. os.environ  ← Variables del archivo .env cargadas al inicio
        │ ¿Encontrado?
        ├─ SÍ → Sanitización → ¿Pasa? → Sustituir → Registrar fuente en Langfuse
        └─ NO ↓
  3. defaults.yaml  ← Valores por defecto no sensibles del skill
        │ ¿Encontrado?
        ├─ SÍ → Sanitización → ¿Pasa? → Sustituir → Registrar fuente en Langfuse
        └─ NO ↓
  NINGUNA FUENTE → ContextResolutionError (fail-fast con mensaje descriptivo)

Sanitización verifica:
  ✓ Sin path traversal (../ o rutas absolutas fuera del proyecto)
  ✓ Sin patrones de credenciales según ADR-010
  ✓ Tipo compatible con el declarado en defaults.yaml
```

### Tab. 1 — Separación entre configuración y secretos

| Tipo de valor | Mecanismo | ¿Puede aparecer en Langfuse? |
|---|---|---|
| Rutas de archivos | Placeholder `${VAR}` en SKILL.md | Sí (solo el nombre, nunca el contenido) |
| Nombres de tablas | Placeholder `${VAR}` en SKILL.md | Sí |
| URLs de endpoints | Placeholder `${VAR}` en SKILL.md | Sí |
| Claves de API | `get_required_env()` en código Python | **Nunca** |
| Contraseñas de BD | `get_required_env()` en código Python | **Nunca** |
| Tokens de acceso | `get_required_env()` en código Python | **Nunca** |
| Semilla TOTP | Ruta al archivo cifrado como placeholder; valor nunca como placeholder | **Nunca** |

### Registro en Langfuse

El ContextResolver registra el **nombre** del placeholder resuelto y la
**fuente** de resolución (`override_state`, `os.environ` o `defaults.yaml`).
Nunca registra el valor resuelto para no exponer configuración sensible.
El registro va con el `trace_id` activo según ADR-011.

### Validación en CI

El GitHub Action de CI verifica que ningún archivo `SKILL.md` o prompt
contiene placeholders sin resolver ni patrones de credenciales antes del merge.

---

## Consecuencias positivas

- Un skill escrito en Dev funciona en producción sin modificaciones.
- El `fail-fast` elimina fallos silenciosos por variables no definidas.
- La sanitización previene ataques de path traversal y exposición accidental
  de credenciales a través del sistema de resolución.

## Consecuencias negativas

- Los desarrolladores deben recordar usar la sintaxis de placeholder.
- La validación en CI actúa como red de seguridad pero no como sustituto de
  la disciplina en el desarrollo.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Valores hardcodeados por entorno | El mismo skill no puede usarse en múltiples entornos |
| Variables de entorno directas sin resolver | El LLM recibe el placeholder literalmente |
| Jinja2 como motor de templates | `string.Template` de Python es suficiente |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se añadió sanitización de valores resueltos con tres verificaciones:
  path traversal, patrones de credenciales y compatibilidad de tipo.
- **b.1.2** Se añadió registro en Langfuse del nombre y fuente de cada
  placeholder resuelto sin exponer el valor.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con la jerarquía de resolución completa incluyendo
  el `fail-fast`.
- **b** Se añadió Tab. 1 con la separación explícita entre tipos de
  configuración y tipos de secretos.
