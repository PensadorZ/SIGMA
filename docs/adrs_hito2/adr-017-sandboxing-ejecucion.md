---
id: ADR-017
titulo: Sandboxing de Ejecución para Código Generado Dinámicamente y Workers
version: 1.3
estado: Aceptado
fecha-original: 2026-07
fecha-revision: 2026-07
supersede: ninguno
referencias-minimas: ADR-003, ADR-005, ADR-008, ADR-014, ADR-016, ADR-019
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-017: Sandboxing de Ejecución para Código Generado Dinámicamente y Workers

## Resumen ejecutivo de cambios v1.2

Versión anterior era correcta en la decisión pero pobre en el
razonamiento — no explicaba *por qué* cada parámetro de configuración
era necesario, solo lo declaraba. Se profundiza contra el Día 4 del
curso Google-Kaggle (Pillar 1 y Pillar 5 del framework de 7 pilares de
seguridad agéntica): se añade el paralelismo directo entre el "bucle
vibe" del curso y la generación dinámica de ADR-014; se nombra
formalmente el principio "Zero Ambient Authority" detrás del JIT
downscoping; se añaden dos mecanismos que faltaban por completo
(aislamiento de red — por qué "none" y no un allowlist — y listas de
archivos permitidos con deny-by-default); y se documenta que el modelo
Red/Blue/Green de ADR-003 coincide, de forma independiente, con el
Pillar 6 del mismo curso — validación cruzada del diseño ya existente,
no una idea nueva.

## Resumen ejecutivo

Este ADR formaliza el aislamiento de ejecución (sandboxing) para las dos
únicas fuentes de código que SIGMA puede producir sin autoría humana
directa: skills generados dinámicamente (`ADR-014`) y Workers
(`ADR-019` §2.1ter). Existió en las iteraciones previas del proyecto
(contenedores Docker/gVisor) pero no sobrevivió a la consolidación en
los 16 ADRs originales — se recupera aquí, formalmente, como condición
de entrada obligatoria a Rollout 3 (`ADR-016` Tab. 2). **No aplica
retroactivamente a los 7 skills de Engineer Datos de Rollout 1** — todos
son de autoría humana, revisados antes de integrarse; el riesgo que
este ADR contiene es específicamente el de código que el propio sistema
escribe sin ese paso de revisión previa.

---

## Contexto

`ADR-003` ya cubre seguridad en tres momentos — antes (Red Team),
durante (Blue Team), después de un fallo (Green Team) — pero ninguno de
los tres **previene** que un fallo tenga radio de explosión amplio
desde el inicio. Green Team aísla *después* de detectar un problema; el
Policy Server (`ADR-005`) valida *antes* de que una herramienta se
invoque. Ninguno de los dos contiene la *ejecución en sí* mientras
ocurre — si un skill generado dinámicamente tiene un bug real (no
necesariamente malicioso, simplemente defectuoso), hoy no hay nada que
le impida, por ejemplo, escribir fuera de las tablas que le corresponden
o consumir memoria sin límite antes de que cualquier otro mecanismo lo
note.

Este riesgo era teórico hasta Rollout 1 — ahora es concreto: `ADR-014`
ya está aprobado en diseño (código que el Orquestador escribe y
ejecuta con autoridad real), y `ADR-019` introduce Workers que
nacen y mueren dentro de una sola corrida. Ambos son, por diseño,
código sin el mismo historial de revisión humana que tienen los 7
skills actuales — es exactamente el escenario que ADR-014 mismo describe
como "el de mayor riesgo del ecosistema".

**Verificado contra el Día 4 del curso Google-Kaggle (Pillar 1,
"Sandboxes and Supply Chain Defence"):** el propio material del curso
describe el mecanismo de generación dinámica de SIGMA (ADR-014) casi
palabra por palabra — un agente que escribe un script, lo ejecuta, lee
el error, y reescribe la lógica hasta que funciona ("el bucle vibe").
Ese proceso es, por naturaleza, de alta variabilidad — el código
resultante no puede ser confiable implícitamente solo porque compiló
sin errores. El curso es explícito en que correr ese código directamente
junto al agente raíz, o sobre la infraestructura estándar del host,
introduce un nivel de riesgo inaceptable — coincide punto por punto con
por qué este ADR existe.

---

## Decisión

### 2.1 — Alcance: qué código se sandboxea, qué código no

| Código | ¿Se sandboxea? | Por qué |
|---|---|---|
| Los 7 skills de Engineer Datos (Rollout 1) | No, por ahora | Autoría humana, revisados antes de integrarse — mismo nivel de confianza que el resto del código del proyecto |
| Skills generados dinámicamente (`ADR-014`) | **Sí, obligatorio** | Sin revisión humana previa a su primera ejecución de prueba (Green Team, paso 5 de ADR-014) |
| Workers (`ADR-019` §2.1ter) | **Sí, obligatorio** | Nacen sin historial — `trust_level` siempre `1` al crearse (ADR-019 §2.1bis) |
| Futuros skills de Engineer Modelos/Auditor (Rollout 2/3) | No, si son de autoría humana igual que los actuales | Mismo criterio que la fila 1 — el sandboxing depende de *cómo se originó* el código, no de *qué Engineer* lo ejecuta |

### 2.2 — Mecanismo: contenedor efímero de bajo privilegio, con reseteo total de estado

Cada ejecución de código dentro del alcance de 2.1 corre en un
contenedor Docker desechable. **El requisito no es solo "aislar" — es
que el contenedor bloquee el acceso directo al host y reinicie su
estado por completo entre corridas, sin excepción** (verificado contra
el Día 4, "Ephemeral Sandboxing and State Management"): incluso si el
código generado tiene una vulnerabilidad severa o es manipulado hacia
un intento de escape de contenedor, esa lógica comprometida no puede
persistir ni afectar al nodo real mientras el agente sigue iterando.
Esto es lo que justifica `lifetime: single_execution` — no es una
preferencia de diseño, es la condición que hace seguro el propio bucle
de generación dinámica de ADR-014.

```yaml
# sigma/core/sandbox_config.yaml (nuevo, a construir cuando se implemente)
sandbox:
  runtime: docker            # gVisor (runsc) opcional para SIGMA-ME/HE, ver 2.4
  network: none              # sin acceso a red, salvo lista explícita de allow (ADR-005) — ver 2.3bis, por qué "none" y no un allowlist
  memory_limit: "512m"
  cpu_limit: "1.0"
  filesystem: read_only_root # solo /tmp/{run_id} es escribible, efímero
  filesystem_allowlist: []   # deny-by-default — ver 2.3ter
  lifetime: single_execution # el contenedor se destruye al terminar, sin excepción, con reseteo total de estado
```

El contenedor se destruye **siempre** al terminar la ejecución, exitosa
o no — no hay estado persistente entre corridas de un mismo skill
generado, ni siquiera para depurar (el log ya sale vía `tracing.py`
antes de la destrucción).

**Corrección real (a petición de Marx, hueco que había quedado
abierto):** "terminar la ejecución" no significa "el proceso del
Worker retornó" — significa **"el Director confirmó, vía su propio
Ag-DR (ADR-018), que el resultado ya fue escrito"**. Si el contenedor
se destruyera al primer retorno del proceso, un fallo entre "el Worker
calculó el resultado" y "el resultado se escribió con la credencial
JIT" lo perdería para siempre, sin nada que recuperar. Secuencia
correcta:

```
Worker calcula resultado → escribe con credencial JIT (2.3)
        │
        ▼
Director recibe confirmación de escritura (vía A2A, ADR-019 §2.6)
        │
        ▼
Director genera su Ag-DR documentando la actividad del Worker (ADR-018)
        │
        ▼
SOLO ENTONCES: contenedor se destruye
```

**Excepción — Workers con `trust_level ≥ 2` (ADR-019 §2.1bis):** el
contenedor no se destruye entre tareas del mismo tipo de Worker, se
mantiene latente (mismos límites de red/memoria/filesystem, sin
relajar ninguno) — reduce el overhead real de arranque de contenedor
que este mismo ADR señala como consecuencia negativa. Esto **no**
saca al Worker del sandbox — la contención sigue activa, solo se evita
destruir y recrear el contenedor entre usos del mismo tipo de Worker ya
verificado por su historial de Ag-DR.

```yaml
sandbox:
  # ... resto de la configuración sin cambios ...
  lifetime_policy: single_execution  # trust_level 1: se destruye tras confirmación de escritura
                                       # trust_level >= 2: se mantiene latente entre tareas del mismo tipo
```

### 2.3 — Zero Ambient Authority y credenciales de vida ultra-corta (JIT downscoping)

Verificado contra el Día 4 (Pillar 5, IAM): el principio formal que
rige esto se llama **Zero Ambient Authority** — un agente ejecutando
código generado **nunca** hereda los privilegios administrativos
completos de quien lo invocó. En vez de eso, el contenedor recibe
credenciales frescas, explícitamente acotadas a las fuentes de datos
exactas que ese script específico necesita — nunca los permisos
amplios del agente padre.

```
Policy Server (ADR-005, capa estructural)
        │
        ▼
Lee defaults.yaml del skill generado → determina qué permisos declara
        │
        ▼
Emite credencial de vida = duración del contenedor, nunca más
        │
        ▼
Contenedor arranca con ESA credencial únicamente, nunca con .env completo
```

Esto no es un mecanismo nuevo aislado — es una extensión directa de lo
que el Policy Server (`ADR-005`) ya hace en su capa estructural, aplicada
en el momento de arranque del contenedor en vez de solo en el momento de
cada llamada a herramienta. Las credenciales expiran en el momento
exacto en que la tarea concluye — no hay periodo de gracia.

**Vínculo con el "Confused Deputy"** (mismo problema que ya motivó el
diseño de ADR-016 para el enrutamiento Director↔Engineer): el Día 4 lo
describe como el riesgo central de Pillar 5 — un agente sobre-privilegiado
puede ser inducido a ejecutar comandos no autorizados. Zero Ambient
Authority es la mitigación directa: si el contenedor nunca tuvo permisos
amplios que heredar, no hay nada que un ataque de este tipo pueda
explotar más allá de lo que ese script concreto ya podía tocar.

### 2.3bis — Aislamiento de red: por qué "none", no un allowlist

Verificado contra el Día 4 (Pillar 1, egress governance): un allowlist
de dominios aprobados **no es suficiente** — no protege contra
inyecciones de prompt indirectas escondidas en páginas de terceros que
el propio agente decide visitar. Por eso `network: none` es el default
correcto en 2.2, no un allowlist configurable por skill. Si un skill
generado dinámicamente necesita datos externos, debe hacerlo a través
de una caché offline o un servicio de acceso pre-saneado — nunca con
acceso directo a internet desde dentro del sandbox.

### 2.3ter — Listas de archivos permitidos, deny-by-default

Verificado contra el Día 4 (Pillar 5): además del aislamiento de red,
el sistema de archivos del contenedor opera con listas de archivos
explícitamente permitidos (`filesystem_allowlist`, ver 2.2) — nunca una
lista de bloqueo. Por defecto, todo está denegado salvo lo que el
`defaults.yaml` del skill generado declare necesitar — mismo principio
de ADR-006 (nunca hardcodear, siempre declarar explícitamente), aplicado
aquí a rutas de archivo en vez de variables de entorno. Esto bloquea
específicamente el acceso a secretos, scripts de build, y manifiestos
de producción que no tengan relación con la tarea del skill.

### 2.4 — Runtime por variante de costo

| Variante | Runtime del sandbox |
|---|---|
| `SIGMA-FE` | Docker estándar con límites de recursos (2.2) — $0, sin dependencias adicionales |
| `SIGMA-LE` / `SIGMA-ME` | Docker estándar, igual que FE |
| `SIGMA-HE` | Docker + gVisor (`runsc`) opcional — aislamiento de kernel adicional para quien lo necesite; no es requisito, es refuerzo disponible |

No se exige gVisor en ninguna variante — Docker con límites de recursos
ya es el mecanismo real y suficiente para el riesgo descrito en 2.1;
gVisor queda como endurecimiento opcional, coherente con no exigir
infraestructura de pago en SIGMA-FE.

### 2.5 — Vínculo con Green Team (ADR-003)

Si el código dentro del sandbox falla, la secuencia de ADR-003 sigue
aplicando sin cambios (snapshot → aislamiento → `code-reviewer` → Vibe
Diff si el impacto es MEDIUM/HIGH) — el sandbox no reemplaza a Green
Team, limita el daño que puede ocurrir *antes* de que Green Team
intervenga.

**Validación cruzada, no solo referencia:** el Día 4 (Pillar 6,
"Observability & Security Ops") describe, de forma independiente al
proyecto, un triage de seguridad autónomo con tres roles — Blue Team
(observabilidad continua), Red Team (simulación proactiva de ataques),
Green Team (ejecuta "cuarentenas con estado" ante una anomalía) — que
coincide, sin que SIGMA lo haya copiado de ahí, con el modelo Red/Blue/
Green que `ADR-003` ya tenía aprobado desde antes de este curso. No es
un mecanismo que este ADR inventa — es la confirmación de que el diseño
ya existente de SIGMA está alineado con lo que la industria considera
la arquitectura base para esto.

---

## Consecuencias

### Beneficios
- Un skill generado con un bug real no puede, por diseño, exceder los
  límites de recursos ni acceder a más credenciales de las que declaró
  necesitar — contenido desde el primer segundo, no solo después de
  que algo ya falló.
- Costo $0 en `SIGMA-FE` — Docker con límites de recursos no requiere
  ningún servicio de pago ni dependencia nueva (ya está en el stack).

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| Overhead de arrancar un contenedor nuevo por cada ejecución | Aceptable — solo aplica a código generado dinámicamente (2.1), no a los 7 skills de Rollout 1, que siguen corriendo sin este overhead |
| Un skill generado que legítimamente necesita más recursos de los límites por defecto | Los límites son configurables por skill vía su propio `defaults.yaml`, con el mismo principio de ADR-006 (placeholder, nunca hardcodeado) |

---

## Alternativas consideradas

| Alternativa | Por qué se descarta |
|---|---|
| gVisor obligatorio en todas las variantes | Contradice el compromiso de `SIGMA-FE` de operar a $0 sin dependencias adicionales — Docker con límites ya es suficiente para el riesgo real |
| Sandboxing de los 7 skills de Rollout 1 también | Sobre-ingeniería — esos skills ya tienen el nivel de confianza de código revisado por humano; aplicar el mismo aislamiento que a código no revisado no reduce ningún riesgo real, solo añade overhead |
| Confiar solo en el Policy Server, sin contenedor efímero | El Policy Server valida *qué herramienta se llama*, no contiene *cómo se ejecuta* el código del skill mismo — son capas distintas, complementarias, no sustitutas |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-003 | Green Team recupera después de un fallo; este ADR previene el radio de explosión desde el inicio — complementarios |
| ADR-005 | El JIT downscoping (2.3) extiende la capa estructural del Policy Server al momento de arranque del contenedor |
| ADR-008 | K⊆X aplica igual dentro del sandbox — el aislamiento de ejecución no es una excepción a la restricción epistémica |
| ADR-014 | Principal fuente de código dentro del alcance de este ADR (2.1) |
| ADR-016 | Condición de entrada obligatoria a Rollout 3 (Tab. 2) |
| ADR-019 | Los Workers corren obligatoriamente dentro de este sandbox, desde su creación hasta su desincorporación |

---

## Histórico de versiones

v1.0 — Primera versión, redactada a petición explícita de Marx tras
actualizar ADR-003. Recupera el concepto de sandboxing de las
iteraciones previas del proyecto (nunca formalizado en los 16 ADRs
originales), con alcance explícitamente acotado a código generado
dinámicamente y Workers — no aplica retroactivamente a los 7
skills de autoría humana de Rollout 1.

**Cambios en v1.1:** corrección de terminología — "Agente Efímero" se
revirtió a "Worker" en todo el documento (ver ADR-019 §2.1ter para la
distinción entre el plano operacional y el epistémico).

**Cambios en v1.2:** ver resumen ejecutivo de cambios v1.2 arriba —
profundización completa contra el Día 4 del curso Google-Kaggle, sin
cambiar ninguna decisión ya tomada, solo su fundamento y dos mecanismos
nuevos (aislamiento de red, listas de archivos permitidos).

**Cambios en v1.3:** cerrado el hueco de persistencia del resultado
antes de destruir el contenedor (el "fin de ejecución" ahora se define
como confirmación de escritura por el Director, no como el retorno del
proceso) — y añadida la política de contenedor latente para
`trust_level ≥ 2` (ADR-019 §2.1quater), que reduce el overhead de
arranque sin relajar ningún límite de contención.

**Nota de aprobación (sin cambio de versión):** Aprobado en firme por
Marx. Sigue siendo condición de entrada obligatoria a Rollout 3
(`ADR-016` Tab. 2) — la aprobación de diseño no sustituye la
verificación de que el sandbox está aplicado en código real a Engineer
Auditor antes de esa fase.
