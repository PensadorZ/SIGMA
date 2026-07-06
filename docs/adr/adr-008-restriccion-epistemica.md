---
id: ADR-008
titulo: Contención Epistémica Estricta (K ⊆ X)
version: 1.3
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-008 v1.2
referencias-minimas: ADR-001, ADR-002, ADR-007
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-008: Contención Epistémica Estricta (K ⊆ X)

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el diagrama de las tres capas de implementación. Se añade
Tab. 1 con los estados de respuesta estándar ante diferentes situaciones de
datos insuficientes. Se incorpora el histórico de versiones.

---

## Contexto

Los modelos de lenguaje generan texto estadísticamente plausible. Cuando el
contexto no contiene la información necesaria, el modelo completa el gap con
texto que puede ser factualmente incorrecto. En SIGMA, una alucinación no es
solo un error de calidad: puede ser un error de negocio con consecuencias
reales.

---

## Decisión

Todo agente de SIGMA opera bajo la restricción formal `K ⊆ X` donde:
- **X** = conjunto de datos reales observados en la ejecución actual
- **K** = conjunto de afirmaciones que el agente puede hacer

El agente tiene **prohibido** hacer afirmaciones sobre elementos fuera de X.

### Fig. 1 — Las tres capas de implementación de K ⊆ X

```
CAPA 1 — Contrato en el prompt del Orquestador
─────────────────────────────────────────────────
"Solo puedes usar conocimiento de los datos en X_observed.
 Ante vacíos de información → DATOS_INSUFICIENTES.
 Las hipótesis deben marcarse como ASSUMPTION en el Grafo
 de Suposiciones (ADR-001)."

         ↓ Si el output intenta incluir afirmaciones fuera de X:

CAPA 2 — Verificación automática con Pydantic
─────────────────────────────────────────────────
OutputSchema del skill solo permite campos derivables de
los datos de entrada.
  ├─ VIOLATION → OUTPUT_SCHEMA_VIOLATION → pipeline termina
  └─ OK → output sale del skill

         ↓ Para hipótesis legítimas que van más allá de X:

CAPA 3 — Grafo de Suposiciones (ADR-001)
─────────────────────────────────────────────────
assumption_graph.add(
  entity="...",
  claim="...",
  evidence_count=N,
  status="PROPOSED"   ← Nunca presentado como hecho en el output
)
```

### Linaje de datos como requisito de implementación

Para que una afirmación sea verificable como perteneciente a X, cada fila
del dataset debe llevar un campo `trace_id` que permita rastrear su origen
y transformaciones según ADR-002. Sin linaje, `K ⊆ X` es verificable solo
a nivel de schema, no de dato individual.

### La restricción aplica al 100%

La verificación Pydantic opera en el 100% de los outputs. El LLM-as-Judge
del 5% de ADR-007 es una evaluación de intención del usuario, no de
restricción epistémica. Son capas diferentes con propósitos diferentes.

### Tab. 1 — Respuestas estándar ante datos insuficientes

| Situación | Respuesta estándar | Procesable por el Orquestador |
|---|---|---|
| Dato completamente ausente | `DATOS_INSUFICIENTES` con indicación del dato faltante | Sí |
| Dato fuera del rango aceptable | `DATOS_FUERA_DE_RANGO` con valor recibido y rango esperado | Sí |
| Hipótesis basada en inferencia | `ASSUMPTION` con claim, evidencia disponible y estado `PROPOSED` en el Grafo | Sí |
| Dato presente con baja confianza del modelo | `UNCLEAR` con la puntuación de confianza | Sí |

---

## Consecuencias positivas

- Elimina alucinaciones por diseño, no por prompt engineering.
- Los outputs son auditables: toda afirmación puede rastrearse hasta su dato
  fuente en X.
- La verificación Pydantic es automática y de coste cero.

## Consecuencias negativas

- El agente no puede hacer generalizaciones creativas basadas en su
  entrenamiento.
- Los outputs `DATOS_INSUFICIENTES` pueden frustrar a usuarios que esperan
  una respuesta completa.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Solo prompt engineering | El modelo ignora la instrucción bajo presión de contexto |
| RAG sin K⊆X | Reduce alucinaciones pero no las elimina formalmente |
| Umbral de confianza del modelo | Los modelos están mal calibrados |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se añadió el linaje de datos como requisito de implementación
  de K⊆X.
- **b.1.2** Se reforzó que la restricción aplica al 100% de los resultados
  mediante Pydantic, aclarando la distinción con el 5% del LLM-as-Judge.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el diagrama de las tres capas de implementación.
- **b** Se añadió Tab. 1 con los estados de respuesta estándar ante diferentes
  situaciones de datos insuficientes.
