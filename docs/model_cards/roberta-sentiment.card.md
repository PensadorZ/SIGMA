---
model_id: cardiffnlp/twitter-roberta-base-sentiment-latest
provider: CardiffNLP (vía Hugging Face, self-hosted, descarga local)
license: CC BY 4.0
license_type: abierta con atribución
source_verified: https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest (campo License del model card)
verification_date: 2026-07
version_pinned: revisión `main` al momento de la primera descarga en Hito 1 (hash de commit pendiente de registrar — ver nota abajo)
sigma_scope: '0008-sentiment-analyzer, único uso del modelo dentro de SIGMA'
---

## Procedencia

RoBERTa-base entrenado sobre tweets (paper de referencia:
arXiv:2202.03829), publicado por el grupo CardiffNLP. Descargado una
vez y servido localmente vía `transformers` — no hay llamada a API de
Hugging Face en tiempo de ejecución del pipeline.

## Licencia — verificada, la más simple de citar de las 4

CC BY 4.0, confirmado directamente en el campo "License" del model card
de Hugging Face. Requiere atribución al reutilizar o redistribuir —
condición ya cumplida por el propio uso académico/de portafolio del
proyecto y por citar el paper de referencia, como ya hace el resto de
la documentación de SIGMA.

## Alcance de uso dentro de SIGMA

Único consumidor: `0008-sentiment-analyzer`. No se usa para ninguna otra
tarea ni se expone como servicio independiente.

## Limitaciones conocidas — ya documentadas en el proyecto, no nuevas aquí

Modelo entrenado sobre tweets en inglés predominantemente — la
generalización cross-domain (IMDb 50K, dataset de redes sociales) ya
está documentada como hallazgo real en el propio proyecto (~70x más
lento en texto largo, detección automática del gate HITL en datos de
baja variedad).

## Monitoreo continuo (SR 26-02, alineación voluntaria vía `ADR-021`)

**Hueco real, distinto a los otros tres:** a diferencia de los modelos
Ollama (con versión pineada explícita en `.env`), esta card no tiene
todavía el hash de commit exacto de Hugging Face registrado — se
descargó una vez durante Hito 1 sin fijar versión de forma explícita.
Corregirlo (registrar el commit hash real del checkpoint usado) es más
urgente que en los otros tres, porque hoy no hay forma de confirmar con
certeza qué revisión exacta está corriendo en producción.
