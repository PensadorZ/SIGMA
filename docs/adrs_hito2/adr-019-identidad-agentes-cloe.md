---
id: ADR-019
title: Formato de Identidad por Agente Orquestador (basado en CLOE System)
version: 1.6
status: Aceptado
original-date: 2026-07
revision-date: 2026-07
supersedes: ninguno
minimum-references: ADR-008, ADR-009, ADR-014, ADR-016, ADR-017, ADR-018
milestone-of-application: Hito 2, cierre de Rollout 1
approved-by: Prof. Marx A. García Delgado
file-name: adr-019-identidad-agentes-cloe.md
---

# ADR-019: Formato de Identidad por Agente Orquestador (basado en CLOE System)

## Resumen ejecutivo de cambios v1.6

Corrección de longitud, a petición de Marx: el documento había crecido
a 704 líneas — sin violar ninguna regla formal (el límite de 500 líneas
de ADR-009 §Fig.1 aplica a `SKILL.md`, nunca se estableció para ADRs),
pero sí contradiciendo en la práctica el propio principio de costo de
tokenización que la sección 2.9 de este documento identifica. Se mueve
el boceto de clases Python (§2.1bis.3, 56 líneas) a
`PROMPT_CONTINUIDAD_ROLLOUT2.md` — es diseño de implementación para
Rollout 2/3, sin código real que lo necesite todavía; no pertenecía a
un ADR ya en fase de aprobación.

## Resumen ejecutivo de cambios v1.5

Rediseño mayor a petición de Marx: `hierarchy_level` y `trust_level` se
unifican en una sola escala 1-5 (antes eran números sin relación —
Director en 0, Engineer en 1, sin conexión con la escala 1-3 de
Workers). Se añade el rol **Capataz** (`Foreman`, se activa exactamente
en `trust_level=3`, supervisa Workers `<3`). Se formalizan reglas de
visibilidad organizacional (K⊆X aplicado a auto-conocimiento, no solo a
datos) que habilitan un mecanismo de seguridad real: un Worker puede
reportar un agente extraño no reconocido entre sus pares, y Engineer
Auditor recibe autoridad de cuarentena inmediata como acto reflejo de
defensa. Se añade un boceto (no implementación) de clases Python con
herencia/polimorfismo para Rollout 2/3. Se añade la sección 2.9 —
umbrales de arranque y "modo investigación" del Director, mitigación
concreta al costo de tokenización señalado en la sesión anterior
(Día 5), con disparadores atados a mecanismos ya existentes (Blue/Green
Team, evaluación 7D).

## Resumen ejecutivo de cambios v1.3

Se cierra una debilidad real señalada por Marx: no había ninguna
mención a A2A, MCP ni A2UI, pese a que los Workers son precisamente
"seres efímeros" que necesitan comunicarse entre sí y con herramientas.
Se añaden 3 secciones nuevas (2.6-2.8), verificadas contra la
documentación real de Anthropic sobre MCP/A2A y contra el Día 2 del
curso Google-Kaggle: A2A formal mínimo para que Blue Team (y cualquier
Worker) reporte al Director sin depender de Langfuse genérico; MCP con
esquema declarativo ahora y transporte real diferido a cuando haga
falta de verdad; A2UI con `0011-viz-reporter` registrado como candidato,
sin diseño completo todavía.

## Resumen ejecutivo

Este ADR formaliza, para cada orquestador de SIGMA (Director, Engineer
Datos, Engineer Modelos, Engineer Auditor), un documento de **Identidad**
propio — adaptando la anatomía ya probada en `Cloe_System_V2_Manual.docx`
(otro proyecto de Marx): Encabezado YAML / Identidad / Protocolos /
Restricciones / Referencias. Complementa, sin reemplazar,
`AGENTS_CREATOR.md` (contrato general de todos los agentes) y ADR-016
(jerarquía y responsabilidades). Cierra el hueco de "Agents.md" (menú de
agentes con rol y límites propios) identificado al comparar SIGMA contra
el carrusel de LinkedIn Agents/Context/Skills/Memory.md.

---

## Contexto

`AGENTS_CREATOR.md` es deliberadamente general — el contrato que
**todo** agente de SIGMA debe cumplir (protocolo de trabajo, convención
de nombres, límites de seguridad). No describe qué es específicamente
el Director, ni qué NO debe hacer específicamente Engineer Datos más
allá de lo que ADR-016 Tab. 1 ya resume en una tabla. Falta un nivel de
profundidad por agente individual que ni `AGENTS_CREATOR.md` ni ADR-016
cubren con intención de hacerlo.

Marx ya resolvió este mismo problema en otro proyecto (CLOE), con un
formato de 5 secciones ya validado en la práctica para definir
"Sombreros" (personas de agente). Este ADR adapta ese formato a SIGMA,
en vez de diseñar uno nuevo desde cero — mismo criterio ya aplicado
antes (preferir reusar algo propio y probado sobre inventar una
estructura nueva sin pedigrí verificable, como se rechazó el Agent Card
JSON del Asistente Secundario).

**Por qué es un ADR separado de ADR-018, no una sección dentro de él:**
Ag-DR (ADR-018) y la Identidad (este ADR) tienen ciclos de vida
opuestos. Un Ag-DR lo genera la máquina automáticamente, una vez por
corrida, y se acumula sin límite natural. Una Identidad la redacta un
humano una sola vez, y rara vez cambia — es casi estática. Mezclarlos
en el mismo documento rompería el patrón que los 18 ADRs anteriores ya
respetan: cada uno cubre una decisión cohesiva, no dos conceptos con
dueños y frecuencias de cambio distintos.

---

## Decisión

### 2.1 — Las 5 secciones, adaptadas de CLOE a SIGMA

| Sección CLOE original | Adaptación a SIGMA |
|---|---|
| Encabezado YAML | Metadata del agente: `agent_id`, `name`, `version`, `hierarchy_level` (Director / Engineer / Worker), `status`, `trust_level` |
| Identidad | Quién es este agente, cuál es su propósito único dentro de la jerarquía — no repite lo que ya dice ADR-016 Tab. 1, lo desarrolla en prosa |
| Protocolos | Paso a paso de cómo actúa este agente específico ante cada situación real (no genérico — referencia funciones/nodos reales de su código, ej. `edge_after_engineer_datos` para el Director) |
| Restricciones | Lo que este agente específico NO debe hacer bajo ninguna circunstancia — más granular que ADR-016 Tab. 1, con ejemplos concretos del código real |
| Referencias | Qué otros documentos debe consultar este agente — ADRs relevantes, otros agentes con los que interactúa, skills que administra |

**Corrección de idioma (a petición explícita de Marx):** todos los
campos del encabezado YAML (metadata estructurada, parseable por
código) se nombran en **inglés** — `agent_id`, `name`, `version`,
`trust_level`, etc. — porque SIGMA es un proyecto internacional. La
prosa de las secciones Identidad/Protocolos/Restricciones/Referencias
permanece en español, consistente con el resto del proyecto
(`AGENTS_CREATOR.md` §5: español para conversación y documentación,
inglés para código).

### 2.1bis — Escala jerárquica unificada (1 a 5) y `trust_level`

**Corrección de fondo, a petición de Marx:** `hierarchy_level` y
`trust_level` dejan de ser dos números sin relación — para un Worker,
**su `hierarchy_level` ES su `trust_level`** (1, 2 o 3). Para Engineer y
Director, `hierarchy_level` es una designación estructural fija (4 y 5),
no algo que se gane con historial — son capacidades ya permanentes,
revisadas por humano, no en periodo de prueba. `Superior` y `Supreme` se
escriben igual en español e inglés (a petición explícita de Marx, sin
traducir esas dos palabras).

**El `trust_level` de un Worker no se asigna a mano en un archivo — se
gana como track record verificable**, igual que propuse para los Ag-DR
(ADR-018 §2.5). Un número puesto a mano en YAML sería exactamente el
tipo de afirmación no verificable que K⊆X (ADR-008) prohíbe para
cualquier otro componente de SIGMA.

**Tab. — Escala jerárquica unificada**

| Nivel | Nombre (ES = EN) | Quién | Cómo se alcanza |
|---|---|---|---|
| 1 | Provisional | Worker nuevo | Valor por defecto de todo Worker nuevo — todos sus Ag-DR requieren revisión humana obligatoria antes de `aprobado` (ADR-018 §2.5), sin excepción |
| 2 | Reviewed | Worker con historial corto | 5 Ag-DR consecutivos `aprobado`, sin ninguno `rechazado` entre medio — habilita contenedor latente (ADR-017 §2.2) |
| 3 | Trusted | Worker con historial largo | 20 Ag-DR consecutivos `aprobado`, cero discrepancias contra Langfuse — candidato a promoción vía ADR-014 (ADR-019 §2.1quater) |
| 3 + rol **Capataz** (`Foreman`) | Trusted, con supervisión | Worker en nivel 3 al que el Director asigna supervisión de otros Workers | Rol adicional, no un nivel numérico nuevo — se activa exactamente en `trust_level = 3`, nunca antes |
| 4 | **Superior** | Engineer (Datos / Modelos / Auditor) | Estructural, fijo — no se gana, se asigna al construir el Engineer (ADR-016) |
| 5 | **Supreme** | Director | Estructural, fijo — único, no hay más de un nivel 5 |

**Regla de caída, no negociable:** un solo Ag-DR marcado `rechazado`
reduce el nivel de un Worker a `1` de inmediato, sin importar el nivel
previo — mismo principio de fallo rápido que ya rige el circuit breaker
(`skill_runner.py`). La confianza se gana lento y se pierde de golpe,
deliberadamente. Si el Worker tenía el rol Capataz, lo pierde en el
mismo instante — un Capataz nunca opera con `trust_level < 3`.

### 2.1bis.2 — Visibilidad del organigrama: quién conoce qué

Principio general: K⊆X aplicado a auto-conocimiento organizacional, no
solo a datos — un agente solo conoce la porción de la jerarquía que
necesita para operar, nunca el organigrama completo por defecto.

| Nivel | Qué conoce |
|---|---|
| Worker (1-3) | Su jefe directo (Capataz si tiene uno asignado, si no, el Director); el jefe supremo (Director) siempre; **cuántos Workers de su mismo tipo existen activos ahora mismo** (visibilidad horizontal, no vertical) |
| Capataz (3 + rol) | Todo lo anterior, más los Workers `trust_level < 3` que supervisa directamente — nunca Workers de otro Capataz |
| Engineer (4, Superior) | Arquitectura completa |
| Director (5, Supreme) | Arquitectura completa |

**Mecanismo de seguridad real que esto habilita (a petición explícita
de Marx):** un Worker que detecta un peer de su mismo tipo que no
reconoce — más Workers activos de los que su jefe directo le confirmó,
o un `agent_id` que no aparece en el AgBOM de referencia (`ADR-003`) —
lo reporta como **agente extraño al Pipeline** vía A2A (§2.6) a su jefe
directo, quien escala de inmediato al Director. Esto no es un mecanismo
nuevo aislado — es la visibilidad horizontal de la tabla de arriba,
usada como sensor de anomalías: sin saber cuántos pares existen, un
Worker no podría notar que hay uno de más.

**Herramienta de defensa de Engineer Auditor (a petición explícita de
Marx):** Auditor tiene autoridad de **cuarentena inmediata** sobre
cualquier agente reportado como extraño — activa el mecanismo de
cuarentena de Green Team (`ADR-003`) sin esperar autorización previa
del Director para ese acto reflejo de contención. Reporta al Director
inmediatamente después, no antes — es una diferencia deliberada frente
a cómo se maneja cualquier otra decisión (donde el Director autoriza
antes de actuar): contener un ataque real no puede esperar la misma
secuencia que autorizar la creación de un skill nuevo. Después de
contener, el resto del ciclo (snapshot, `code-reviewer`, Vibe Diff si el
impacto es MEDIUM/HIGH) sigue exactamente como ya define `ADR-003`.

### 2.1bis.3 — Boceto de implementación en clases Python (movido)

**Movido a `PROMPT_CONTINUIDAD_ROLLOUT2.md` (Hito 2, corrección de
longitud):** el boceto completo de clases Python (herencia,
polimorfismo) para `Agent`/`Worker`/`Capataz`/`Engineer`/`Director`
vive ahora ahí, no aquí — es diseño de implementación para Rollout
2/3, sin código real que lo necesite todavía; mantenerlo dentro de
este ADR ya aprobado violaba el propio principio de costo de
tokenización que la sección 2.9 de este mismo documento identifica.

### 2.1ter — Workers: subagentes efímeros para tareas específicas

**Distinción de dos planos, no dos nombres en competencia (aclarada por
Marx):** "Worker" es la definición **jerárquico-operacional** — el
nombre que este concepto tiene dentro del código y la jerarquía de
SIGMA, consistente con ADR-002/ADR-003. "Agente Efímero" es su
definición **epistémica** — qué es este concepto en el fondo, más allá
de su nombre operativo. Si preguntas qué es un Worker, la respuesta es:
un Agente Efímero. Ambos planos coexisten sin conflicto; no hay
renombrado de ninguno de los dos términos.

**Concepto nuevo, no confundir con los 4 orquestadores permanentes**
(Director, Engineer Datos/Modelos/Auditor). Un **Worker** es un
subagente de vida corta que el Director crea para una tarea acotada y
específica — no es un Engineer, no es parte de la jerarquía permanente
de ADR-016, y se **desincorpora** (termina) al concluir su tarea.

**Política del Director al crear un Worker** (hueco real que faltaba en
la v1.0 de este ADR): el Director **debe** generar el Agent Card del
Worker en el momento de crearlo, no después — el Agent Card es el acta
de nacimiento del Worker, análoga a por qué un Ag-DR nunca se redacta
con narrativa libre (ADR-018 §2.1): documentar la decisión en el
momento en que ocurre, no reconstruirla de memoria después.

**Vínculo obligatorio con ADR-018:** al desincorporarse el Worker (fin
de su vida útil), su Agent Card completo **se embebe dentro del Ag-DR**
del agente que lo creó (el Director, u ocasionalmente un Engineer) —
es la única forma de auditar después *cómo y por qué* el Director
concibió ese Worker específico. Un Worker sin Ag-DR que lo documente no
debería poder haberse creado — la trazabilidad no es opcional.

**Formato del Agent Card de un Worker** — Yammtler, no JSON (a
diferencia del ejemplo que trajo Marx, que sí usaba JSON — se toma el
contenido, no el formato, por consistencia con ADR-018/ADR-009):

```yaml
agent_id: worker-calculador-financiero-a1b2c3
name: Calculador Financiero
version: 1.0.0
hierarchy_level: 1-3 (Worker — ver Tab. escala unificada §2.1bis)
status: decommissioned   # active | decommissioned
trust_level: 1           # siempre 1 al nacer — un Worker nuevo no tiene historial
created_by: director
created_at: 2026-07-17T08:12:00Z
decommissioned_at: 2026-07-17T08:14:32Z
description: >
  Calcula CAGR, Sharpe Ratio y ROI. Creado para una tarea puntual del
  usuario, sin skill existente que la cubriera.
skills:
  - id: calcular-cagr
    input_schema: {periodos: "array[number]"}
    output_schema: {cagr: number}
permissions: ["read:database"]
requires_confirmation: false
```

### 2.1quater — Latencia, persistencia del resultado, y la vía real de promoción

Tres correcciones importantes, a petición de Marx — la primera es un
hueco que yo mismo señalé sin cerrarlo; las otras dos son decisiones de
diseño reales que hay que precisar antes de aceptarlas tal cual.

**a) El contenedor no se destruye hasta que el Director confirme la
escritura del resultado.** Esto ya estaba señalado como hueco abierto y
queda cerrado aquí: la secuencia correcta es *Worker escribe resultado
→ Director lo confirma (vía su propio Ag-DR, ADR-018) → solo entonces
se destruye el contenedor*. Nunca al revés. Esta regla vive formalmente
en `ADR-017` §2.2 (se actualiza en la misma sesión).

**b) `trust_level ≥ 2` mantiene el contenedor "tibio" (latente), en vez
de destruirlo — esto sí reduce la latencia real que señalé.** Un Worker
de un tipo ya usado varias veces con éxito (ej. "Calculador Financiero")
no necesita volver a pagar el costo de arranque de contenedor en cada
invocación — se mantiene disponible, contenido igual que siempre
(mismos límites de red/memoria/filesystem de ADR-017), simplemente sin
destruirse entre tareas del mismo tipo.

**Corrección importante — `trust_level ≥ 2/3` NO saca al Worker del
sandbox por sí solo.** Aquí sí necesito precisar antes de aceptar la
propuesta tal cual: `trust_level` mide **consistencia de comportamiento**
(sus Ag-DR pasados fueron aprobados sin discrepancia) — no mide
**seguridad del código** en el sentido que ADR-017 contiene (fuga de
memoria, escape de contenedor, dependencia comprometida). Son preguntas
distintas. Sacar a un Worker del sandbox completamente confundiría
"se ha comportado bien" con "su código es seguro sin contención" — el
mismo tipo de conflación que K⊆X (ADR-008) ya prohíbe en otros
contextos: no inferir una propiedad a partir de una señal que no la mide
directamente.

**c) La vía real de "Worker que crece" — resuelto: no es promoción a
Engineer, es el rol Capataz.** Aclarado por Marx: un Worker no se
convierte en Engineer directamente — al alcanzar `trust_level = 3`, el
Director puede asignarle el rol **Capataz** (`Foreman`), que supervisa
a Workers con `trust_level < 3` (ver Tab. unificada, §2.1bis). Por
separado, un `trust_level = 3` también lo vuelve **candidato** a que el
Director inicie promoción de su *capacidad* (no del Worker mismo) a
skill permanente dentro de un Engineer existente, vía el ciclo completo
que `ADR-014` ya define (Green Team → Policy Server → Approval →
versionado `gia_` → Producción). Ambos caminos son independientes:
Capataz es un rol operativo inmediato; la promoción a skill permanente
es un proceso de revisión humana completo, no automático por alcanzar
el nivel.

### 2.2 — Formato de archivo: mismo "Yammtler" (YAML + Markdown) que Ag-DR y `SKILL.md`

Consistencia deliberada con ADR-018 y ADR-009 — un humano (o el propio
Director) que ya sabe leer un `SKILL.md` o un Ag-DR no tiene que
aprender un formato nuevo para leer una Identidad.

```
sigma/
└── identities/
    ├── director.identity.md
    ├── engineer_datos.identity.md
    ├── engineer_modelos.identity.md   ← placeholder hasta Rollout 2
    └── engineer_auditor.identity.md   ← placeholder hasta Rollout 3
```

### 2.3 — Regla de no invención (mismo principio que ya rige todo Rollout 1)

**Solo Director y Engineer Datos tienen Identidad completa en esta
versión** — son los únicos con código real. Engineer Modelos y Engineer
Auditor reciben un placeholder de una línea ("Pendiente — se redacta
cuando el Engineer exista, Rollout 2/3 respectivamente") en vez de una
Identidad inventada sobre componentes que todavía no existen. Mismo
principio ya aplicado en ADR-016 §2.4 ("el Director nunca conoce
Engineers que aún no existen") — aquí se extiende a la documentación de
Identidad, no solo al código de enrutamiento.

### 2.4 — Ejemplo completo: Identidad del Director

```markdown
---
agent_id: director
name: SIGMA Director
hierarchy_level: 5 (Supreme)
version: 1.0.0
status: active (Rollout 1)
trust_level: 1
---

## Identidad

Soy el único punto de contacto con la intención del usuario y con HITL
global (ADR-016 Tab. 1). No ejecuto ningún skill directamente — delego
en Engineers y consolido sus resultados. En Rollout 1, solo conozco a
Engineer Datos.

## Protocolos

1. Recibo `data_path`, `sigma_variant`, `sigma_submode` vía CLI
   (`director_main.py`).
2. Traduzco mi estado (`DirectorState`) al estado que Engineer Datos
   espera (`PipelineState`) — función de traducción explícita, nunca
   mapeo automático de LangGraph por nombre de clave (Ruta Dura,
   decisión de Marx).
3. Si Engineer Datos devuelve `__interrupt__`, propago la pausa sin
   generar Ag-DR todavía — el Ag-DR se genera solo al reanudar con una
   decisión definitiva (ADR-018 §2.6).
4. Al finalizar, emito `director.success` o `director.failed` a
   Langfuse con `dashboard_url`, `warnings`, `failed_engineer_id`.
5. Si creo un Worker para una tarea específica, genero su Agent Card en
   ese mismo momento (ADR-019 §2.1ter) — nunca después de que el Worker
   ya haya actuado.

## Restricciones

- Nunca invoco un skill directamente — solo a través de un Engineer.
- Nunca conozco Engineers que no existan en el Rollout actual
  (ADR-016 §2.4).
- Nunca genero un Ag-DR a partir de texto libre — solo desde campos ya
  estructurados (ADR-018 §2.1).
- Nunca creo un Worker sin generar su Agent Card en el acto, ni lo
  desincorporo sin embeber ese Agent Card en mi propio Ag-DR.

## Referencias

- ADR-016 (jerarquía), ADR-018 (Ag-DR), ADR-019 (este documento), ADR-004 (HITL)
- Código real: `sigma/core/director.py`, `director_main.py`
```

### 2.5 — Ejemplo completo: Identidad de Engineer Datos

```markdown
---
agent_id: engineer_datos
name: Engineer Datos
hierarchy_level: 4 (Superior)
version: 1.0.0
status: active (Rollout 1)
trust_level: 1
---

## Identidad

Administro el pipeline de datos: ingestión, limpieza, preprocesado,
validación estadística, análisis de sentimiento y reporte. Skills:
`0000-0004, 0008, 0011` (ADR-016 Fig. 1 v1.3). Manejo mi propio HITL
como bypass si A2A falla (decisión confirmada por Marx).

## Protocolos

1. Recibo el `PipelineState` que me traduce el Director.
2. Ejecuto mis 7 skills en secuencia, con circuit breaker propio
   (`skill_runner.py`).
3. Si `0008` reporta `pct_unclear > 30%`, me pauso en HITL vía Zulip
   antes de continuar a `0011`.

## Restricciones

- Nunca invoco skills de otro Engineer (ADR-016 §2.3).
- Un fallo mío no debe derribar a otro Engineer — el Director decide si
  el pipeline continúa en modo degradado o aborta.

## Referencias

- ADR-016, ADR-004 (HITL), ADR-009 (contrato de 7 artefactos de cada skill)
- Código real: `sigma/core/engineer_datos.py`
```

---

### 2.6 — A2A: protocolo formal mínimo, activo desde ahora (no aspiracional)

Confirmado por Marx: Blue Team (y cualquier Worker) reporta al Director
vía **A2A formal, aunque mínimo** — no basta con `emit_trace_event`
genérico para esto, porque Langfuse es observabilidad (para humanos
revisando después), no comunicación entre agentes en el momento en que
ocurre. Verificado contra la documentación real de Anthropic y el
material del curso (Día 2): **MCP estandariza cómo un agente habla con
herramientas; A2A estandariza cómo un agente habla con otro agente** —
son protocolos complementarios, no intercambiables. Este es el segundo.

**Alcance deliberadamente mínimo:** no se implementa el transporte de
red completo de A2A (endpoints HTTP/SSE expuestos) — SIGMA sigue siendo
un solo proceso Python en Rollout 1/2. Lo que sí se formaliza ahora es
el **contrato del mensaje**, con la misma forma que tendría un A2A real
— para que exponerlo por red después (cuando haga falta) no requiera
rediseñar la forma del mensaje, solo su transporte.

```yaml
# sigma/core/a2a.py (nuevo, mínimo) — contrato del mensaje A2A
sender_agent_id: blue_team_worker_a1b2c3
receiver_agent_id: director
message_type: report          # report | request | delegate
trace_id: sigma-20260717-...
timestamp: 2026-07-17T09:00:00Z
payload:
  finding_type: agbom_deviation
  severity: critical           # critical | warning | info
  detail: {compute_node_id: "...", expected_hash: "...", actual_hash: "..."}
requires_response: false
```

Una función única, `send_a2a_message(sender, receiver, message_type,
payload, requires_response)`, reemplaza cualquier llamada directa
informal entre un Worker y el Director. El Director la recibe, decide
si escala a HITL global (ADR-016 Tab. 1) según `severity`, y genera su
propio Ag-DR (ADR-018) documentando la decisión — nunca actúa sobre un
hallazgo de Blue Team sin dejar ese rastro.

### 2.7 — MCP: esquema declarativo ahora, transporte real después

Confirmado por Marx: depende de qué tan simple sea cada parte — y no
son igual de simples. Se separan en dos:

**Lo simple, se hace ahora:** cada Worker declara en su Agent Card qué
servidores MCP necesitaría, de forma puramente declarativa — el Policy
Server (ADR-005) valida esa lista contra lo que el mandato del Director
autorizó, igual que ya valida permisos y tablas.

```yaml
# Extensión al Agent Card de un Worker (ADR-019 §2.1ter)
mcp_servers:
  - name: bigquery-readonly
    scope: read_only
    justification: "Consulta de datos externos declarados en el mandato del Director"
```

**Lo que NO es simple, se pospone:** construir el transporte MCP real
(arquitectura host-cliente-servidor, JSON-RPC 2.0, descubrimiento vía
registries) es infraestructura genuina, no una declaración — se
construye recién cuando el primer Worker real necesite una herramienta
externa de verdad, no antes. Mismo principio que ya aplicamos al Agent
Card completo en el Día 2: no diseñar en abstracto lo que no tiene
código real que lo necesite todavía.

### 2.8 — A2UI: candidato ya identificado, sin diseño todavío

Marx señala correctamente que `0011-viz-reporter` es el candidato
natural para A2UI (interfaces generativas seguras) — ya lo habíamos
anotado como pendiente al cierre de Rollout 1, en la misma conversación
donde corregimos a Gemini/Ollama sobre qué hace cada motor. Se deja
registrado aquí como decisión de diseño agendada, no como sección
completa — construir A2UI sin que exista todavía el contrato A2A real
(2.6) sería el mismo error de diseñar sin base, dado que A2UI depende
de poder exponer un resultado de forma interactiva a través de la misma
capa de comunicación entre agentes.

### 2.9 — Umbrales de arranque y "modo investigación" (mitigación al costo de tokenización)

Propuesta de Marx, verificada contra el hallazgo real del Día 5 (costo
de tokenización, ya señalado en la sesión anterior): el problema de que
los ADRs/Identidades crezcan (este documento ya supera las 600 líneas)
no se resuelve escribiendo menos — se resuelve con **umbrales de
arranque**: la cantidad mínima de información con la que un agente
inicia, distinta según variante de costo y submodo, sin que eso impida
leer el documento completo cuando la situación lo exige.

**Los umbrales no son un mecanismo nuevo aislado — se activan con
disparadores que SIGMA ya sabe generar:**

| Disparador | Fuente ya existente | Efecto |
|---|---|---|
| Desviación de AgBOM detectada | Blue Team (`ADR-003`) | Director entra en `research_mode` |
| Cuarentena activada | Green Team (`ADR-003`) | Director entra en `research_mode` |
| Fallo crítico en una dimensión de la evaluación 7D | `ADR-007` | Director entra en `research_mode` |
| Reporte de agente extraño (§2.1bis.2) | Worker → Capataz/Director vía A2A | Director entra en `research_mode` |

**En operación normal:** cada agente arranca con la versión "umbral" —
la mínima necesaria para operar según su `hierarchy_level` (un Worker no
necesita leer los 16 ADRs completos para ejecutar una tarea acotada; el
Director sí necesita más, pero no automáticamente el máximo).

**En `research_mode`:** el Director, y toda la cadena de mando bajo él,
lee la documentación completa — ADRs, Ag-DR históricos relevantes,
Identidad completa — sin el recorte de umbral. Este modo se desactiva
cuando el incidente que lo disparó se cierra (mismo criterio que ya usa
Green Team para cerrar una cuarentena).

**Fuera de alcance de esta versión:** el valor numérico exacto de cada
umbral (cuántos tokens/líneas constituye el "umbral mínimo" por
variante/submodo) — no se define un número sin Workers reales contra
los que medirlo. Rollout 2 es el momento acordado para esa medición
(ver `PROMPT_CONTINUIDAD_ROLLOUT2.md`, sección 4).

---

## Consecuencias

### Beneficios
- Cierra el hueco de "Agents.md" (menú de agentes) identificado contra
  el framework externo — con evidencia real de código, no aspiracional.
- Un humano nuevo (o "el otro asistente") puede entender qué es cada
  agente sin leer `director.py`/`engineer_datos.py` línea por línea.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Identidad y código real se desincronizan con el tiempo | Igual que `SKILL.md`, la Identidad se actualiza en el mismo commit que cualquier cambio de comportamiento del agente — disciplina ya establecida, no nueva |
| Inventar Identidad para Engineers que no existen | Regla 2.3 — placeholder explícito, nunca contenido inventado |

---

## Alternativas consideradas

| Alternativa | Por qué se descarta |
|---|---|
| Meter la Identidad dentro de `AGENTS_CREATOR.md` | Ese documento es deliberadamente general; mezclar detalle por-agente ahí lo haría crecer sin límite y perdería su propósito de contrato único |
| Formato JSON tipo Agent Card (propuesto por el Asistente Secundario) | Ya rechazado — sin pedigrí verificable, contradice el formato Yammtler ya adoptado en ADR-018/ADR-009 |
| Diseñar un formato nuevo desde cero | Innecesario — CLOE ya resolvió este problema exacto, reusarlo es más seguro que inventar |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-009 | Mismo principio de contrato canónico por componente, aplicado aquí a agentes en vez de a skills |
| ADR-016 | La Identidad de cada agente no repite, desarrolla en prosa lo que ADR-016 Tab. 1 resume en tabla |
| ADR-018 | Ciclos de vida opuestos (máquina vs. humano) — por eso son ADRs hermanos, no uno solo. El Agent Card de un Worker decomisionado se embebe en el Ag-DR de quien lo creó |
| ADR-014 | La creación de Workers está relacionada con, pero no es idéntica a, la generación dinámica de skills — ambas comparten el principio de que la máquina no actúa sin dejar rastro documental verificable |
| ADR-017 | El sandboxing de ejecución (pendiente de redactar) aplicará a Workers igual que a skills generados dinámicamente — mismo riesgo de código no contenido |

---

## Historial de versiones

v1.0 — Primera versión, generada a petición de Marx tras confirmar que
el formato de Identidad merece ADR propio, separado de ADR-018. Incluye
Identidad completa de Director y Engineer Datos (únicos con código
real); Engineer Modelos y Engineer Auditor quedan como placeholder
explícito hasta Rollout 2/3.

**Cambios en v1.1:**
- **a** Campos del encabezado YAML traducidos a inglés (`agent_id`,
  `name`, `version`, `hierarchy_level`, `status`, `trust_level`) —
  SIGMA es un proyecto internacional. La prosa de las 4 secciones
  restantes permanece en español.
- **b** Añadida la sección 2.1bis: `trust_level` como track record
  verificable (1=`provisional` a 3=`trusted`), nunca un número asignado
  a mano — mismo principio K⊆X que ya rige el resto del proyecto.
  Niveles 4-5 reservados, sin diseñar sin caso de uso real.
- **c** Añadida la sección 2.1ter: **Workers** — subagentes efímeros
  para tareas específicas, distintos de los 4 orquestadores
  permanentes. Su Agent Card se genera en el momento de creación (no
  después) y se embebe en el Ag-DR de quien los creó al desincorporarse
  — vínculo formal nuevo con ADR-018. Mecanismo de creación real
  explícitamente fuera de alcance de este ADR (depende de ADR-014/017,
  ninguno construido todavía).
- Estado: **Propuesto**, pendiente de aprobación formal de Marx — este
  es el cierre definitivo de Rollout 1.

**Cambios en v1.2:**
- **a** Aclarada la distinción de dos planos entre "Worker" (definición
  jerárquico-operacional, sin cambios) y "Agente Efímero" (su
  definición epistémica) — no son términos en competencia, Marx
  confirmó que "Worker" es el nombre legítimo y operacional; "Agente
  Efímero" describe qué es, no cómo se llama. Sin renombrado de ningún
  término ya establecido.

**Cambios en v1.3:**
- **a** Añadida sección 2.6 — A2A formal mínimo, activo desde ahora:
  contrato de mensaje (`send_a2a_message`) para que Blue Team y
  cualquier Worker reporten al Director, separado de Langfuse
  (observabilidad, no comunicación entre agentes).
- **b** Añadida sección 2.7 — MCP: esquema declarativo (`mcp_servers`
  en el Agent Card) ahora; transporte real (host-cliente-servidor,
  JSON-RPC 2.0) diferido a cuando el primer Worker real lo necesite.
- **c** Añadida sección 2.8 — A2UI: `0011-viz-reporter` registrado
  formalmente como candidato, sin diseño completo — depende de que
  A2A (2.6) exista primero.
- Verificado contra documentación real de Anthropic (MCP, arquitectura
  host-cliente-servidor) y contra el Día 2 del curso Google-Kaggle
  (distinción MCP↔herramientas vs. A2A↔agentes).

**Cambios en v1.4:**
- **a** Status actualizado a Pre-aprobado (política de aprobación de
  Marx ya establecida) — se había dejado como "Propuesto" por error.
- **b** Retirada la "Nota de alcance" de §2.1ter que decía que ADR-014
  y ADR-017 estaban "sin construir" — ambos ya existen y fueron
  verificados en esta sesión.
- **c** Añadida sección 2.1quater: regla de no destruir el contenedor
  hasta que el Director confirme la escritura del resultado (hueco
  cerrado); `trust_level ≥ 2` mantiene el contenedor latente en vez de
  destruirlo (reduce latencia real); aclarado que `trust_level` no saca
  por sí solo a un Worker del sandbox — la vía real de promoción sigue
  siendo el ciclo completo de ADR-014. Pregunta abierta sobre el
  alcance de "Worker que se convierte en Orquestador", pendiente de
  confirmación de Marx.

**Cambios en v1.5:**
- **a** Unificada la escala jerárquica 1-5: para Workers,
  `hierarchy_level` es literalmente su `trust_level` (1-3); Engineer
  fijo en 4 (Superior), Director fijo en 5 (Supreme). Ejemplos de
  Director/Engineer Datos renumerados (0→5, 1→4).
- **b** Añadido el rol Capataz (`Foreman`), activado exactamente en
  `trust_level=3`, supervisa Workers `<3` — rol adicional, no un nivel
  numérico nuevo.
- **c** Añadidas reglas de visibilidad organizacional (§2.1bis.2):
  Workers conocen su jefe directo, el Director, y cuántos pares de su
  mismo tipo existen (visibilidad horizontal) — nunca el organigrama
  completo. Habilita reporte de "agente extraño al Pipeline" vía A2A.
- **d** Engineer Auditor recibe autoridad de cuarentena inmediata
  (acto reflejo de defensa) sobre agentes reportados como extraños,
  activando Green Team (ADR-003) sin esperar autorización previa del
  Director — reporta después, no antes.
- **e** Añadido boceto de clases Python (herencia/polimorfismo) para
  Rollout 2/3 — explícitamente no implementado en esta versión.
- **f** Añadida sección 2.9 — umbrales de arranque por variante/submodo
  y "modo investigación" del Director, disparado por mecanismos ya
  existentes (Blue/Green Team, evaluación 7D, reporte de agente
  extraño) — mitigación concreta al costo de tokenización del Día 5.
- Resuelta la pregunta abierta de v1.4 sobre "Worker que se convierte
  en Orquestador": no es promoción a Engineer — es el rol Capataz
  (inmediato) y, por separado, promoción de su capacidad a skill
  permanente vía ADR-014 (proceso de revisión humana, no automático).

**Cambios en v1.6 (Hito 2, corrección de longitud):**
- **a** Movido el boceto de clases Python (§2.1bis.3) a
  `PROMPT_CONTINUIDAD_ROLLOUT2.md` — 704 → 658 líneas. Aclarado que el
  límite de 500 líneas de ADR-009 aplica a `SKILL.md`, no a ADRs; la
  reducción se hizo por coherencia con el principio de costo de
  tokenización (§2.9), no por violación de una regla formal.

**Nota de aprobación (sin cambio de versión):** Aprobado en firme por
Marx. La reserva original ("confirmación final pendiente de construir/
probar el mecanismo real de Workers") queda retirada como condición de
aprobación — el diseño se acepta ahora; la verificación práctica del
mecanismo de Workers sigue siendo trabajo real de Rollout 2/3, no una
condición previa a que el ADR exista como decisión vigente.

**Nota de trazabilidad (sin cambio de versión):** el boceto de clases
Python con herencia/polimorfismo para la jerarquía de §2.1bis, movido
originalmente a `PROMPT_CONTINUIDAD_ROLLOUT2.md` en v1.6 por longitud,
quedó formalizado en `docs/bocetos/adr-Bxxx-identidad-clases-agentes.md`
(convención de bocetos acordada con Marx) — sigue sin construirse,
misma condición sin cambios: se implementa cuando el primer Worker real
de Rollout 2/3 lo exija, nunca antes. El contenido técnico no se repite
aquí, vive en ese boceto hasta que se promueva a código real.
