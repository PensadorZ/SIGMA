---
id: ADR-021
titulo: Alineación Regulatoria y de Gestión de Riesgo de IA — Marco Multi-Jurisdiccional para SIGMA
version: 1.1
estado: Propuesto — pendiente de aprobación formal final
fecha-original: 2026-07
fecha-revision: 2026-07
supersede: ADR-021 v1.1 (Alineación Voluntaria de Gobernanza con Principios de Gestión de Riesgo de Modelos, SR 26-02) — eliminado por Marx, contenido preservado como motivación histórica en §5
referencias-minimas: ADR-001, ADR-007, ADR-008, ADR-009, ADR-016, ADR-017, ADR-018
milestone-de-aplicacion: Hito 2 (documental) / continuo
aprobado-por: pendiente de confirmación final
nombre-archivo: ADR-021_regulatory_law.md
---

# ADR-021: Alineación Regulatoria y de Gestión de Riesgo de IA — Marco Multi-Jurisdiccional para SIGMA

## Resumen ejecutivo

Este ADR reemplaza a la versión anterior de `ADR-021`, limitada a
SR 26-02. Amplía el alcance a un panorama completo de marcos de gestión
de riesgo de IA y regulación aplicable: **NIST AI RMF**, **ISO/IEC
42001** (con miras explícitas a certificación futura), **ISO/IEC
23894**, **legislación estatal de EE. UU.** (caso de estudio: Colorado),
y **RGPD/GDPR**. Establece además un Programa Base de Sistema de
Gestión de IA (AIMS), viable para un operador único, con proyección
declarada de escalamiento hacia certificación formal conforme SIGMA
crezca. El texto de SR 26-02 que motivó la primera versión se conserva
íntegro en §5, como antecedente histórico.

---

## Contexto

Un sistema agéntico que gestiona datos, incluyendo texto generado por
personas vía el pipeline de sentiment analysis, opera en un espacio
regulatorio fragmentado, compuesto por marcos voluntarios sin fuerza
legal, un estándar certificable sin obligación inmediata de
certificarse, y al menos una ley con fuerza vinculante que no depende
de qué marco de inteligencia artificial (IA) se adopte.

El primero de estos marcos es el **Marco de Gestión de Riesgo de
Inteligencia Artificial del NIST** (NIST AI RMF, por las siglas en
inglés de *National Institute of Standards and Technology — Artificial
Intelligence Risk Management Framework*), publicado por el Instituto
Nacional de Estándares y Tecnología de los Estados Unidos (National
Institute of Standards and Technology [NIST], 2023). Es un marco
voluntario, no certificable, organizado en cuatro funciones (Gobernar,
Mapear, Medir, Gestionar).

El segundo es la norma **ISO/IEC 42001:2023**, *Tecnología de la
información — Inteligencia artificial — Sistema de gestión*, publicada
conjuntamente por la Organización Internacional de Normalización (ISO)
y la Comisión Electrotécnica Internacional (IEC) (International
Organization for Standardization & International Electrotechnical
Commission, 2023a). Establece un Sistema de Gestión de IA (AIMS, por
*AI Management System*) y es, a diferencia del NIST AI RMF,
certificable mediante auditoría externa de tercero.

El tercero es la norma **ISO/IEC 23894:2023**, *Tecnología de la
información — Inteligencia artificial — Orientación sobre gestión de
riesgo*, también de ISO/IEC (International Organization for
Standardization & International Electrotechnical Commission, 2023b).
Es la guía metodológica de identificación, análisis, evaluación y
tratamiento de riesgo específico de IA, y extiende a la norma general
ISO 31000 de gestión de riesgo.

El cuarto es el **Reglamento General de Protección de Datos** (RGPD;
en inglés, *General Data Protection Regulation*, GDPR), Reglamento
(UE) 2016/679 del Parlamento Europeo y del Consejo (European Parliament
and Council of the European Union, 2016). Es una ley vinculante de
aplicación extraterritorial: rige el procesamiento de datos personales
de residentes de la Unión Europea (UE) independientemente del marco de
gestión de riesgo de IA que una organización adopte.

El quinto es la **Ley de Inteligencia Artificial de Colorado** (Colorado
AI Act), promulgada originalmente como S.B. 24-205 (Colorado General
Assembly, 2024) y sustancialmente enmendada por S.B. 189/S.B. 26-189,
firmada el 14 de mayo de 2026, que redujo su alcance y pospuso su fecha
efectiva al 1 de enero de 2027 (Colorado General Assembly, 2026).

El sexto es la guía **SR 26-02** (SR Letter 26-2), emitida por la Junta
de Gobernadores del Sistema de la Reserva Federal de los Estados Unidos
(Board of Governors of the Federal Reserve System, 2026), que deroga y
reemplaza a la guía SR 11-7 de gestión de riesgo de modelos.

A partir de este punto, el documento usa únicamente los acrónimos
(NIST AI RMF, ISO/IEC 42001, ISO/IEC 23894, RGPD, Colorado AI Act,
SR 26-02) sin repetir su expansión ni su cita completa — la referencia
bibliográfica completa de cada uno queda consolidada en la sección de
Referencias Bibliográficas al cierre del documento.

Este ADR ordena ese panorama y, adicionalmente, formaliza el
compromiso de que la gobernanza de SIGMA no espera a tener equipo o
clientes para constituirse — la responsabilidad hacia usuarios y
clientes potenciales comienza con el operador único, documentada desde
el origen.

---

## Decisión

### 2.1 — Panorama de marcos, sin mezclarlos

| Marco | Naturaleza | Jurisdicción | ¿Aplica a IA agéntica? |
|---|---|---|---|
| **NIST AI RMF 1.0** | Voluntario, no certificable, autodeclarable | EE. UU. | Sí — tecnológicamente neutral, cubre ciclo de vida completo |
| **ISO/IEC 23894** | Guía metodológica de gestión de riesgo (extiende ISO 31000) | Internacional | Sí — mismo alcance que NIST AI RMF |
| **ISO/IEC 42001** | Estándar de sistema de gestión (AIMS), certificable por auditoría de tercero | Internacional | Sí — con proyección de certificación formal, ver §2.3bis |
| **Colorado AI Act (SB 24-205, enmendada por SB 189, mayo 2026)** | Ley estatal vinculante, fecha efectiva pospuesta al 1 de enero de 2027 | Colorado, EE. UU. | No aplica directamente — el alcance enmendado se limita a tecnología de toma de decisiones automatizada en empleo, vivienda, crédito, salud; SIGMA no toma ese tipo de decisiones sobre personas |
| **RGPD/GDPR** | Ley vinculante, aplicación extraterritorial | Unión Europea | Aplica de forma independiente a cualquier marco de gestión de riesgo de IA, condicionado al procesamiento real de datos personales — ver §2.6 |

### 2.2 — NIST AI RMF: correspondencias por función

| Función NIST | Mecanismo de SIGMA | ADR de origen |
|---|---|---|
| **Gobernar** | `AGENTS_CREATOR.md`, jerarquía 1-5, revisión humana obligatoria de cada ADR | `ADR-016`, `ADR-019` |
| **Mapear** | Catálogo de skills + tabla de ADRs como inventario; K⊆X como delimitación de alcance | `ADR-008`, `ADR-009` |
| **Medir** | Evaluación multidimensional 7D; `_run_permutation_bootstrap` de `0004-statistical-validator` | `ADR-007` |
| **Gestionar** | HITL vía Zulip + `interrupt()`; Ag-DR como monitoreo continuo | `ADR-018` |

### 2.3 — ISO/IEC 42001 (AIMS): correspondencias, con miras a la certificación

| Control típico de un AIMS | Mecanismo de SIGMA | ADR de origen |
|---|---|---|
| Supervisión humana / control operacional | HITL vía Zulip, `interrupt()` + checkpointer | `ADR-004`, `ADR-018` |
| Gestión de acceso y control de agentes | Sandboxing, jerarquía 1-5, visibilidad acotada del Capataz | `ADR-017`, `ADR-019` |
| Registro documentado / trazabilidad de decisiones | Trazabilidad Langfuse | `ADR-011` |
| Monitoreo continuo del sistema | Auditoría de trayectoria | `ADR-013` |
| Gestión de memoria/conocimiento operativo | Ag-DR | `ADR-018` |
| Gestión de riesgo de alcance/deriva del sistema | Restricción epistémica K⊆X | `ADR-008` |

#### 2.3bis — Programa Base AIMS: viable desde el operador único, con proyección de escalamiento

La gobernanza formal no depende del tamaño del equipo. Un AIMS en
Nivel 0 —documentado, con evidencia real acumulándose desde el
origen— constituye el fundamento legal y organizacional sobre el cual
SIGMA escala hacia niveles de responsabilidad mayores conforme
incorpore usuarios y clientes reales.

**Nivel 0 — Operador único, en curso:**

| Elemento del AIMS (cláusula ISO 42001 de referencia) | Implementación actual |
|---|---|
| Política de IA documentada (§5.2) | Formalizada en `AGENTS_CREATOR.md`, como Política del AIMS de SIGMA |
| Alcance declarado del sistema de gestión (§4.3) | Declaración explícita de componentes dentro (Director, Engineers, skills) y fuera (proyectos externos como `ADR-B026`) |
| Roles y responsabilidades (§5.3) | Documentados por función —política, revisión, operación— aun ejercidos por un único operador, siguiendo el mismo principio de separación de funciones que rige controles internos en organizaciones pequeñas |
| Registro de riesgo (§6.1) | Las tablas de correspondencias y vacíos de este ADR, mantenidas como registro vivo |
| Revisión de dirección (§9.3) | Revisión trimestral programada de ADRs vigentes, vacíos abiertos e incidentes del periodo, documentada con fecha y conclusiones |
| Gestión de incidentes (§8.2) | El incidente de `tracing.py` (Rollout 1, observaciones huérfanas de Langfuse), documentado con causa raíz y corrección, constituye la primera entrada del registro de incidentes del AIMS |

**Nivel 1 — Primeros datos reales de usuarios o clientes:**
Evaluación de impacto de IA formal previa a cada despliegue con datos
reales; base legal documentada para cualquier dato personal procesado;
aviso de privacidad y términos de servicio antes de exponer SIGMA a un
tercero.

**Nivel 2 — Escalamiento a equipo o clientes formales:**
Auditoría interna (eventualmente por tercero contratado); consolidación
del expediente de evidencia de Niveles 0 y 1; decisión, en ese momento,
sobre si el volumen o la exigencia contractual de clientes justifica la
certificación formal ISO/IEC 42001.

Cada nivel constituye evidencia acumulada y verificable con fecha,
construida como fundamento progresivo de gobernanza — no como una
promesa diferida a un futuro indeterminado.

### 2.4 — ISO/IEC 23894: correspondencias metodológicas

| Etapa | Mecanismo de SIGMA | ADR de origen |
|---|---|---|
| Identificar riesgo | Alertas Blue/Green Team | `ADR-016`, `ADR-019` |
| Analizar/evaluar riesgo | "Modo investigación" del Director, activado por umbral | `ADR-019` §2.9 |
| Tratar riesgo | Escalamiento HITL | `ADR-004` |
| Seguimiento de riesgo residual | Índice de embeddings de patrones de Ag-DR | `ADR-023` |

### 2.5 — Colorado AI Act: por qué no aplica hoy

La ley original (2024) habría exigido programa de gestión de riesgo,
evaluaciones de impacto y deber de cuidado frente a discriminación
algorítmica para sistemas de alto riesgo. La enmienda de mayo 2026
(SB 189) elimina esas obligaciones y estrecha el alcance a divulgación
y transparencia sobre tecnología de decisión automatizada en empleo,
vivienda, crédito, salud y educación, con fecha efectiva pospuesta al
1 de enero de 2027. SIGMA no toma decisiones consecuentes sobre
personas en ninguna de esas categorías — es una herramienta de análisis
de Big Data, no un sistema de decisión automatizada sobre sujetos. Esta
conclusión no se reabre salvo que SIGMA cambie de propósito hacia
decisiones sobre personas.

### 2.6 — RGPD/GDPR: obligación paralela, no resuelta por ningún marco de riesgo de IA

Ningún marco de gestión de riesgo de IA sustituye una obligación de
protección de datos ya vigente. Los datasets de desarrollo usados hasta
ahora (Tirendaz/Kaggle, Zenodo, Mendeley) son públicos y de
investigación — se realizó una revisión de la descripción y términos de
cada dataset, confirmando que no incluyen información sensible
declarada, y las políticas de uso de Kaggle prohíben explícitamente la
inclusión de datos personales identificables por parte de quien publica
el dataset. Esto establece una base razonable, aunque no una auditoría
legal formal, para sostener que los datos de desarrollo actuales no
contienen datos personales de residentes de la UE.

SIGMA, en cualquier despliegue futuro, podría procesar datos de sujetos
identificables europeos; en ese escenario se aplicarían las salvaguardas
de seguridad correspondientes (cifrado en tránsito y en reposo,
minimización de datos, base legal documentada antes de procesar). Este
punto queda en standby, sujeto a verificación posterior conforme
evolucionen las disposiciones legales vigentes de la UE y de EE. UU.

### 2.7 — Relación con `policies.yaml`

Este ADR contiene el razonamiento, el mapeo por marco y las
motivaciones. `policies.yaml` contiene únicamente los parámetros
operativos accionables en runtime derivados de este mapeo —umbrales de
trust_level, condiciones de activación de modo investigación, límites
de sandbox— sin contenido regulatorio en prosa. La separación reafirma
el patrón ya establecido entre `ADR-016`/`ADR-002`/`ADR-017` y
`policies.yaml`.

### 2.8 — Regla de lenguaje

Cualquier material derivado de este ADR, interno o externo, debe
formular la alineación como: *"SIGMA aplica, por diseño, principios de
gestión de riesgo de IA alineados con NIST AI RMF e ISO/IEC 23894, y
mantiene un Programa Base de Sistema de Gestión de IA orientado a
certificación ISO/IEC 42001, en un dominio donde la regulación
vinculante (SR 26-02, Colorado AI Act) aún no impone obligaciones
directas."* Nunca "SIGMA cumple con [marco]" ni "SIGMA está certificado"
sin calificación del nivel real alcanzado.

### 2.9 — Visión declarada: SIGMA como referencia de gobernabilidad agéntica

Se espera que SIGMA, más allá de alinearse con los marcos existentes,
se posicione a mediano plazo como una referencia de gobernabilidad para
ecosistemas de IA agéntica. Este ADR documenta esa dirección como
**motivación declarada** del Programa Base AIMS de §2.3bis — para
cuando SIGMA ocupe ese lugar en la industria en algún punto del tiempo
futuro. La distinción no es cosmética: es el piso legal que le da a
este documento los soportes necesarios para que usuarios e
inversionistas puedan tener tranquilidad, con evidencia de progreso
desde el Nivel 0, y se construye pensando en el futuro que se avecina.
La responsabilidad hacia futuros usuarios y clientes es precisamente lo
que justifica iniciar el Programa Base ahora, como operador único, en
vez de esperar a tener el estándar consolidado para recién entonces
gestionar el riesgo.

---

## Consecuencias

**Beneficios:** escalabilidad y legitimidad certificable y legalmente
vinculante cuando corresponda; establecimiento de los requisitos
mínimos para un Programa Base AIMS con progresión clara hacia
certificación; cumplimiento con las disposiciones legales vigentes
para que los usuarios de este ecosistema se sientan seguros.

**Riesgos y mitigaciones:**

| Riesgo | Mitigación |
|---|---|
| Que se lea como certificación ya obtenida | Regla 2.8 distingue explícitamente "con miras a" de "certificado" |
| Que el estatus de Colorado cambie antes de publicarse | Fecha de verificación documentada en frontmatter |
| Que RGPD se dé por descartado sin verificación completa | §2.6 lo mantiene en standby, no como conclusión cerrada |

---

## Alternativas consideradas

| Alternativa | Por qué se descarta |
|---|---|
| Mantener `ADR-021` limitado a SR 26-02 | Insuficiente frente al panorama internacional y de certificación que se decidió incorporar |
| Aplazar el Programa Base AIMS hasta tener equipo | Contradice la responsabilidad hacia usuarios y clientes potenciales que se busca sostener desde ahora |
| Declarar a SIGMA "conforme" con RGPD sin verificación completa | No sostenible frente a escrutinio; se mantiene en standby en su lugar |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-001 | K⊆X y la Feature Store, base del control de linaje relevante para RGPD |
| ADR-007 | Evaluación 7D, base metodológica de "Medir" (NIST) y "evaluar riesgo" (ISO 23894) |
| ADR-008 | Fundamento epistémico del Programa Base AIMS |
| ADR-009 | Catálogo de skills como inventario, equivalente a "Mapear" |
| ADR-016 | Aislamiento Engineer↔Engineer como separación de responsabilidades |
| ADR-017 | Sandboxing como control de acceso, relevante para ISO 42001 §2.3 |
| ADR-018 | Ag-DR como mecanismo de monitoreo continuo transversal |

---

## §5 — Motivación histórica: SR 26-02

> SR 26-02 deroga y reemplaza a SR 11-7, aplicable a instituciones
> bancarias con más de $30B en activos reguladas por la Reserva
> Federal. Introduce un enfoque basado en riesgo, proporcional a la
> materialidad del modelo, y formaliza *effective challenge*, *model
> inventory*, *ongoing monitoring* y separación entre desarrollo y
> validación.
>
> La nota 3 del documento es explícita: *"Generative AI and agentic AI
> models are novel and rapidly evolving. As such, they are not within
> the scope of this guidance. Nonetheless, a banking organization's
> risk management and governance practices should guide the
> determination of appropriate governance and controls for any tools,
> processes, or systems not covered in this document."*

**Correspondencias verificadas (preservadas del original):**

| Principio de SR 26-02 | Mecanismo de SIGMA | ADR de origen |
|---|---|---|
| *Effective challenge* | Revisión humana obligatoria de cada ADR | `AGENTS_CREATOR.md` §2 |
| *Model Inventory* | Catálogo de skills + tabla de ADRs | `ADR-009` |
| *Documentation* | ADRs + Ag-DR | `ADR-018` |
| *Ongoing Model Monitoring* | Ag-DR, con gate de aprobación humana | `ADR-018` §2.5 |
| *Outcomes Analysis* | `_run_permutation_bootstrap` de `0004-statistical-validator` | `ADR-001`, `ADR-009` |
| Separación desarrollo/validación | Aislamiento Engineer↔Engineer | `ADR-016` §2.3 |

**Vacíos históricos preservados:** rigor proporcional a materialidad
(sin resolver, candidato para `0005-framework-selector`); validación de
modelos de terceros (parcialmente cerrado, `docs/model_cards/`,
pendiente hash de commit de RoBERTa).

---

## Referencias Bibliográficas

Board of Governors of the Federal Reserve System. (2026). *Supervisory guidance on model risk management* (SR Letter 26-2).

Colorado General Assembly. (2024). *Concerning consumer protections in interactions with artificial intelligence systems* (S.B. 24-205).

Colorado General Assembly. (2026). *Concerning automated decision-making technology* (S.B. 26-189).

European Parliament and Council of the European Union. (2016). *Regulation (EU) 2016/679 on the protection of natural persons with regard to the processing of personal data (General Data Protection Regulation)*. Official Journal of the European Union, L119, 1–88.

International Organization for Standardization & International Electrotechnical Commission. (2023a). *Information technology — Artificial intelligence — Management system* (ISO/IEC 42001:2023).

International Organization for Standardization & International Electrotechnical Commission. (2023b). *Information technology — Artificial intelligence — Guidance on risk management* (ISO/IEC 23894:2023).

National Institute of Standards and Technology. (2023). *Artificial intelligence risk management framework (AI RMF 1.0)* (NIST AI 100-1). U.S. Department of Commerce. https://doi.org/10.6028/NIST.AI.100-1

---

## Historial de versiones

**v1.0** — Reemplaza por completo a `ADR-021` v1.1 anterior. Amplía el
alcance de SR 26-02 exclusivamente a un panorama multi-marco. Cambios:
- **a** Panorama multi-marco (NIST, ISO 23894, ISO 42001, Colorado
  actualizado, RGPD) sustituyendo el alcance exclusivo de SR 26-02.
- **b** §2.3 orientada explícitamente "con miras a la certificación",
  con Programa Base AIMS (§2.3bis) por niveles de madurez.
- **c** §2.9 añadida: visión declarada de SIGMA como referencia de
  gobernabilidad agéntica, en tercera persona, como motivación del
  Programa Base.
- **d** §2.6 reescrita: revisión de datasets de desarrollo documentada
  como base razonable, RGPD en standby, no como vacío sin fundamento.
- **e** Contenido de SR 26-02 preservado íntegro en §5 como motivación
  histórica.
- **f** Consecuencias reescritas en clave de gobernanza y cumplimiento
  legal.

**v1.1** — Cambios de esta sesión:
- **a** Contexto reescrito: cada acrónimo (NIST AI RMF, ISO/IEC 42001,
  ISO/IEC 23894, RGPD, Colorado AI Act, SR 26-02) explicado en su
  primera aparición, con cita en estilo APA 7.ª edición; uso del
  acrónimo sin nueva explicación a partir de ese punto.
- **b** Añadida la sección Referencias Bibliográficas al cierre del
  documento, consolidando las siete fuentes primarias citadas.

Pendiente de confirmación final antes de commit.
