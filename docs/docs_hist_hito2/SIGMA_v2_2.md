# SIGMA v2.2 — Sistema Integrado para la Gestión Multiagente

> **SIGMA no es una respuesta. Es el sistema que aprende a responder.**

**Reemplaza a `SIGMA_v1.7.md`** (archivado en `docs/Docs_hito1/`, describe
el estado verificado del cierre de Hito 1 — sigue siendo válido como
registro histórico, no como estado actual). Este documento consolida
Rollout 1 de Hito 2, ya cerrado con evidencia real, y proyecta Rollout 2,
Rollout 3, y una prospectiva de Hito 3.

SIGMA es un ecosistema de agentes autónomos para analizar, diseñar,
calcular y decidir en diversas situaciones y niveles de complejidad,
desde el análisis exploratorio de un dataset hasta el diseño completo
de un pipeline de producción. Cada decisión que el sistema toma queda
respaldada por gobernanza explícita — memoria epistémica, contención de
alucinaciones (`K ⊆ X`), memoria operativa entre corridas y
trazabilidad completa — en vez de convención tácita.

---

## Nota de alcance — qué es real hoy, qué es proyección

Este documento distingue tres capas, sin mezclarlas:

1. **Verificado** — Rollout 1 de Hito 2: código real, corridas reales,
   65/65 tests, evidencia directa de base de datos. Sección "Estado del
   ecosistema" y "Rollout 1 — consolidado".
2. **Planeado con diseño aprobado o pre-aprobado** — Rollout 2, Rollout
   3: ADRs ya escritos (algunos pre-aprobados), sin código todavía.
   Sección "Rollout 2" y "Rollout 3".
3. **Prospectiva** — Hito 3: dirección de intención, no diseño cerrado.
   Sección "Hito 3 — prospectiva", redactada en primera persona porque
   así es como corresponde presentar una proyección propia, no un
   hecho verificado.

---

## Estado del ecosistema

### Documentos canónicos

| # | Documento | Versión | Estado |
|---|---|---|---|
| 01 | README.md / README.es.md | — | ✅ Operativo, actualizado a Rollout 1 |
| 02 | AGENTS_CREATOR.md | 1.2.0 | ✅ Operativo — §8/§9 pendientes de actualización menor (ver Changelog) |
| 03 | SIGMA_v2.0.md (este documento) | 2.0 | ✅ Operativo |
| 04 | ESTRUCTURA_PROYECTO.md | 3.2.0 | 🔄 Pendiente de actualizar — todavía referencia `orchestrator.py` |
| 05 | TROUBLESHOOTING.md | 1.1 | ✅ Operativo (Hito 1, cerrado) |
| 06 | TROUBLESHOOTING_HITO2.md | 1.0.0 | ✅ Operativo |
| 07 | INSTALL.md | — | ⬜ Pendiente — condicionado al cierre de Rollout 3 (ver ADR-010 v1.5) |
| 08 | PIPELINES.md | — | ⬜ Pendiente |

### Architecture Decision Records (20 ADRs, uno en camino)

| ADR | Título | Versión | Estado |
|---|---|---|---|
| ADR-001 | Memoria Epistémica — Feature Store + Grafo de Suposiciones | 1.6 | ✅ Aceptado |
| ADR-002 | Paralelismo Masivo Intra-Skill mediante MapReduce | 1.5 | ✅ Aceptado |
| ADR-003 | Seguridad Automática Red/Blue/Green | 1.7 | ✅ Aceptado |
| ADR-004 | Vibe Diff Persistente y HITL con MFA | 1.6 | ✅ Aceptado |
| ADR-005 | Policy Server Híbrido | 1.5 | ✅ Aceptado |
| ADR-006 | Higiene del Contexto (Placeholders) | 1.5 | ✅ Aceptado |
| ADR-007 | Evaluación Multidimensional (7D) | 1.4 | ✅ Aceptado |
| ADR-008 | Contención Epistémica K ⊆ X | 1.4 | ✅ Aceptado |
| ADR-009 | Especificación de Skills | 1.8 | ✅ Aceptado |
| ADR-010 | Gestión de Secretos (12-Factor) | 1.5 | ✅ Aceptado |
| ADR-011 | Trazabilidad Langfuse V2 | 1.6 | ✅ Aceptado |
| ADR-012 | Versionado y Promoción de Skills | 1.5 | ✅ Aceptado |
| ADR-013 | Auditoría de Trayectoria | 1.5 | ✅ Aceptado |
| ADR-014 | Generación Dinámica de Skills | 1.2 | 🔶 Pre-aprobado |
| ADR-015 | Hamilton Selector (Streaming, Hito 3) | 1.3 | 🔶 Pre-aprobado |
| ADR-016 | Orquestación Jerárquica (Director/Engineer/Auditor) | 1.3 | 🔶 Candidato a aprobación firme — 4 condiciones de Rollout 1 ya verificadas |
| ADR-017 | Sandboxing de Ejecución | 1.3 | 🔶 Pre-aprobado |
| ADR-018 | Memoria Operativa entre Corridas (Ag-DR) | 1.1 | 🔶 Pre-aprobado |
| ADR-019 | Identidad de Agentes (CLOE, jerarquía unificada) | 1.6 | 🔶 Pre-aprobado |
| ADR-020 | Mensajería avanzada (número reservado, sin redactar) | — | ⬜ No escrito — se activa si `chain` (ADR-002) supera la capacidad de Redis/Kafka |

### Catálogo de skills

| Rango | Skills | Hito / Rollout | Estado |
|---|---|---|---|
| 0000–0003, 0008, 0011 | Pipeline batch core + sentiment + viz | Hito 1 | ✅ 55/55 tests en el cierre original |
| 0004 | `statistical-validator` (Engineer Datos) | Hito 2, Rollout 1 | ✅ Implementado — suite conjunta 65/65 |
| 0005–0007, 0009–0010 | `framework-selector`, `ml-trainer`, `dl-trainer`, `cluster-analyzer`, `engagement-calculator` (Engineer Modelos) | Hito 2, Rollout 2 | ⬜ Especificación — sin código todavía |
| 0012–0015 | `code-reviewer`, `skill-discovery`, `stride-modeling`, `pipeline-inspector` (Engineer Auditor) | Hito 2, Rollout 3 | ⬜ Especificación — gateado por ADR-017 real |
| 0016–0019 | Hamilton Selector + consumidores Faust | Hito 3 | ⬜ Reservados (ADR-015) |

---

## Filosofía de diseño

**Agente = Modelo + Arnés.** Un modelo por sí solo no es un agente: es
un ecosistema que se convierte en algo integrado cuando un arnés le da
estado, ejecución de herramientas, ciclos de retroalimentación y
restricciones exigibles. SIGMA es ese arnés.

**Multiagente por diseño, ahora con jerarquía real, no plana.**
Rollout 1 verificó en código lo que hasta hace poco era solo diseño:
Director coordina Engineers especializados (Datos, con Modelos y
Auditor en camino), cada uno con su propio circuit breaker, su propio
HITL, su propia identidad formal (`ADR-019`). La colaboración ya no es
solo "interfaces explícitas y contratos Gherkin + LTL" — es jerarquía
verificable con condiciones de salida objetivas por Rollout.

**Seguridad y gobernanza integradas — con un cuarto pilar nuevo.**
Al Policy Server, Red/Blue/Green y STRIDE modeling se suma el
**sandboxing de ejecución** (`ADR-017`): código generado dinámicamente
y Workers efímeros corren contenidos desde el primer segundo, no solo
después de que algo falla. Auditoría cruzada confirmó que este diseño
coincide con el Pillar 6 del curso Google-Kaggle — no es una idea
aislada, es la arquitectura base que la industria ya reconoce para
esto.

**Memoria en dos planos, no uno.** La Memoria Epistémica (`ADR-001`)
sigue rigiendo qué puede afirmarse *dentro* de una corrida. A eso se
suma, con Rollout 1, la **Memoria Operativa entre corridas** (Ag-DR,
`ADR-018`): SIGMA ya no empieza cada ejecución en blanco por completo.
**Precisión importante, no contradicción:** la regla de "contexto de
solo lectura al arrancar" sigue siendo el comportamiento por defecto
*dentro* de una corrida — el Ag-DR es la excepción explícita,
documentada, y con aprobación humana obligatoria antes de que
cualquier Ag-DR pueda influir una decisión futura. Memoria sí, pero
nunca memoria que un LLM escribe libremente ni que actúa sin que un
humano la haya revisado primero.

**Interoperabilidad formalizada, no solo evaluada.** Donde Hito 1
documentaba honestamente "MCP/A2A/A2UI no implementados", `ADR-019`
§2.6-2.8 ya formaliza un A2A mínimo activo (Worker/Blue Team → Director
sin depender de Langfuse genérico), un esquema declarativo de MCP
(transporte real diferido a cuando haga falta), y A2UI con
`0011-viz-reporter` como candidato registrado. Sigue sin ser
implementación completa — pero ya no es "no implementado" a secas.

**Evaluación continua en 7 dimensiones**, sin cambios de fondo respecto
a Hito 1 — sigue siendo el marco que decide si un resultado
técnicamente correcto es también un resultado bueno.

**Interoperabilidad por reducción de complejidad**, sin cambios — la
razón por la que MCP y A2A se adoptan como estándares en vez de
integraciones ad-hoc sigue siendo la misma: O(N×M) reducido a O(N+M).

---

## Interoperabilidad — más allá del binario implementado/no implementado

`AGENTS_CREATOR.md` §9 (Hito 1) documentaba MCP/A2A/A2UI
como "No implementado" en bloque. Con `ADR-019` §2.6-2.8 ya no es
preciso — cada estándar tiene capas en estados distintos. Para
expresar eso sin forzar un binario, esta sección usa el **Álgebra
Axiométrica** de Marx García (*Axiometry: First Foundational Article*,
proyecto en desarrollo — ver Proyecto OSF, referencia al final del documento),
**comparada contra** los cuatro valores de la lógica de Belnap (1977)
— dos marcos distintos que trabajan en distintos planos de comprensión[^axiometria].

### Los 4 estados del Álgebra Axiométrica (Tabla 1, sección D.6 del Ensayo)

Cada estado se define sobre dos planos independientes: **E** (Existencia
ontológica) y **M** (Manifestación fenoménica) — no sobre una escala
de "cuánta información hay", que es el eje de Belnap.

| Valor | Estado (E, M) | Interpretación onto-axiométrica |
|---|---|---|
| **1** | (1, 1) | Inmanencia Plena — existe y se manifiesta |
| **0** | (0, 0) | Nada Absoluta — no existe y no se manifiesta |
| **`̸0`** | (1, 0) | Potencialidad Pura — existe, pero no se manifiesta |
| **`̸1`** | (0, 1) | Supra-inmanencia / Simulacro — **no existe, pero se manifiesta** |

**Corrección real, verificada contra la tabla original:** `̸1`
(Supra-inmanencia) hice lectura errónea de una sección
distinta del ensayo (D.9, la extensión epistémica). La definición
formal (D.6, Tabla 1) es más precisa y más simple: algo que **se
manifiesta sin existir realmente** — un simulacro. El ejemplo del
propio ensayo: *"el campo cuántico está localizado"* — se manifiesta
(`M=1`) pero no existe de esa forma (`E=0`).

**Comparación formal con Belnap:** el ensayo (D.6.1)
es explícito en que esto es una *"similitud estructural y una profunda
diferencia ontológica"* — Belnap describe qué información tiene un
sistema (plano epistémico); el Álgebra Axiométrica explica por qué esa
información adopta ese estado y qué tipo de realidad señala (plano
ontológico). Son marcos comparables, que se complementan entre sí.

### Tabla de interoperabilidad de SIGMA

| Estándar | Componente | Valor Belnap (epistémico) | Valor SupraBooleano (ontológico) | Estado real |
|---|---|---|---|---|
| **MCP** | Transporte real (host-cliente-servidor) | N | `̸0` — existe como diseño, no se manifiesta en código | Diseñado (`ADR-019` §2.7), sin código — pendiente, sin fecha |
| **MCP** | Esquema declarativo (`mcp_servers` en Agent Card) | T | `1` — existe y se manifiesta | Implementado, validado por Policy Server |
| **A2A** | Contrato de mensaje (`send_a2a_message`) | T | `1` — existe y se manifiesta | Implementado, activo desde ahora (`ADR-019` §2.6) |
| **A2A** | Transporte de red (HTTP/SSE expuesto) | N | `̸0` — existe como diseño, no se manifiesta en código | Diseñado, diferido a cuando haga falta |
| **A2UI** | Candidato (`0011-viz-reporter`) | B | `̸1` — el nombre "candidato A2UI" se manifiesta en la documentación, pero el protocolo A2UI real todavía no existe detrás de ese nombre | Sin diseño completo, solo señalado |
| **AP2/UCP** | Comercio autónomo | F | `0` — no existe ni se manifiesta | Fuera de alcance, explícitamente descartado |

[^axiometria]: Marx A. García Delgado, *Axiometry: First Foundational
Article*. Proyecto completo en OSF:
https://osf.io/yp7ng/overview — el artículo específico en
https://osf.io/yp7ng/files/wtpc9. **Nota de acceso:** OSF no es una
plataforma de indexación constante — el enlace puede no resolver en
el momento de la lectura. La versión narrativa sin desarrollo
matemático (misma teoría, sin álgebra formal) tiene aprobación
independiente en OSF Theses Common, lo cual es un dato relevante para
cualquiera que evalúe la legitimidad académica del marco antes de
llegar al artículo técnico completo.



Cerrado con las 4 condiciones de `ADR-016` Tab. 2 confirmadas en la
práctica, no solo en diseño:

- **65/65 tests** pasando en conjunto (`0000-0004, 0008, 0011`).
- **4+ corridas reales consecutivas** sin fallo, con evidencia de log.
- **Circuit breaker probado con fallo forzado** (`SourceNotFoundError`
  en `0001`) — fallo rápido confirmado, cero reintentos.
- **Traza Langfuse verificada de extremo a extremo** — no solo HTTP
  201, confirmado con consulta directa a la tabla `traces` de
  PostgreSQL tras corregir un bug real (`client.trace()` faltante
  antes de `client.event()`, documentado en `ADR-011` v1.6).

Código real que existe hoy: `director_main.py`, `sigma/core/director.py`,
`sigma/core/engineer_datos.py`, `sigma/core/skill_runner.py`, más los 7
skills de Engineer Datos. `orchestrator.py` (Hito 1) queda archivado
como `scripts/old_scripts_sigma/orchestrator_hito1_v1.0.py`.

Migración de esquema de variantes completada a nivel de código —
`Full/Lite/Dev/Runtime` ya no existe en ningún archivo activo; el
esquema real (`SIGMA-FE/LE/ME/HE` + submodo `Dev/Runtime`) es el único
vigente.

---

## Rollout 2 — Engineer Modelos (siguiente)

**Objetivo:** construir `0005-framework-selector`, `0006-ml-trainer`,
`0007-dl-trainer`, `0009-cluster-analyzer`, `0010-engagement-calculator`
desde cero, con los 7 artefactos canónicos cada uno.

**Condiciones de salida** (mismo criterio que Rollout 1, `ADR-016`
Tab. 2): suite aislada de Engineer Modelos en verde antes de conectarse
al Director; contrato de entrada Engineer Datos → Engineer Modelos
probado explícitamente; al menos una corrida real con ambos Engineers
coordinados; verificación en vivo de que un fallo en Engineer Modelos
no derriba a Engineer Datos.

**Pendiente que cruza desde Rollout 1:**
- Resolver el alcance de "Worker que se convierte en Orquestador"
  (resuelto en `ADR-019` v1.5: es el rol Capataz, no promoción directa
  a Engineer — confirmado por Marx).
- Medir el valor numérico real de los umbrales de arranque de
  `ADR-019` §2.9, con Workers reales por primera vez.
- Evaluar si hace falta una versión "compilada" de ADRs/Identidad para
  mitigar el costo de tokenización (Día 5, Google-Kaggle) antes de que
  el volumen de documentación siga creciendo con 5 skills nuevos.
- Reconciliar `ADR-002` con cualquier documento adicional que todavía
  use "worker" sin el renombrado a "nodo de cómputo".

---

## Rollout 3 — Engineer Auditor (cierra Hito 2)

**Objetivo:** construir `0012-code-reviewer`, `0013-skill-discovery`,
`0014-stride-modeling`, `0015-pipeline-inspector`.

**Condición de entrada, no negociable:** `ADR-017` (sandboxing) debe
estar **implementado y probado con un Worker real**, no solo
pre-aprobado en diseño — es la puerta de entrada explícita que
`ADR-016` Tab. 2 exige, porque la auditoría es el punto con mayor
probabilidad de disparar generación dinámica de skills (`ADR-014`).

**Lo que se cierra aquí, no antes:**
- El veredicto de overfitting (curvas train/val ya generadas por
  `0006`/`0007` en Rollout 2, el veredicto final es de Engineer
  Auditor — decisión ya tomada, pendiente de construir).
- La herramienta de defensa de Engineer Auditor (`ADR-019`
  §2.1bis.2, cuarentena inmediata sobre agentes reportados como
  extraños) — diseñada, sin código todavía.
- `INSTALL.md` — solo tiene sentido escribirlo una vez que la pila de
  servicios deje de cambiar entre Rollouts (`ADR-010` v1.5).

---

## Hito 3 — prospectiva

*Esta sección es una proyección hacia dónde va a llegar SIGMA una vez
que el Hito 2 cierre, con los requisitos exigidos para esta
construcción.*

El Hito 3 resuelve algo que me preocupa desde antes de que existiera
este documento: que SIGMA no se quede atado al texto y al sentimiento.
`0004-statistical-validator` ya demostró que el núcleo estadístico es
completamente numérico — Bayes Factor, ADF+Granger, KS-test, nada de
eso depende de que el dato de entrada sea una opinión escrita. Lo que
todavía no he resuelto es la escala real de Big Data: hoy todo el
pipeline vive en `pandas.DataFrame`, y eso no sobrevive un dataset de
BigQuery de cientos de millones de filas. Antes de tocar streaming en
serio, quiero un ADR — probablemente el `021` o el que corresponda
cuando llegue el momento — que defina cómo SIGMA lee de una fuente sin
traer todo a memoria local: la dirección concreta que ya tengo en mente
es delegar el cómputo pesado al propio motor de la fuente (consultas
SQL directas a BigQuery, no `pandas.read_csv`), extendiendo el mismo
patrón de conector abstracto que `0001-data-ingestion` ya usa para
`required_column` — un backend nuevo detrás de la misma interfaz, no un
skill nuevo desde cero.

El streaming en sí ya tiene su ADR (`ADR-015`, Hamilton Selector) —
Kafka + Faust, matriz de priorización, todo sigue en pie. Lo que sí
quiero dejar anotado es que, si el volumen de eventos supera lo que
Redis/Kafka pueden sostener, ahí está reservado `ADR-020` — sin
proponer antes de tiempo. El disparador que tengo en mente, para que no
quede solo en la intención, es medible: cuando el caudal de eventos por
segundo supere lo que un solo broker Kafka sostiene con la
configuración que `ADR-015` ya define, ahí es cuando `ADR-020` deja de
ser un número reservado y se convierte en un documento real. Ya
aprendí, con la propia colisión de numeración que tuvo `ADR-002`, que
reservar un número sin construirlo genera más problemas de los que
resuelve.

La parte que más me interesa desarrollar, y que sé que todavía es
prematura, es hasta dónde puede crecer un Worker. Ya definimos que un
Worker con `trust_level = 3` puede convertirse en Capataz — eso ya es
real, está en `ADR-019`. Lo que quiero explorar en Hito 3, sin
comprometerme todavía a un diseño, es si tiene sentido que un Capataz
con suficiente historial pueda agregarse a algo más — no necesariamente
un Engineer nuevo (eso reabriría la jerarquía fija de `ADR-016`, y no
tengo claro todavía si eso es lo que realmente necesita SIGMA), sino
quizás un nivel intermedio que no existe hoy. El terreno de prueba más
obvio para esa pregunta, si decido explorarla, son Red Team y Green
Team: ya son procesos acotados a una tarea, ya se crean y se
desincorporan como un Worker, y ya supervisan resultados de otros
componentes como lo haría un Capataz — sin ser ninguna de las dos
cosas del todo hoy. Lo dejo como pregunta abierta a propósito, no como
decisión.

También quiero llevar más lejos la extensión matemática de K⊆X que
dejé anotada al cerrar Rollout 1 — sustituir la restricción binaria por
una función de distancia real, con interpolación permitida dentro del
rango observado y extrapolación exigiendo intervalo de confianza
explícito. El punto de partida técnico más razonable que veo hoy es el
`_run_permutation_bootstrap` que ya construimos dentro de `0004` — ya
calcula intervalos de confianza empíricos, así que la función de
distancia no empezaría de cero, empezaría extendiendo algo que ya
funciona. Sigo pensando que el punto donde eso deja de ser "SIGMA
siendo flexible" y pasa a ser alucinación con intervalo decorativo
necesita un umbral numérico concreto, no solo la intención que tengo
hoy — ese es, probablemente, el trabajo técnico más difícil de todo
Hito 3.

El costo de tokenización, que empecé a mitigar con los umbrales de
arranque de `ADR-019` §2.9, madure en Hito 3 hasta tener números
reales — no una promesa de "se medirá cuando haya Workers reales", sino
datos concretos de cuánto cuesta, en tokens, que el Director entre en
modo investigación con la documentación completa cargada. La métrica ya
existe, solo no se ha apuntado a esta pregunta todavía: D4 de la
Evaluación Multidimensional (`ADR-007`) ya mide tokens y tiempo por
sesión en Langfuse — Hito 3 es cuestión de leer ese dato con esta
pregunta específica en mente, no de construir un mecanismo de medición
nuevo.

Nada de esto está prometido con fecha. Es, literalmente, una carta de
intención para el Hito 3, las prioridades no cambian antes de llegar
ahí.

---

## Stack técnico — sin cambios de fondo respecto a Hito 1

Python 3.12, LangGraph (MIT, autoalojable), PostgreSQL, Redis, MinIO,
Langfuse V2 (autoalojado, `langfuse<3` fijado), Docker. RoBERTa vía
Hugging Face para sentimiento; `scipy`/`statsmodels` para el núcleo
estadístico, sin intervención de ningún LLM. pytest + pytest-bdd para
la disciplina de testing. FastAPI para el Approval Endpoint. Zulip para
notificaciones.

**Nuevo en Hito 2, verificado:** Docker con límites de recursos como
mecanismo de sandboxing (`ADR-017`) — gVisor queda como endurecimiento
opcional para `SIGMA-ME/HE`, nunca requisito.

---

## Registro de cambios (Changelog)

### Cambios en v2.2

- **a** Corregida la columna "Valores Axiométricos Extendidos" a
  "Valores SupraBooleanos". Añadida la Tabla 1 de la sección D.6 del
  Ensayo (los 4 estados formales `{0, 1, ̸0, ̸1}` sobre los planos E/M),
  con nota al pie referenciando el Proyecto OSF completo para su
  desarrollo matemático real.
- **b** Corregida la definición de `̸1` (Supra-inmanencia): no es "se
  manifiesta por canales inconsistentes" (confusión con la extensión
  epistémica de D.9) — es, según la Tabla 1 formal, "no existe pero se
  manifiesta" (simulacro).
- **c** Corregido el planteamiento del vínculo con Belnap: Añadida la
  tabla de interoperabilidad con el Álgebra Axiométrica de Marx García
  (Ver Proyecto OSF) comparada contra los cuatro valores de Belnap
  (1977) — no "sobre" la lógica de Belnap, como decía la versión
  anterior. Son marcos comparables, no el mismo marco renombrado.

### Cambios en v2.1

- **a** Añadida la tabla de interoperabilidad con el Álgebra Axiométrica
  de Marx García sobre la lógica de cuatro valores de Belnap (1977) —
  reemplaza el binario "implementado/no implementado" de
  `AGENTS_CREATOR.md` §9. Verdadero/Falso conservan `1`/`0`; los
  estados suprabooleanos `̸0` (Potencialidad Pura) y `̸1`
  (Supra-inmanencia) dan lectura ontológica a los estados N y B de
  Belnap.
- **b** Sección "Hito 3 — prospectiva" reescrita sobre la versión de
  Marx (más natural, menos forzada), con datos concretos inferidos y
  añadidos donde la intención quedaba sin anclaje técnico: motor SQL
  de BigQuery vía el mismo patrón de conector de `0001`, disparador
  medible para `ADR-020` (caudal > capacidad de un broker Kafka bajo
  `ADR-015`), Red/Green Team como terreno de prueba del nivel
  intermedio Worker↔Capataz, `_run_permutation_bootstrap` de `0004`
  como punto de partida de la función de distancia de K⊆X, y D4 de
  `ADR-007` como la métrica ya existente para medir el costo real de
  tokenización.

### Cambios en v2.0

- **a** Documento reemplaza a `SIGMA_v1.7.md` (archivado en
  `docs/Docs_hito1/`). Refleja el cierre real de Rollout 1, no una
  proyección.
- **b** Tabla de ADRs actualizada a las 19 versiones reales
  post-auditoría de Hito 2, con `ADR-017`, `018`, `019` incorporados
  por primera vez, y `ADR-020` (mensajería avanzada) registrado como
  número reservado, sin redactar.
- **c** Catálogo de skills reorganizado por Rollout real de `ADR-016`,
  no por bloque plano "Hito 2".
- **d** Filosofía de diseño actualizada: cuarto pilar de seguridad
  (sandboxing), memoria en dos planos (epistémica + operativa entre
  corridas), interoperabilidad parcialmente formalizada.
- **e** Añadida la sección "Hito 3 — prospectiva", en primera persona,
  distinguida explícitamente de diseño ya aprobado.
- **f** Se retira toda referencia a `orchestrator.py` como componente
  activo — reemplazado por `director_main.py` + jerarquía Director/
  Engineers en toda mención de arquitectura.
- **g** Terminología "worker" reconciliada a "nodo de cómputo" en todo
  el documento, consistente con `ADR-002`/`ADR-003`; "Worker" (con
  mayúscula) se reserva exclusivamente para el concepto de `ADR-019`.


---

## Pendiente de decisión — no resuelto en esta versión

1. **`AGENTS_CREATOR.md` §8** — la descripción de Hito 2 todavía dice
   "nunca memoria mutable compartida en vivo" sin la matización del
   Ag-DR que este documento ya incorpora. Pendiente de que apruebes el
   texto de reemplazo antes de tocar ese archivo.
2. **`AGENTS_CREATOR.md` §9** — la tabla de interoperabilidad sigue en
   binario "No implementado" para MCP/A2A/A2UI; necesita el estado
   intermedio que `ADR-019` ya formalizó.
3. **`ESTRUCTURA_PROYECTO.md`** — todavía no se ha actualizado el árbol
   de carpetas ni el orden de operaciones; sigue pendiente como tarea
   separada.

---

## Licencia

[MIT](LICENSE)

---

> **SIGMA** no es un producto cerrado: es un marco de trabajo vivo.
> Si entiendes este documento, entiendes el punto de entrada del
> ecosistema tal como está hoy — no como estaba hace tres sesiones.
