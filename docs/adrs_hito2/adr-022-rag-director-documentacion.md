---
id: ADR-022
titulo: RAG del Director sobre Documentación Interna (ChromaDB)
version: 1.0
estado: Aceptado
fecha-original: 2026-07
fecha-revision: 2026-07
supersede: ninguno
referencias-minimas: ADR-008, ADR-016, ADR-019, ADR-021
milestone-de-aplicacion: Hito 3 (prospectiva) — implementación fuera del alcance de Rollout 2/3
aprobado-por: Prof. Marx A. García Delgado
nombre-archivo: adr-022-rag-director-documentacion.md
---

# ADR-022: RAG del Director sobre Documentación Interna (ChromaDB)

## Resumen ejecutivo

Formaliza el mecanismo técnico real detrás de
`Director.enter_research_mode()`, boceto que existe en `ADR-019` §2.9
desde su origen sin cuerpo de implementación. Cuando el Director entra
en modo investigación, este ADR define cómo consulta la documentación
interna de SIGMA (ADRs, Carta de Fundación) para responder con
evidencia trazable en vez de narrativa libre. **No conecta a los
Ag-DR** — esa es una memoria distinta, agente-facing, cubierta por
`ADR-023`.

---

## Contexto

El Director es el único punto de contacto con la intención del usuario
(`ADR-016` Tab. 1). A medida que el ecosistema crece — 21+ ADRs y
subiendo — cargar todo ese contexto en cada conversación se vuelve
costoso en tokens (problema ya anotado desde el Día 5 del curso
Google-Kaggle, sin mecanismo de mitigación real hasta ahora). El
Director necesita poder recuperar solo los fragmentos relevantes de su
propia documentación, bajo demanda, en vez de tener todo cargado
siempre o nada disponible nunca.

---

## Decisión

### 2.1 — Ubicación del módulo

```
sigma/
└── memory/
    └── rag/
        ├── indexer.py      # construye/actualiza la colección Chroma
        ├── retriever.py    # interfaz que el Director consulta
        └── chroma_data/    # persistencia local, SIGMA-FE, $0
```

No vive dentro de `director.py` — es una herramienta que el Director
decide invocar, mismo patrón de contrato que ya usa con los Engineers:
conoce la interfaz, no la implementación interna.

### 2.2 — Alcance de indexación, acotado deliberadamente

Se indexan únicamente documentos **estables y versionados**: los ADRs
aceptados y la Carta de Fundación del Ecosistema (`SIGMA_v2.3.md` en
adelante). **No se indexan Ag-DR** — su volumen y formato cambian con
cada Rollout real; indexarlos aquí sería indexar algo que se desactualiza
en semanas. Los Ag-DR tienen su propio mecanismo, agente-facing, en
`ADR-023`.

### 2.3 — Cumplimiento de K⊆X, no negociable

Si el Director recupera fragmentos y genera una respuesta a partir de
ellos, esa es exactamente la superficie que `ADR-008` existe para
contener. Cada fragmento recuperado lleva metadata trazable:

```yaml
chunk_metadata:
  source_file: adr-018-memoria-operativa-agdr.md
  adr_id: ADR-018
  version: "1.2"
  chunk_id: "018-2.5"
```

El Director puede **parafrasear** lo recuperado, nunca **inventar**
sobre él — mismo principio que ya rige la sección "Resumen de la
corrida" del Ag-DR (`ADR-018` §2.3). Toda respuesta generada en modo
investigación debe poder citar de qué documento y versión salió cada
afirmación.

### 2.4 — Modelo de embeddings

Local, vía `sentence-transformers` (`all-MiniLM-L6-v2`) — sin API de
pago, consistente con `SIGMA-FE` y con el mismo patrón ya usado para
RoBERTa vía Hugging Face. Migración a un embedding de pago queda
reservada para `SIGMA-HE`, si algún día hay un problema real que lo
justifique — no antes.

### 2.5 — Disparador: `Director.enter_research_mode()`

Este RAG es la implementación real del método que `ADR-019` §2.9 ya
declara con firma pero sin cuerpo, disparado por: desviación reportada
por Blue Team, cuarentena de Green Team, o fallo crítico en la
evaluación 7D (`ADR-007`). El research mode consulta este índice antes
de responder, no en cada turno de conversación normal — evita el
mismo problema de costo de tokenización que motivó el ADR en primer
lugar.

---

## Consecuencias

### Beneficios
- Costo $0 en `SIGMA-FE` — Chroma y `sentence-transformers` corren
  localmente, sin dependencia nueva de pago.
- Cierra el hueco de `Director.enter_research_mode()`, que hasta hoy
  era firma sin implementación.

### Riesgos y mitigaciones
| Riesgo | Mitigación |
|---|---|
| El índice queda desactualizado cuando se aprueba un ADR nuevo | `indexer.py` corre como parte del mismo flujo de aprobación de ADR — disciplina equivalente a la ya establecida para Identidad/`SKILL.md` |
| El Director "alucina" citando un ADR que no dice lo que afirma | 2.3 — metadata trazable + regla de parafraseo, verificable mecánicamente igual que D3 de `ADR-007` |

---

## Alternativas consideradas

| Alternativa | Por qué se descarta |
|---|---|
| Meter todo el contexto de ADRs directo en el prompt del Director | Inviable a partir de cierto volumen — el mismo problema de tokenización que este ADR resuelve |
| Pinecone u otro vector DB SaaS | Contradice el compromiso de `SIGMA-FE` de operar a $0; candidato legítimo si algún día se construye `SIGMA-LE/ME` con este componente |
| Indexar también los Ag-DR en el mismo módulo | Mezclaría un consumidor humano-facing (Director conversando contigo) con uno agente-facing (detección de patrones) — responsabilidades distintas, separado en `ADR-023` |

---

## Relación con otros ADRs

| ADR | Relación |
|---|---|
| ADR-008 | K⊆X gobierna la Regla 2.3 sin excepción |
| ADR-016 | El Director consulta este RAG como herramienta, sin alterar su contrato de enrutamiento con los Engineers |
| ADR-019 | Implementa el cuerpo real de `Director.enter_research_mode()` (§2.9) |
| ADR-021 | La trazabilidad citada aquí es evidencia concreta de *documentation* y *effective challenge* |
| ADR-023 | ADR hermano — mismo stack técnico (Chroma), consumidor y alcance de datos distintos |

---

## Historial de versiones

v1.0 — Primera versión, aprobada por Marx en la misma sesión en que se
propuso. Alcance de implementación explícitamente prospectivo (Hito 3)
— el diseño se acepta ahora, el código no se construye antes de que
Rollout 3 cierre.
