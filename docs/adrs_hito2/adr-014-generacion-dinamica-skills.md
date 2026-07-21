---
id: ADR-014
titulo: Generación Dinámica de Nuevos Skills bajo Demanda
version: 1.2
estado: Propuesto
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-014 v1.1
referencias-minimas: ADR-003, ADR-004, ADR-009, ADR-012, ADR-016, ADR-017
aprobado-por: Pendiente de aprobación por Prof. Marx A. García Delgado
---

# ADR-014: Generación Dinámica de Nuevos Skills bajo Demanda

## Resumen ejecutivo de cambios v1.2

**Reconciliación con la jerarquía real (ADR-016).** La v1.1 hablaba de
un "Orquestador (modo Arquitecto)" genérico como autor — terminología de
antes de que existiera la jerarquía Director/Engineer/Auditor. Se
reasignan los roles: **Engineer Auditor detecta** la necesidad (vía
`0013-skill-discovery`), **Director autoriza** (único punto de contacto
con HITL global, ADR-016 Tab. 1), **Engineer del dominio correspondiente
construye** — nunca un "Orquestador" abstracto. Se añade vínculo con
ADR-017 (sandboxing): todo skill generado dinámicamente ejecuta dentro
de un contenedor efímero hasta su promoción a producción.

## Resumen ejecutivo de cambios v1.1

Se amplía la sección de Contexto para explicar primero que este ADR es
el escenario de mayor riesgo del ecosistema — el único donde el sistema
escribe su propio código — y que no introduce mecanismos nuevos, sino
que orquesta juntos los de ADR-003, ADR-004, ADR-005, ADR-009 y ADR-012
en su punto de mayor exigencia.

## Resumen ejecutivo

Este ADR define el proceso mediante el cual el ecosistema SIGMA puede generar
nuevos skills de forma autónoma cuando el catálogo existente no cubre una
necesidad funcional detectada. **Engineer Auditor detecta la carencia**
(vía `0013-skill-discovery`); **el Director autoriza** la generación;
**el Engineer del dominio correspondiente** (Datos, Modelos, o el propio
Auditor si la carencia es de auditoría) **genera el nuevo skill**.
El nuevo skill pasa por el ciclo de validación estándar de Policy
Server, Green Team, Approval Endpoint, sandboxing (ADR-017) y
versionado según ADR-012. Este ADR es aplicable en todas las variantes
de costo, con el submodo Dev desactivado (ver Tab. 2).

---

## Contexto

La Generación Dinámica de Skills es el escenario de mayor riesgo
gobernado por todo el ecosistema: es el único punto donde el propio
sistema escribe código nuevo que después se ejecutará con autoridad
real. Por eso este ADR no introduce mecanismos nuevos — orquesta, en su
punto de mayor exigencia, todos los que ya existen: la especificación de
ADR-009, la validación del Policy Server (ADR-005), las pruebas del
Green Team (ADR-003), la aprobación de ADR-004, el sandboxing de
ADR-017, y el versionado de ADR-012. Si alguno de esos mecanismos
tuviera una falla, este es el lugar donde esa falla tendría el mayor
impacto posible.

El catálogo de skills de SIGMA es inicialmente finito. En un ecosistema
que opera en dominios tan diversos como ciencia de datos, ingeniería,
física, matemática o filosofía, surgirán inevitablemente necesidades
funcionales no cubiertas. Sin un mecanismo formal, el sistema queda
limitado a su catálogo inicial, perdiendo su carácter de ecosistema
autónomo y adaptable.

**Por qué la reasignación de roles de v1.2 no es cosmética:** con un
"Orquestador" genérico como autor, no queda claro *qué Engineer* asume
la responsabilidad del código nuevo una vez promocionado — un skill de
Data Science generado por un actor abstracto no tiene dueño claro
dentro de ADR-016. Asignar la autoría al Engineer del dominio
correspondiente resuelve eso: el skill generado se integra al Engineer
que ya lo va a operar, con la misma responsabilidad que sus skills
manuales.

---

## Decisión

### Fig. 1 — Flujo de generación dinámica de un nuevo skill

```
PASO 1 — Detección de la necesidad
─────────────────────────────────────
Fuentes de detección:
  A. Consulta de usuario que ningún skill puede resolver
     └─ El Director la recibe (intérprete de intención, ADR-016 Fig. 1)
        y la registra en Langfuse como fallo de cobertura
  B. Patrón de fallo recurrente detectado en Langfuse
     └─ Engineer Auditor, vía 0013-skill-discovery, lo detecta
        sistemáticamente — no requiere que el Director lo note primero
  C. Solicitud explícita del operador vía Approval Endpoint
     └─ Llega directo al Director
        │
        ▼
Director consolida el mandato de creación y asigna el Engineer de
dominio correspondiente:
  {descripción funcional, restricciones de dominio,
   nivel de impacto estimado, ADRs que rigen el nuevo skill,
   Engineer asignado (Datos | Modelos | Auditor)}

PASO 2 — Generación por el Engineer de dominio asignado
─────────────────────────────────────
El Engineer asignado genera, dentro de un contenedor efímero
(ADR-017 — nunca fuera de sandbox, sin excepción):
  ├─ SKILL.md completo (formato ADR-009)
  │    ├─ Frontmatter YAML (versión: gia_0.1.0)
  │    ├─ Escenarios Gherkin (≥1 positivo, ≥1 negativo)
  │    ├─ Propiedades LTL (≥1 safety, ≥1 liveness)
  │    └─ Especificación de trazabilidad
  └─ skill.py (implementación inicial)
Almacenamiento temporal: skills/generated/{skill_id}/

PASO 3 — Revisión por Engineer Auditor
─────────────────────────────────────
Engineer Auditor (vía 0012-code-reviewer) verifica:
  ├─ Coherencia de expected_trajectory con skills existentes
  ├─ Corrección formal de propiedades LTL
  └─ OutputSchema no viola K⊆X (ADR-008)

PASO 4 — Validación por el Policy Server (ADR-005)
─────────────────────────────────────
  ├─ Capa estructural: herramientas autorizadas, dependencias permitidas
  └─ Capa semántica: PII, credenciales, desviación de intención

PASO 5 — Pruebas por el Green Team (ADR-003), dentro del sandbox
─────────────────────────────────────
  ├─ Ejecuta el skill en el contenedor efímero de ADR-017
  ├─ Verifica escenarios Gherkin
  ├─ Verifica propiedades LTL en runtime
  └─ Análisis estático con skill code-reviewer

PASO 6 — Aprobación (ADR-004)
─────────────────────────────────────
  ├─ Impacto LOW  → Vibe Diff generado pero sin aprobación requerida
  └─ Impacto MEDIUM/HIGH → Vibe Diff + aprobación del operador (Director
     escala a HITL global — único punto de contacto, ADR-016 Tab. 1)

PASO 7 — Versionado y promoción (ADR-012)
─────────────────────────────────────
  Versión inicial: gia_0.1.0
  Ciclo: Dev → Staging → Production
  (mismos criterios que cualquier skill)
  El skill sale del sandbox de ADR-017 solo al llegar a Production,
  con historial de Green Team en verde
```

### Tab. 1 — Roles y responsabilidades en la generación dinámica

| Agente | Rol | Responsabilidad |
|---|---|---|
| **Director** | Autorizador | Consolida el mandato, decide si autoriza (HITL global si el impacto lo requiere), asigna el Engineer de dominio |
| **Engineer de dominio asignado** (Datos / Modelos / Auditor) | Autor | Detecta vía fuente A (si es el Director quien lo nota) o recibe el mandato, redacta `SKILL.md` y `skill.py` dentro del sandbox |
| **Engineer Auditor** (`0013-skill-discovery`) | Detector sistemático | Detecta patrones de fallo recurrente en Langfuse (fuente B) |
| **Engineer Auditor** (`0012-code-reviewer`) | Revisor | Verifica coherencia de trayectoria, LTL y K⊆X del skill generado |
| **Policy Server** | Validador estructural/semántico | Valida herramientas y dependencias en el skill generado |
| **Green Team** | Validador funcional | Ejecuta pruebas Gherkin/LTL dentro del sandbox de ADR-017, revisa código con `code-reviewer`, gestiona Vibe Diff |
| **Blue Team** | Registrador | Actualiza el AgBOM cuando el skill se promociona a producción |

**Nota:** Engineer Auditor aparece dos veces con responsabilidades
distintas (detección sistemática vía `0013`, revisión vía `0012`) — son
skills diferentes dentro del mismo Engineer, no un conflicto de roles.

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
- La separación de roles entre el Engineer autor y Engineer Auditor como
  revisor sigue el principio de separación de intereses de ADR-003 — y
  ahora además asigna un dueño claro (el Engineer de dominio) al skill
  una vez promocionado.
- La marca `gia_` en la versión (ADR-009) identifica permanentemente el
  origen del skill para auditorías de seguridad.
- El sandboxing obligatorio (ADR-017) contiene el escenario de mayor
  riesgo del ecosistema desde el primer segundo de ejecución.

## Consecuencias negativas

- El proceso añade overhead computacional y de tiempo antes de que un nuevo
  skill esté disponible en producción.
- La calidad del skill generado depende de la capacidad del Engineer
  asignado para interpretar el mandato correctamente.
- El directorio `skills/generated/` requiere políticas de limpieza para
  skills obsoletos no promocionados.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Generación manual por un desarrollador | Introduce latencia y dependencia de recursos humanos |
| Generación por el Auditor | Mezcla responsabilidades de gobernanza con generación de código, violando ADR-003 |
| Un "Orquestador" genérico como autor único (v1.1) | Sin dueño claro tras la promoción — no encaja con la jerarquía real de ADR-016 |
| Validación solo por el Policy Server | No verifica funcionalidad ni calidad del código |
| Sin repositorio de investigación | Impide trazabilidad, versionado y rollback |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-003 | Green Team ejecuta sus pruebas dentro del sandbox de ADR-017 |
| ADR-016 | Fuente de la reasignación de roles v1.2 — Director/Engineer/Auditor reales, no un Orquestador abstracto |
| ADR-017 | Todo skill generado ejecuta en sandbox desde su primera línea hasta su promoción a producción |

---

## Histórico de versiones

Este es el primer registro de este ADR (v1.0, sin cambios documentados
antes de v1.1).

**Cambios en v1.1:** ver resumen ejecutivo de cambios v1.1 arriba.

**Cambios en v1.2 (Hito 2, cierre de Rollout 1):**
- **a** Reasignación completa de roles: "Orquestador (modo Arquitecto)"
  → Director (autoriza) + Engineer de dominio asignado (autor). Agente
  Auditor genérico → Engineer Auditor, con dos responsabilidades
  distintas y explícitas (`0013` detecta, `0012` revisa).
- **b** Vínculo nuevo con ADR-017: todo skill generado ejecuta dentro
  de un contenedor efímero, sin excepción, hasta su promoción a
  producción.
- **c** Fig. 1 y Tab. 1 actualizadas para reflejar ambos cambios.
