---
id: ADR-014
titulo: Generación Dinámica de Nuevos Skills bajo Demanda
version: 1.0
estado: Propuesto
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: Ninguno
referencias-minimas: ADR-003, ADR-004, ADR-009, ADR-012
aprobado-por: Pendiente de aprobación por Prof. Marx A. García Delgado
---

# ADR-014: Generación Dinámica de Nuevos Skills bajo Demanda

## Resumen ejecutivo

Este ADR define el proceso mediante el cual el ecosistema SIGMA puede generar
nuevos skills de forma autónoma cuando el catálogo existente no cubre una
necesidad funcional detectada. El Orquestador en modo **Arquitecto** detecta
la carencia y genera el nuevo skill. El Agente Auditor actúa como **revisor**
(no como autor). El nuevo skill pasa por el ciclo de validación estándar de
Policy Server, Green Team, Approval Endpoint y versionado según ADR-012. Este
ADR es aplicable en todas las variantes excepto SIGMA Dev.

---

## Contexto

El catálogo de skills de SIGMA es inicialmente finito. En un ecosistema que
opera en dominios tan diversos como ciencia de datos, ingeniería, física,
matemática o filosofía, surgirán inevitablemente necesidades funcionales no
cubiertas. Sin un mecanismo formal, el sistema queda limitado a su catálogo
inicial, perdiendo su carácter de ecosistema autónomo y adaptable.

---

## Decisión

### Fig. 1 — Flujo de generación dinámica de un nuevo skill

```
PASO 1 — Detección de la necesidad
─────────────────────────────────────
Fuentes de detección:
  A. Consulta de usuario que ningún skill puede resolver
     └─ Orquestador registra el fallo en Langfuse
  B. Patrón de fallo recurrente detectado en Langfuse
  C. Solicitud explícita del operador vía Approval Endpoint
        │
        ▼
Orquestador genera mandato de creación:
  {descripción funcional, restricciones de dominio,
   nivel de impacto estimado, ADRs que rigen el nuevo skill}

PASO 2 — Generación por el Orquestador (modo Arquitecto)
─────────────────────────────────────
Orquestador genera:
  ├─ SKILL.md completo (formato ADR-009)
  │    ├─ Frontmatter YAML (versión: gia_0.1.0)
  │    ├─ Escenarios Gherkin (≥1 positivo, ≥1 negativo)
  │    ├─ Propiedades LTL (≥1 safety, ≥1 liveness)
  │    └─ Especificación de trazabilidad
  └─ skill.py (implementación inicial)
Almacenamiento temporal: skills/generated/{skill_id}/

PASO 3 — Revisión por el Agente Auditor
─────────────────────────────────────
El Auditor verifica:
  ├─ Coherencia de expected_trajectory con skills existentes
  ├─ Corrección formal de propiedades LTL
  └─ OutputSchema no viola K⊆X (ADR-008)

PASO 4 — Validación por el Policy Server (ADR-005)
─────────────────────────────────────
  ├─ Capa estructural: herramientas autorizadas, dependencias permitidas
  └─ Capa semántica: PII, credenciales, desviación de intención

PASO 5 — Pruebas por el Green Team (ADR-003)
─────────────────────────────────────
  ├─ Ejecuta el skill en entorno aislado
  ├─ Verifica escenarios Gherkin
  ├─ Verifica propiedades LTL en runtime
  └─ Análisis estático con skill code-reviewer

PASO 6 — Aprobación (ADR-004)
─────────────────────────────────────
  ├─ Impacto LOW  → Vibe Diff generado pero sin aprobación requerida
  └─ Impacto MEDIUM/HIGH → Vibe Diff + aprobación del operador

PASO 7 — Versionado y promoción (ADR-012)
─────────────────────────────────────
  Versión inicial: gia_0.1.0
  Ciclo: Dev → Staging → Production
  (mismos criterios que cualquier skill)
```

### Tab. 1 — Roles y responsabilidades en la generación dinámica

| Agente | Rol | Responsabilidad |
|---|---|---|
| **Orquestador (modo Arquitecto)** | Autor | Detecta la necesidad, genera el mandato, redacta `SKILL.md` y `skill.py`, supervisa el ciclo |
| **Agente Auditor** | Revisor | Verifica coherencia de trayectoria, LTL y K⊆X |
| **Policy Server** | Validador estructural/semántico | Valida herramientas y dependencias en el skill generado |
| **Green Team** | Validador funcional | Ejecuta pruebas Gherkin/LTL, revisa código con `code-reviewer`, gestiona Vibe Diff |
| **Blue Team** | Registrador | Actualiza el AgBOM cuando el skill se promociona a producción |

### Tab. 2 — Comportamiento por variante de costo

| Variante | Estado | Nivel de aprobación |
|---|---|---|
| **SIGMA-FE** | Activo | Impacto LOW sin aprobación humana; MEDIUM/HIGH con aprobación |
| **SIGMA-LE** | Activo | Mismos niveles que FE |
| **SIGMA-ME** | Activo | Mismos niveles que FE |
| **SIGMA-HE** | Activo | Mismos niveles que FE |

**Submodos transversales** (aplican a cualquiera de las cuatro variantes de costo):

| Submodo | Estado | Nivel de aprobación |
|---|---|---|
| **Dev** | **Desactivado** | No aplica; evita proliferación de skills no validados en depuración |
| **Runtime** | Activo | **Cualquier generación** requiere aprobación del operador, independientemente del nivel |

---

## Consecuencias positivas

- El sistema puede adaptarse a nuevas necesidades sin intervención humana
  para casos de bajo impacto.
- El ciclo de validación garantiza que los skills generados cumplen los mismos
  estándares que los diseñados manualmente.
- La separación de roles entre el Orquestador como autor y el Auditor como
  revisor sigue el principio de separación de intereses de ADR-003.
- La marca `gia_` en la versión (ADR-009) identifica permanentemente el
  origen del skill para auditorías de seguridad.

## Consecuencias negativas

- El proceso añade overhead computacional y de tiempo antes de que un nuevo
  skill esté disponible en producción.
- La calidad del skill generado depende de la capacidad del Orquestador en
  modo Arquitecto para interpretar el mandato correctamente.
- El directorio `skills/generated/` requiere políticas de limpieza para
  skills obsoletos no promocionados.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Generación manual por un desarrollador | Introduce latencia y dependencia de recursos humanos |
| Generación por el Auditor | Mezcla responsabilidades de gobernanza con generación de código, violando ADR-003 |
| Validación solo por el Policy Server | No verifica funcionalidad ni calidad del código |
| Sin repositorio de investigación | Impide trazabilidad, versionado y rollback |

---

## Histórico de versiones

Este es el primer registro de este ADR. No hay versiones anteriores.
