---
id: ADR-012
titulo: Gestión de Versiones y Promoción de Skills
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-012 v1.3
referencias-minimas: ADR-009, ADR-010, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-012: Gestión de Versiones y Promoción de Skills

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para explicar primero que este ADR es
el proceso operativo que da consecuencia real a la obligatoriedad de
`tests/` en ADR-009, usando las métricas de Langfuse de ADR-011 como
criterio de promoción — antes de entrar al detalle del ciclo
Dev → Staging → Production.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el flujo de promoción entre entornos. Se añade Tab. 1
con el significado SemVer para cada tipo de artefacto versionado. Se incorpora
el histórico de versiones.

---

## Contexto

ADR-012 es el mecanismo que convierte en proceso operativo lo que
ADR-009 exige como obligatorio: la existencia de `tests/` en cada skill
solo tiene sentido real si existe un ciclo formal que decida, con base
en esos tests y en las métricas de Langfuse (ADR-011), si un skill está
listo para avanzar de Dev a Staging y finalmente a Production. Sin este
ADR, la obligatoriedad de `tests/` sería una exigencia sin consecuencia
práctica — se escribirían tests, pero nada dictaría cuándo un skill
puede confiarse a producción ni cómo revertir si algo sale mal.

Los skills evolucionan. Sin un protocolo formal de versionado ocurren
regresiones silenciosas cuando una actualización rompe pipelines en
producción, y el rollback es imposible cuando no hay versión anterior
estructurada.
---

## Decisión

Los skills siguen **Semantic Versioning (SemVer)**:
- **MAJOR:** cambio que rompe compatibilidad de schema.
- **MINOR:** nueva funcionalidad compatible hacia atrás.
- **PATCH:** corrección de bugs sin cambio de comportamiento.

### Fig. 1 — Flujo de promoción de un skill entre entornos

```
Rama feature/skill-{nombre}-v{version}
        │
        ▼
ENTORNO DEV
  ├─ Tests unitarios (pytest)
  ├─ Tests de comportamiento (pytest-bdd, escenarios Gherkin)
  └─ Verificación estática de propiedades LTL
        │ ¿Todos los tests pasan?
        ▼
ENTORNO STAGING
  Datos de prueba reales (ej. Tirendaz 22.5K registros)
  Métricas medidas en Langfuse:
  ├─ d2_functional_score >= 1.0
  └─ d6_trajectory_adherence >= 0.9
        │ ¿Métricas superan umbrales?
        ▼
ENTORNO PRODUCTION
  Aprobación final del operador (Approval Endpoint, ADR-004)
  Verificación de no-regresión en pipelines existentes
        │
        ▼
Versión pinned en producción (ej. sentiment-analyzer:1.2.0)
```

### Tab. 1 — Significado SemVer por tipo de artefacto versionado

| Artefacto | MAJOR | MINOR | PATCH |
|---|---|---|---|
| **Skills** (`SKILL.md` + `skill.py`) | Schema de input u output cambia y rompe consumers | Nueva funcionalidad compatible | Corrección de bug sin impacto de comportamiento |
| **`policies.yaml`** | Se restringe una herramienta actualmente en uso | Solo se añade a la allowlist | Corrección de regex de detección |
| **`allowed_packages.yaml`** | Se elimina un paquete actualmente en uso | Se añade un paquete nuevo | Actualización del hash de paquete existente |
| **Pipelines YAML** | Cambio en versiones pinned que afecta el comportamiento | Adición de pasos opcionales | Corrección tipográfica o de metadatos |

### Extensión del alcance del versionado

`policies.yaml` y `allowed_packages.yaml` también siguen SemVer bajo el mismo
ciclo de promoción que los skills. El ciclo Dev → Staging → Production aplica
a estos artefactos igual que a los skills.

### Versiones pinned en pipelines

Los archivos YAML de pipelines deben referenciar versiones explícitas de los
skills que usan. Un pipeline que referencia un skill sin versión explícita es
inválido y el Orquestador lo rechaza en el momento de carga con error
`UNPINNED_SKILL_VERSION`.

---

## Consecuencias positivas

- El proceso de promoción garantiza que solo skills validados llegan a
  producción.
- Los pipelines con versiones pinned son reproducibles
  independientemente de las versiones disponibles en el sistema.
- La coexistencia de hasta 3 versiones permite comparaciones A/B en staging.

## Consecuencias negativas

- El proceso de promoción añade pasos formales al ciclo de desarrollo.
- Mantener hasta 3 versiones simultáneas aumenta el overhead de gestión en
  equipos pequeños.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Versiones en ramas Git sin SemVer | Dificulta saber qué versión está en producción |
| Despliegue directo sin staging | Sin red de seguridad; las regresiones llegan a producción |
| Versiones numéricas sin SemVer | No comunican el impacto del cambio a los consumers |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se extendió el alcance del versionado SemVer a `policies.yaml`
  y `allowed_packages.yaml` con el mismo ciclo de promoción que los skills.
- **b.1.2** Se añadió que los pipelines deben referenciar versiones pinned
  de los skills bajo pena de rechazo por el Orquestador.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el flujo de promoción entre entornos y los
  datasets de prueba en cada etapa.
- **b** Se añadió Tab. 1 con el significado de cada nivel SemVer para cada
  tipo de artefacto versionado.
