# Model Cards — SIGMA

Carpeta: `docs/model_cards/`

Registro de procedencia y licencia de cada modelo de terceros que SIGMA
usa hoy. Cierra parcialmente el vacío documentado en `ADR-021` §2.2
("validación de modelos de terceros"). Formato Yammtler (YAML +
Markdown), mismo patrón que Identidad (`ADR-019`) — redactado una vez
por un humano, se actualiza cuando cambia la versión del modelo, no en
cada corrida.

| Modelo | Proveedor | Licencia | Estado |
|---|---|---|---|
| `deepseek-coder.card.md` | DeepSeek (Ollama) | DeepSeek License v1.0 — permisiva, uso comercial permitido | Verificado |
| `mistral.card.md` | Mistral AI (Ollama) | Apache 2.0 — totalmente abierta | Verificado |
| `llama3.2.card.md` | Meta (Ollama) | Llama 3.2 Community License — **restricciones reales, ver card** | Verificado — prioridad de seguimiento |
| `roberta-sentiment.card.md` | CardiffNLP (Hugging Face) | CC BY 4.0 | Verificado — falta fijar hash de commit exacto |

## Lo que esto NO resuelve todavía

- No hay mecanismo automatizado de monitoreo continuo de fitness de
  estos modelos (el "ongoing monitoring" completo de SR 26-02) — hoy es
  revisión manual al cambiar de versión.
- El hash de commit exacto de `roberta-sentiment` no está registrado.

Ambos quedan anotados en `ADR-021` como vacío parcialmente cerrado, no
cerrado del todo — no se declara más de lo que estos 4 archivos
verifican.
