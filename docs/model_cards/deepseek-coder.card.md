---
model_id: deepseek-coder
provider: DeepSeek (vía Ollama, self-hosted)
license: DeepSeek License Agreement v1.0 (23 octubre 2023)
license_type: permisiva con atribución — permite uso comercial y redistribución
source_verified: https://ollama.com/library/deepseek-coder
verification_date: 2026-07
version_pinned: deepseek-coder:6.7b (según .env / Ollama Modelfile real)
sigma_scope: gia_ (generación asistida de código interno del ecosistema — no expuesto a usuarios finales, no genera output que llegue a un cliente)
---

## Procedencia

Modelo base entrenado desde cero por DeepSeek (87% código, 13% lenguaje
natural en inglés y chino, 2 billones de tokens). Servido localmente vía
Ollama — sin llamada a API externa, consistente con `SIGMA-FE` ($0,
self-hosted).

## Licencia — verificada, no asumida

DeepSeek License Agreement v1.0, texto real capturado directo de la
página de Ollama (no de un resumen de terceros). Otorga licencia de
copyright y de patente perpetua, mundial, no exclusiva, gratuita —
permite reproducir, mostrar públicamente, sublicenciar y distribuir el
modelo y sus derivados. **Uso comercial permitido.** No es OSI-approved
en sentido estricto (licencia propia de DeepSeek, no Apache/MIT), pero
sin restricciones de umbral de usuarios como Llama 3.2.

## Alcance de uso dentro de SIGMA

Uso interno de generación de código asistida (`gia_`, `ADR-014`) — nunca
output directo a un usuario final del pipeline. Este alcance declarado
es el que consta en `ADR-021`, no un uso genérico del modelo.

## Limitaciones conocidas

Modelo de código, no de lenguaje natural general — SIGMA no lo usa para
tareas de razonamiento fuera de generación/revisión de código.

## Monitoreo continuo (SR 26-02, alineación voluntaria vía `ADR-021`)

Pendiente de mecanismo automatizado — hoy, cualquier cambio de versión
del modelo se revisa manualmente antes de actualizar el pin en
`.env`/Modelfile. Candidato a formalizarse cuando exista Ag-DR real de
Engineer Modelos (Rollout 2) que registre qué versión de modelo generó
cada resultado.
