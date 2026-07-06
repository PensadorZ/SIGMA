---
id: ADR-009
titulo: Especificación de Skills con Gherkin, LTL y Estructura Granular
version: 1.6
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-07
supersede: ADR-009 v1.5
referencias-minimas: ADR-002, ADR-006, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-009: Especificación de Skills con Gherkin, LTL y Estructura Granular

## Resumen ejecutivo de cambios v1.6

Se añade la justificación de ingeniería de la carpeta `tests/` como decisión
funcional —no meramente estructural—: los skills se prueban y se mejoran
iterativamente, y `tests/` es el soporte de ese ciclo. Se documentan los
**módulos a nivel de raíz de `skills/`** (`__init__.py`, `_loader.py`,
`_common.py`), verificados en la estructura real de `sigma-hito1`, que
permiten invocar cualquier skill como módulo Python desde fuera de su
contexto de ejecución (otros servicios, otros agentes, el Orquestador
mismo). Ningún cambio rompe la compatibilidad con los skills existentes.

---

## Contexto

Un skill debe comunicar qué hace, cuándo puede ejecutarse, qué garantiza y
cómo se traza. Un `SKILL.md` con solo prosa no es suficiente porque es
ambigua y no puede alimentar tests de integración. Además, los skills más
complejos necesitan una organización interna predecible para sus activos,
evaluaciones, scripts auxiliares y referencias. Esta organización debe
distinguirse claramente de las carpetas globales del ecosistema para evitar
confusiones operativas y de mantenimiento.

Dos necesidades adicionales, verificadas en la práctica del Hito 1, no
estaban justificadas formalmente en versiones anteriores de este ADR:

- **Por qué `tests/` es obligatoria y no solo una convención de estilo.**
  Un skill no es un artefacto que se escribe una vez y queda fijo: se
  refina, se corrige y se mejora a lo largo de su vida (ver ADR-012). Sin
  una carpeta de tests que acompañe al skill, cada mejora arriesga romper
  comportamiento ya validado sin que nadie lo note hasta producción.
- **Cómo un skill es invocado por *algo que no es el Orquestador de su
  propio Hito*.** Un dashboard externo, un segundo orquestador (ADR-016),
  o un servicio de terceros pueden necesitar ejecutar la lógica de un skill
  sin pasar por el DAG completo. Sin un mecanismo de importación estándar,
  cada consumidor externo reinventa su propio wrapper.

---

## Decisión

### Fig. 1 — Estructura de archivos de un skill: los siete artefactos canónicos

```
skills/
├── __init__.py                   ← Módulo raíz (ver Fig. 2)
├── _loader.py                    ← Cargador dinámico de skills (ver Fig. 2)
├── _common.py                    ← Utilidades compartidas (ver Fig. 2)
│
└── 0001-data-ingestion/          ← Carpeta del skill (formato 00xx-nombre)
    │
    │  ═══ SIETE ARTEFACTOS OBLIGATORIOS (v1.5) ═══
    ├── SKILL.md                  ← 1. Especificación completa (≤ 500 líneas)
    ├── skill.py                  ← 2. Implementación Python
    ├── defaults.yaml             ← 3. Valores por defecto no sensibles
    ├── tests/
    │   ├── test_skill.feature    ← 4. Escenarios Gherkin
    │   └── test_skill.py         ← 5. Steps ejecutables (pytest-bdd)
    ├── references/
    │   └── schemas.md            ← 6. Contrato Pydantic del output (D2, ADR-007)
    ├── evals/
    │   └── eval_adherencia.yaml  ← 7. Evaluación de adherencia (D6, ADR-013)
    │
    │  ═══ OPCIONALES para skills complejos ═══
    ├── tests/conftest.py         ← Fixtures propias del skill si las necesita
    ├── assets/                   ← Activos del skill
    └── scripts/                  ← Utilidades auxiliares del skill
```

Verificación de la práctica: los 6 skills del Hito 1 (0000, 0001, 0002,
0003, 0008, 0011) cumplen este protocolo con 65/65 tests pasando. El
protocolo no es teórico: está validado contra código ejecutable real,
incluyendo la estructura confirmada de `0000-system-health-check` con sus
ocho entradas (siete artefactos + `__pycache__` generado en runtime, que
no se versiona).

### Justificación de ingeniería de `tests/` (no solo convención)

`tests/` no es una carpeta que exista por prolijidad documental. Es la
respuesta a un problema de ingeniería concreto: **los skills cambian, y
cada cambio puede romper algo que ya funcionaba.**

- Un skill se define una vez en `SKILL.md` pero se **corrige y mejora
  muchas veces** en `skill.py` a lo largo de su ciclo de vida (bugs
  encontrados en producción, nuevos formatos de dato de entrada, ajustes
  de umbral). `tests/test_skill.feature` congela el comportamiento
  esperado; `tests/test_skill.py` lo verifica de forma automática y
  repetible en cada cambio.
- Sin esta carpeta, la única forma de saber si una modificación rompió
  algo sería ejecutar manualmente el pipeline completo contra datos
  reales — lento, costoso, y no reproducible en CI.
- La obligatoriedad de `tests/` es lo que hace posible el ciclo de
  promoción Dev → Staging → Production de ADR-012: sin tests que se
  puedan ejecutar automáticamente, no hay criterio objetivo para decidir
  si un skill está listo para avanzar de entorno.

En síntesis: `tests/` es una **decisión de ingeniería sobre cómo se
sostiene la calidad de un skill en el tiempo**, no una preferencia de
organización de carpetas.

### Fig. 2 — Módulos a nivel de raíz de `skills/`: skills como módulos Python

Además de la estructura interna de cada skill, la carpeta `skills/` tiene
tres archivos propios en su raíz, verificados en la estructura real de
`sigma-hito1`:

```
skills/
├── __init__.py     ← Convierte skills/ en un paquete Python importable
├── _loader.py      ← Descubre y carga skills dinámicamente por su ID (00xx)
├── _common.py      ← Utilidades compartidas entre skills (no específicas
│                      de ningún skill individual)
├── 0000-system-health-check/
├── 0001-data-ingestion/
└── ...
```

**Propósito de cada archivo:**

| Archivo | Rol |
|---|---|
| `__init__.py` | Declara `skills/` como paquete Python. Sin este archivo, ningún consumidor externo puede hacer `import skills` ni `from skills import ...` |
| `_loader.py` | Cargador dinámico: dado un ID de skill (`"0008"`), localiza la carpeta `00xx-nombre/`, importa su `skill.py` y expone su función de entrada sin que el consumidor necesite conocer la ruta física ni el nombre completo de la carpeta |
| `_common.py` | Utilidades genuinamente compartidas entre skills (ej. helpers de logging estructurado, wrappers de `get_required_env()` de ADR-010) que no pertenecen a la lógica de negocio de ningún skill particular |

**Por qué esto es necesario — el problema que resuelve:**

Un skill fue diseñado originalmente para ejecutarse como nodo de un DAG de
LangGraph dentro de *su propio* Hito. Pero en la práctica, otros
consumidores necesitan su lógica sin pasar por ese DAG completo:

- Un segundo orquestador de la jerarquía Director/Engineer (ADR-016) puede
  necesitar invocar un skill de otro Engineer bajo autorización del
  Director, sin instanciar el subgrafo completo de ese Engineer.
- Un dashboard reactivo del Hito 3 (ADR-015) puede necesitar ejecutar la
  lógica de clasificación de `0008-sentiment-analyzer` sobre un mensaje
  aislado, fuera de cualquier pipeline batch.
- Un servicio externo o un script de mantenimiento puede necesitar
  ejecutar `0004-statistical-validator` sobre un dataset ad-hoc sin montar
  el Orquestador completo.

Sin `__init__.py` + `_loader.py`, cada uno de estos consumidores tendría
que reinventar su propia forma de localizar e importar el skill —
duplicando lógica y arriesgando romper la encapsulación que ADR-002 y
ADR-008 exigen. Con este mecanismo, cualquier consumidor autorizado hace:

```python
from skills._loader import load_skill

sentiment = load_skill("0008")
resultado = sentiment.run(texto_aislado, context=override_state)
```

**Reglas de uso de este mecanismo:**

1. `_loader.py` **no** otorga por sí mismo autorización para ejecutar un
   skill fuera de su Hito — la autorización sigue pasando por el Policy
   Server (ADR-005) y, si el nivel de impacto lo exige, por el Vibe Diff
   (ADR-004). El loader es un mecanismo de acceso técnico, no un bypass de
   gobernanza.
2. `_common.py` solo contiene utilidades **sin estado de negocio**. Lógica
   específica de un dominio (sentimiento, drift, etc.) vive dentro del
   skill correspondiente, nunca en `_common.py`.
3. Estos tres archivos son responsabilidad transversal del catálogo de
   skills, no de ningún skill individual: se versionan junto con
   `AGENTS_CREATOR.md`, no con el ciclo SemVer de un skill particular.

### Tab. 1 — Las cuatro secciones obligatorias del SKILL.md

| Sección | Contenido | Propósito |
|---|---|---|
| **Frontmatter YAML** | id, version, description, domain, model, input/output patterns, parallelism, output_schema, expected_trajectory, sigma_variants, referencias ADRs | Procesado automáticamente por el Orquestador |
| **Escenarios Gherkin** | Al menos un caso positivo y uno negativo | Ejecutables con `pytest-bdd`; legibles por stakeholders |
| **Propiedades LTL** | Al menos una propiedad de seguridad y una de vivacidad | Verificadas en diseño, CI y runtime por el Blue Team (ADR-003) |
| **Especificación de trazabilidad** | Eventos exactos que el skill emitirá a Langfuse con payload mínimo | Uniformidad en la observabilidad del ecosistema |

### Tab. 2 — Subcarpetas del skill: obligatorias y opcionales

| Carpeta | Estado | Propósito | Contenido mínimo |
|---|---|---|---|
| `tests/` | **Obligatoria** | Sostener el ciclo de prueba y mejora continua del skill (ver justificación de ingeniería arriba) | `test_skill.feature` + `test_skill.py` |
| `references/` | **Obligatoria** | Contrato de datos | `schemas.md` (Pydantic del output) |
| `evals/` | **Obligatoria** | Evaluación de adherencia | `eval_adherencia.yaml` |
| `assets/` | Opcional | Activos visuales, datos de prueba | `sample_data.parquet`, `custom_theme.yaml` |
| `scripts/` | Opcional | Utilidades auxiliares del skill | `migrate_schema.py`, `pre_clean.sh` |

### Tab. 2b — Catálogo oficial de skills por Hito (0000–0019)

| Rango | Skills | Hito | Estado |
|---|---|---|---|
| 0000–0004, 0008, 0011 | Pipeline batch core + sentiment + viz | Hito 1 | ✅ Implementados (65/65 tests) |
| 0005–0007, 0009–0010, 0012–0015 | ML/DL trainers, HITL, explainability, inspector | Hito 2 | Especificación |
| 0016–0019 | Hamilton Selector streaming + skills RT (ADR-015) | Hito 3 | Reservados |

Los skills 0016–0019 incluyen líneas futuras de analítica bancaria,
análisis de video/imagen y pruebas de seguridad autorizadas, con el límite
no negociable de que el escaneo no autorizado de sistemas de terceros está
fuera del alcance del ecosistema, independientemente de la intención.

### Tab. 3 — Diferenciación entre carpetas globales y locales

| Propósito | Carpeta global (raíz del repositorio) | Carpeta local (dentro de cada skill) |
|---|---|---|
| Evaluaciones transversales de todo SIGMA | `evals_SIGMA/` | `skills/00xx-nombre/evals/` |
| Hooks y scripts transversales | `hooks_SIGMA/` | `skills/00xx-nombre/scripts/` |
| Assets globales compartidos | `assets_SIGMA/` | `skills/00xx-nombre/assets/` |
| Referencias globales | `references_SIGMA/` | `skills/00xx-nombre/references/` |
| **Módulos del catálogo (nuevo v1.6)** | `skills/__init__.py`, `skills/_loader.py`, `skills/_common.py` | *(no aplica — son transversales por definición)* |

Esta convención garantiza que un desarrollador identifique de inmediato si
un recurso pertenece al ecosistema completo o a un skill particular, y evita
colisiones de nombres entre skills que definen sus propias evaluaciones o
scripts.

### Tab. 4 — Convención de nomenclatura y numeración de skills

| Elemento | Formato | Ejemplo |
|---|---|---|
| Carpeta del skill | `00xx-nombre-del-skill` | `0001-data-ingestion`, `0012-code-reviewer` |
| Archivo de especificación | `SKILL.md` | `skills/0001-data-ingestion/SKILL.md` |
| Archivo de implementación | `skill.py` | `skills/0001-data-ingestion/skill.py` |
| Valores por defecto | `defaults.yaml` | `skills/0001-data-ingestion/defaults.yaml` |
| Carpeta de tests | `tests/` | `skills/0001-data-ingestion/tests/` |

La numeración sigue un formato de cuatro dígitos con relleno de ceros,
asignado secuencialmente al incorporarse al catálogo oficial. Es estable
durante toda la vida del skill y **no se reasigna** aunque el skill sea
deprecado.

### Tab. 5 — Marca de autor para skills generados dinámicamente

| Tipo de skill | Formato de versión | Ejemplo |
|---|---|---|
| Diseñado manualmente | SemVer estándar `MAJOR.MINOR.PATCH` | `1.2.0` |
| Generado por IA (Orquestador en modo Arquitecto) | `gia_` + SemVer | `gia_0.1.0` |

El prefijo `gia_` significa **Generado por Inteligencia Artificial**. Los
skills con esta marca han sido producidos por el Orquestador en modo
Arquitecto siguiendo el flujo de generación dinámica definido en ADR-014.
La marca es permanente durante la vida del skill generado. Si un skill
generado por IA es rediseñado por completo por un humano, se considera un
skill nuevo con numeración y versión independientes.

La regla de al menos tres referencias a ADRs anteriores aplica también al
frontmatter del `SKILL.md`.

---

## Consecuencias positivas

- Los escenarios Gherkin son directamente ejecutables como tests de integración.
- Las propiedades LTL hacen explícitas las garantías del skill.
- La estructura granular facilita la organización de skills complejos sin
  forzar a los simples a adoptarla.
- La obligatoriedad justificada de `tests/` sostiene el ciclo de promoción
  de ADR-012 con un criterio objetivo y automatizable.
- Los módulos de raíz (`__init__.py`, `_loader.py`, `_common.py`) permiten
  que cualquier skill se invoque como módulo Python desde fuera de su Hito,
  sin duplicar lógica de importación en cada consumidor externo.
- La diferenciación global vs. local elimina la ambigüedad sobre la
  pertenencia de evaluaciones y scripts.
- La marca `gia_` permite identificar el origen de un skill para auditorías
  de seguridad y revisiones de calidad.
- La numeración secuencial de cuatro dígitos permite referencias inequívocas
  en pipelines y configuraciones.

## Consecuencias negativas

- Escribir un `SKILL.md` completo requiere más tiempo que una implementación
  sin especificación.
- Las propiedades LTL requieren conocimiento de lógica temporal.
- La estructura granular puede generar duplicación de activos si varios skills
  comparten recursos; se mitiga con la carpeta global `assets_SIGMA/`.
- La numeración requiere mantener un registro centralizado para evitar
  colisiones.
- `_loader.py` es un punto único de acceso transversal: un error en su
  lógica de descubrimiento afecta a todos los skills simultáneamente. Se
  mitiga con la cobertura de tests que ADR-012 exige antes de promover
  cualquier cambio a `_loader.py` o `_common.py`.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Solo descripción en prosa | Ambigua; no genera tests automáticamente |
| Solo OpenAPI o JSON Schema | Adecuado para APIs HTTP; no captura propiedades temporales |
| Estructura única obligatoria para todos | Sobrecarga los skills simples sin beneficio |
| Sin módulos de raíz — cada consumidor externo importa el skill a mano | Duplica lógica de localización/importación en cada consumidor; arriesga romper la encapsulación de ADR-002/ADR-008 al exponer rutas internas |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se confirmó la integración del campo `parallelism` con la
  estrategia `chain` de ADR-002.
- **b.1.2** Se añadió la mención explícita a que las propiedades LTL son
  verificadas en tiempo real por el Blue Team de ADR-003.

**Cambios en v1.3:**
- **a.1.3** Se añadió Fig. 1 con la estructura de archivos completa de un skill.
- **b.1.3** Se añadió Tab. 1 con las cuatro secciones obligatorias del `SKILL.md`.

**Cambios en v1.4:**
- **a.1.4** Se actualizó Fig. 1 para reflejar la estructura granular opcional
  con subcarpetas `assets/`, `evals/`, `scripts/` y `references/`.
- **b.1.4** Se añadió Tab. 2 con la descripción de cada subcarpeta opcional.
- **c.1.4** Se añadió Tab. 3 con la diferenciación entre carpetas globales
  con sufijo `_SIGMA` y carpetas locales de cada skill.
- **d.1.4** Se añadió Tab. 4 con la numeración de cuatro dígitos.
- **e.1.4** Se añadió Tab. 5 con la marca `gia_` en coordinación con ADR-014.
- **f.1.4** Se clarificó la compatibilidad hacia atrás de la estructura
  granular.
- **g.1.4** La relación con ADR-014 se encuadró como nota informativa para
  evitar dependencia circular.

**Cambios en v1.5:**
- **a.1.5** El protocolo de empaquetado se elevó a siete artefactos canónicos
  obligatorios: `references/schemas.md` y `evals/eval_adherencia.yaml` pasan
  de opcionales a obligatorios, y `tests/test_skill.py` se exige junto al
  `.feature`. Verificado contra los 6 skills del Hito 1 con 65/65 tests.
- **b.1.5** Se añadió el límite recomendado de 500 líneas por `SKILL.md`.
- **c.1.5** Se añadió Tab. 2b con el catálogo oficial de 20 skills (0000–0019)
  organizados en 3 Hitos, incluyendo el rango reservado 0016–0019 y su
  límite ético no negociable.
- **d.1.5** Fig. 1 se actualizó para distinguir los siete artefactos
  obligatorios de las subcarpetas opcionales restantes.

**Cambios en v1.6:**
- **a** Se añadió la justificación de ingeniería de `tests/` como decisión
  funcional que sostiene el ciclo de prueba y mejora continua del skill, no
  una convención de estilo.
- **b** Se documentaron los módulos a nivel de raíz de `skills/`
  (`__init__.py`, `_loader.py`, `_common.py`), verificados en la estructura
  real de `sigma-hito1`, con Fig. 2 y su propósito, el problema que
  resuelven, y las reglas de uso (sin bypass del Policy Server ni del Vibe
  Diff).
- **c** Se actualizó Fig. 1 para mostrar los módulos de raíz junto a la
  carpeta del skill individual.
- **d** Se añadió fila en Tab. 3 para los módulos del catálogo como recurso
  transversal por definición.
- **e** Se añadió una consecuencia negativa sobre el riesgo de punto único
  de acceso en `_loader.py`, con su mitigación vía ADR-012.
