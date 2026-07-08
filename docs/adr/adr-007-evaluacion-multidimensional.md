---
id: ADR-007
titulo: Evaluación Multidimensional (7 Dimensiones) con LLM-as-Judge
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-007 v1.3
referencias-minimas: ADR-001, ADR-008, ADR-011
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-007: Evaluación Multidimensional (7 Dimensiones) con LLM-as-Judge

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para explicar primero qué evalúa este
marco y por qué es distinto de K ⊆ X (ADR-008) — uno mide si el output
es honesto, el otro si es bueno — antes de entrar al detalle de las
capas y las siete dimensiones.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el diagrama de capas de evaluación en orden de ejecución.
Se añade Tab. 1 con las siete dimensiones, su método y su coste. Se incorpora
el histórico de versiones.

---

## Contexto

La Evaluación Multidimensional es el mecanismo que decide si un
resultado técnicamente correcto es también un resultado *bueno* — y
existe porque "pasar los tests" y "ser un resultado de calidad" no son
lo mismo. Sin este marco, SIGMA solo sabría si un skill funcionó, nunca
si funcionó bien: si gastó recursos razonables, si entendió lo que el
usuario realmente pedía, o si el código que produjo es mantenible. Este
ADR trabaja junto con la Contención Epistémica K ⊆ X (ADR-008,
restricción sobre qué puede afirmarse como cierto) y con la trazabilidad
de ADR-011 (dónde queda registrada cada evaluación), pero resuelve un
problema distinto de ambos: no si el output es honesto, sino si el
output es bueno.

Un pipeline que supera los tests unitarios puede, aun así, malinterpretar
la intención del usuario, gastar diez veces más recursos de los
necesarios, requerir cinco correcciones antes de dar con lo pedido, o
producir código funcional pero ilegible. Los frameworks de evaluación
tradicionales miden una o dos dimensiones — típicamente solo corrección
funcional. SIGMA necesita un marco completo que capture las siete
facetas reales de lo que hace bueno a un resultado.

---

## Decisión

### Separación fundamental

`K ⊆ X` **no es una dimensión de evaluación**. Es una invariante del sistema
que opera antes de la evaluación en la capa de validación Pydantic del
`OutputSchema`. Si el output viola `K ⊆ X`, el pipeline falla con
`OUTPUT_SCHEMA_VIOLATION` antes de llegar a ninguna dimensión. No hay
contradicción entre el 5% del LLM-as-Judge y la restricción epistémica porque
operan en capas distintas con propósitos distintos.

### Fig. 1 — Capas de evaluación en orden de ejecución

```
Output del skill
        │
        ▼
CAPA 0 — Validación Pydantic (100% de ejecuciones)
  Verifica K⊆X: ¿el output solo contiene campos derivables de los datos?
  ├─ FALLA → OUTPUT_SCHEMA_VIOLATION → pipeline termina
  └─ PASA ↓
        ▼
CAPA 1 — Evaluador rápido determinista (100% de ejecuciones)
  Verifica: reglas estadísticas, campos requeridos, rangos, sesgos conocidos
  Sin consumo de tokens LLM
  ├─ ANOMALÍA detectada → activa LLM-as-Judge (además del muestreo habitual)
  └─ OK ↓
        ▼
CAPA 2 — LLM-as-Judge (5% de ejecuciones + activaciones por anomalía)
  Evalúa D1: intención del usuario
  Modelo: diferente al Orquestador (principio ADR-005)
        │
        ▼
Artefactos de evaluación → Langfuse V2 (trace padre del pipeline)
```

### Tab. 1 — Las siete dimensiones de evaluación

| # | Dimensión | Método de evaluación | Coste |
|---|---|---|---|
| **D1** | Intención del usuario | LLM-as-Judge (5% + activaciones por anomalía) | Bajo |
| **D2** | Corrección funcional | Tests deterministas + Pydantic | Cero |
| **D3** | Corrección visual/comportamental | Validación de schema HTML/dashboard | Cero |
| **D4** | Coste y eficiencia | Métricas Langfuse (tokens, tiempo, convergencia de sesión) | Cero |
| **D5** | Calidad del código | Análisis estático (`pylint`, `bandit`) | Cero |
| **D6** | Calidad de la trayectoria | Comparación con `expected_trajectory` en SKILL.md | Cero |
| **D7** | Capacidad de autoreparación | Ratio reintentos exitosos vs. escalados a HITL | Cero |

Todas las evaluaciones se almacenan en Langfuse V2 como artefactos del trace
padre según ADR-011.

---

## Consecuencias positivas

- El 95% de las evaluaciones no consume tokens LLM.
- La convergencia de sesión (D4) captura la calidad percibida por el usuario
  de forma objetiva sin encuestas.
- Las evaluaciones acumuladas permiten detectar degradación de calidad a lo
  largo del tiempo.

## Consecuencias negativas

- El LLM-as-Judge introduce subjetividad. El muestreo del 5% limita el
  impacto pero no lo elimina.
- La trayectoria esperada en el `SKILL.md` debe mantenerse actualizada.

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Solo tests unitarios | No capturan intención, eficiencia ni trayectoria |
| LLM-as-Judge al 100% | Coste prohibitivo |
| Frameworks externos (Ragas, TruLens) | Las 7 dimensiones de SIGMA son más específicas |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se declaró la separación entre K⊆X (100% Pydantic) y evaluación
  de intención (5% LLM-as-Judge), resolviendo la contradicción con ADR-008.
- **b.1.2** Se añadió el evaluador rápido determinista al 100% como primera
  capa de evaluación.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el diagrama de capas de evaluación en orden de
  ejecución.
- **b** Se añadió Tab. 1 con las siete dimensiones, su método y su coste.
