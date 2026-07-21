---
model_id: mistral
provider: Mistral AI (vía Ollama, self-hosted)
license: Apache License 2.0
license_type: totalmente abierta — sin restricciones de uso, incluyendo comercial
source_verified: https://ollama.com/library/mistral (y anuncio oficial mistral.ai/news/announcing-mistral-7b)
verification_date: 2026-07
version_pinned: mistral:7b (según .env / Ollama Modelfile real)
sigma_scope: razonamiento general de propósito amplio dentro del Director/Engineers, self-hosted
---

## Procedencia

Modelo de 7B parámetros publicado por Mistral AI, distribuido bajo
Apache 2.0 desde su lanzamiento — "puede usarse sin restricciones",
según la propia nota de lanzamiento de Mistral AI. Servido localmente
vía Ollama, sin llamada a API externa.

## Licencia — la más simple de las 4, verificada igual que las demás

Apache License 2.0, texto completo confirmado en la página real de
Ollama. Sin cláusulas de umbral de usuarios, sin política de uso
aceptable adicional impuesta por el proveedor del modelo — la licencia
más abierta de los tres modelos servidos vía Ollama.

## Alcance de uso dentro de SIGMA

Modelo de propósito general para razonamiento del Director y lógica de
los Engineers que no requiere especialización de código — mismo
principio de `AGENTS_CREATOR.md`: nunca se usa para inferencia sobre
datos sensibles sin pasar primero por K⊆X (`ADR-008`).

## Limitaciones conocidas

Ventana de contexto y capacidad razonadora menores que modelos de
frontera de pago — motivo explícito por el que `SIGMA-HE` existe como
variante, para cuando el caso de uso lo exija.

## Monitoreo continuo (SR 26-02, alineación voluntaria vía `ADR-021`)

Mismo estado que `deepseek-coder` — revisión manual al cambiar de
versión, formalización pendiente de Ag-DR real.
