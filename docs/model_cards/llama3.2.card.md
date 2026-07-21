---
model_id: llama3.2:3b
provider: Meta (vía Ollama, self-hosted)
license: Llama 3.2 Community License Agreement (25 septiembre 2024)
license_type: "NO totalmente abierta — permisiva con restricciones reales, ver abajo"
source_verified: https://www.llama.com/llama3_2/license/, https://ollama.com/library/llama3.2 (texto de licencia real)
verification_date: 2026-07
version_pinned: llama3.2:3b (según .env / Ollama Modelfile real)
sigma_scope: razonamiento ligero / tareas de bajo costo computacional dentro de Engineer Datos
---

## Procedencia

Modelo de Meta, servido localmente vía Ollama sin llamada a API externa
— pero la licencia, a diferencia de `mistral` y `deepseek-coder`, **no
es una licencia de código abierto convencional**.

## Licencia — el único de los 4 con restricciones reales, y hay que documentarlo así

Llama 3.2 Community License Agreement, texto verificado directamente
contra `llama.com` y el propio blob de licencia de Ollama. Restricciones
concretas, no genéricas:

- **Umbral de 700 millones de usuarios activos mensuales:** si el
  licenciatario (o sus afiliados) supera ese umbral, debe solicitar una
  licencia separada a Meta — no aplica a SIGMA como proyecto individual,
  pero es una condición del contrato, no una nota al margen.
- **Restricción a modelos multimodales para entidades domiciliadas en
  la Unión Europea** — no aplica a los pesos de texto puro que SIGMA usa,
  pero corresponde documentarlo porque la licencia sí lo distingue.
- **Acceptable Use Policy incorporada por referencia** — prohíbe usos
  específicos (militar, armas, actividades ilegales, entre otros) y
  exige aviso de atribución obligatorio: *"Llama 3.2 is licensed under
  the Llama 3.2 Community License, Copyright © Meta Platforms, Inc. All
  Rights Reserved."* en cualquier redistribución.

**Esto no bloquea el uso de SIGMA-FE** — el proyecto cumple todas las
condiciones sin esfuerzo adicional (uso individual, texto puro, sin
distribución comercial masiva) — pero es el único de los 4 modelos que
exige activamente demostrar cumplimiento de una política de uso, no solo
citar una licencia permisiva. Documentado así porque es precisamente el
tipo de matiz que `SR 26-02` (`ADR-021`) espera que una validación de
modelos de terceros distinga, no que homogenice.

## Alcance de uso dentro de SIGMA

Tareas de menor costo computacional dentro de Engineer Datos — nunca
output que se redistribuya fuera del pipeline sin el aviso de
atribución que la licencia exige si algún día se libera un artefacto
que lo incluya.

## Limitaciones conocidas

Modelo de 3B parámetros — capacidad de razonamiento limitada frente a
`mistral:7b`; SIGMA lo reserva para tareas donde la velocidad importa
más que la profundidad de razonamiento.

## Monitoreo continuo (SR 26-02, alineación voluntaria vía `ADR-021`)

Mismo estado que los otros dos — revisión manual al cambiar de versión.
**Prioridad más alta que los otros tres** para cuando se formalice el
mecanismo automatizado, precisamente por ser el único con condiciones
contractuales activas que verificar, no solo una licencia permisiva.
