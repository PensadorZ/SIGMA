---
id: OUTPUT-REPORT
titulo: Reporte de resultados — Pruebas de generalización cross-domain
version: 1.0
estado: Activo
fecha: 2026-07-10
autor: Prof. Marx A. García Delgado
---

# Reporte de resultados — Pruebas de generalización cross-domain

Este documento explica, en lenguaje llano, qué muestran los tres
dashboards HTML generados durante las pruebas de generalización del
Hito 1, y sirve como guía para quien quiera reproducir estas pruebas
con sus propios datasets de Kaggle.

### Persistencia local vs. MinIO — según el submodo

| Submodo | Dónde queda el dashboard |
|---|---|
| `Dev` | Archivo local: `outputs/dashboards/{trace_id}/index.html` |
| `Full` | Solo en MinIO: `minio://dashboards/{trace_id}/index.html` — nunca se escribe en disco local. Descárgalo manualmente desde la consola web de MinIO (`http://localhost:9003`, bucket `dashboards`) si necesitas una copia local. |

Por esto, de las 6 corridas documentadas en este reporte, solo la
prueba rápida en modo Dev generó automáticamente una carpeta dentro de
`outputs/dashboards/` — las corridas 3 a 6 (todas en modo Full) fueron
descargadas manualmente desde MinIO y renombradas para este reporte.

---

## Navegación — dashboards HTML de todas las corridas

| # | Archivo | Dataset | Resultado |
|---|---|---|---|
| 1 | [dashboard_run1_failed.html](dashboard_run1_failed.html) | Tirendaz (Yasserh) | ❌ Falló — ver `TROUBLESHOOTING.md` |
| 2 | [dashboard_run2_failed.html](dashboard_run2_failed.html) | Tirendaz (Yasserh) | ❌ Falló — ver `TROUBLESHOOTING.md` |
| 3 | [dashboard_run3_ok.html](dashboard_run3_ok.html) | Tirendaz (Yasserh) | ✅ Éxito, pre-reestructuración `sigma/` |
| 4 | [dashboard_run4_ok.html](dashboard_run4_ok.html) | Tirendaz (Yasserh) | ✅ Éxito, post-reestructuración, `warnings=[]` |
| 5 | [dashboard_run5_imdb_ok.html](dashboard_run5_imdb_ok.html) | IMDb 50K Reviews | ✅ Éxito, `warnings=[]` — ver Test 2 abajo |
| 6 | [dashboard_run6_social_ok_warnings.html](dashboard_run6_social_ok_warnings.html) | Social Media 2026 | ✅ Éxito con advertencias — ver Test 3 abajo |

> **Nota:** si buscas `test_dashboard_fix.html`, ese archivo **no** es
> una corrida del pipeline — es la salida de la verificación puntual
> del fix de renderizado de `0011-viz-reporter` (ver
> `TROUBLESHOOTING.md`). Vive junto a su script en
> [`tests/test_dashboard_fix.html`](../tests/test_dashboard_fix.html),
> no en esta carpeta.

Los análisis detallados de las corridas 5 y 6 (las que prueban
generalización cross-domain) están en la Parte 1 de este documento. Las
corridas 1-4 documentan la evolución del Hito 1 sobre el dataset base
(dos fallos diagnosticados y corregidos, luego dos éxitos antes y
después de la reestructuración del código a `sigma/`).

**Dataset:** `ibrahimqasimi/imdb-50k-cleaned-movie-reviews` — 5,000
reseñas de películas (el nombre del dataset en Kaggle sugiere 50,000,
pero el archivo real contiene 5,000 filas — verificado con
`df.shape` tanto localmente como en el propio notebook de Kaggle),
dominio: texto largo (cientos de palabras por fila), completamente
distinto al de Twitter.

---

## Parte 1 — Las tres corridas, explicadas

### Test 1 — Tirendaz / Yasserh (baseline del Hito 1)

**Dataset:** `yasserh/twitter-tweets-sentiment-dataset` — 27,481 tweets
etiquetados, dominio: Twitter, texto corto.

**Resultado:** ✅ éxito completo, `warnings=[]` — ningún dato inusual
detectado.

**Qué muestra el dashboard:** distribución de sentimiento balanceada
entre las tres categorías (positivo, negativo, neutral), engagement por
fila calculado sin errores, e idiomas agrupados correctamente (mayoría
en inglés, con un grupo "otros" para idiomas minoritarios). Este es el
comportamiento de referencia contra el cual se comparan las otras dos
corridas.

---

### Test 2 — IMDb 50K Movie Reviews

**Dataset:** `ibrahimqasimi/imdb-50k-cleaned-movie-reviews` — 50,000
reseñas de películas, dominio: texto largo (cientos de palabras por
fila), completamente distinto al de Twitter.

**Resultado:** ✅ éxito completo, `warnings=[]`.

**Hallazgo real — el tiempo de inferencia escala con la longitud del
texto.** El skill `0008-sentiment-analyzer` tardó **18 minutos 34
segundos** procesando las reseñas de IMDb, frente a **16 segundos**
procesando los tweets de Tirendaz en la corrida base — aproximadamente
**70 veces más lento**. Esto no es un error: refleja el costo real de
RoBERTa procesando texto largo token por token, frente a tweets de
~280 caracteres. **Implicación práctica:** quien aplique SIGMA a
dominios de texto largo (reseñas, artículos, transcripciones) debe
esperar tiempos de `0008` proporcionalmente mayores, y podría necesitar
ajustar `batch_size` en `defaults.yaml`.

**Qué demuestra:** que el pipeline generaliza correctamente a un dominio
de texto completamente distinto del de origen, sin cambios de código —
solo ajustando la variable `SIGMA_INGESTION_REQUIRED_COLUMN` (ver Parte
2 de este documento).

---

### Test 3 — Social Media Sentiment 2026

**Dataset:** `algozee/social-media` — 2,200 filas combinando Twitter,
Reddit y YouTube.

**Resultado:** ✅ éxito con advertencias — el pipeline se pausó una vez
para aprobación humana (HITL), reanudado manualmente por la
desactivación temporal del bot de Zulip (ver "Limitaciones conocidas"
en el README).

**Hallazgo real — el dataset original solo contiene 10 textos únicos.**
Verificado directamente contra el CSV: de 2,200 filas, únicamente 10
valores distintos de `post_text` existen, cada uno repetido entre 199 y
243 veces. `0002-data-cleanser` detectó correctamente esta duplicación
masiva y lo reportó (`warnings: ['high_duplicate_rate']`) en vez de
procesar datos redundantes en silencio — comportamiento correcto, no un
fallo del deduplicador.

**Hallazgo real — el disparador automático de HITL funcionó como está
diseñado.** Con solo 10 filas finales tras la deduplicación, el 40% de
las clasificaciones resultaron `UNCLEAR` (por encima del umbral del
30% que define ADR-004), y el pipeline se pausó automáticamente
pidiendo confirmación humana antes de continuar — exactamente el
comportamiento que ADR-004 y ADR-008 (K⊆X) exigen ante incertidumbre alta.

**Qué demuestra:** esta corrida es menos útil como evidencia de
"generalización de dominio" (por la duplicación extrema del dataset
original) y más útil como evidencia de que **el mecanismo de calidad y
aprobación humana funciona correctamente ante datos ambiguos**. Para una
prueba de generalización más fuerte en redes sociales, se necesitaría un
dataset con texto verdaderamente único por fila.

---

## Resumen comparativo

| Dataset | Dominio | Resultado | Evidencia que aporta |
|---|---|---|---|
| Tirendaz (Yasserh) | Twitter, texto corto | ✅ success, warnings=[] | Comportamiento base verificado del Hito 1 |
| IMDb 50K | Reseñas de cine, texto largo | ✅ success, warnings=[] | Generalización real de dominio; costo de inferencia escala con longitud de texto |
| Social Media 2026 | Multi-plataforma | ✅ success_with_warnings | Funcionamiento correcto del disparador HITL y de la detección de duplicados; no aporta evidencia de generalización por la baja unicidad del dataset original |

---

## Parte 2 — Cómo reproducir estas pruebas con tu propio dataset de Kaggle

### Paso 1 — Crear cuenta y obtener el token de API

1. Crea una cuenta gratuita en [kaggle.com](https://www.kaggle.com).
2. Ve a tu perfil → **Settings** → sección **API** → **Create New Token**.
3. Esto descarga `kaggle.json` con tus credenciales.
4. Colócalo en `C:\Users\<tu_usuario>\.kaggle\kaggle.json` (Windows).

### Paso 2 — Buscar datasets desde la terminal

```cmd
kaggle datasets list -s "tu tema de interés" --sort-by hottest
```

Prioriza datasets con `usabilityRating` cercano a 1.0 — es la propia
métrica de calidad de Kaggle.

### Paso 3 — Descargar y verificar estructura antes de correr el pipeline

```cmd
kaggle datasets download <usuario>/<slug> -p data\raw\test_nombre --unzip
python -c "import pandas as pd; df = pd.read_csv('data/raw/test_nombre/archivo.csv'); print(df.columns.tolist())"
```

**Nunca asumas el nombre de columna** — verifícalo siempre antes de
correr el pipeline completo, tal como se hizo en este reporte.

### Paso 4 — Ajustar el nombre de columna de texto (sin tocar código)

```cmd
set SIGMA_INGESTION_REQUIRED_COLUMN=nombre_real_de_tu_columna
python orchestrator.py --variant Full --data-path ./data/raw/test_nombre/archivo.csv
```

---

## Parte 3 — Datasets candidatos para futuras pruebas (catálogo revisado)

Obtenidos mediante `kaggle datasets list` real (no listados de memoria),
en dos búsquedas: `"twitter sentiment"` y `"sentiment analysis nlp"`,
ambas ordenadas por popularidad (`--sort-by hottest`).

| Dataset | Dominio | Tamaño | usabilityRating | Estado |
|---|---|---|---|---|
| `yasserh/twitter-tweets-sentiment-dataset` | Twitter | 1.3 MB | 1.0 | ✅ Revisado y usado (baseline) |
| `ibrahimqasimi/imdb-50k-cleaned-movie-reviews` | Reseñas de cine | 3.7 MB | 1.0 | ✅ Revisado y probado |
| `algozee/social-media` | Multi-plataforma | 112 KB | 1.0 | ✅ Revisado y probado |
| `columbine/imdb-dataset-sentiment-analysis-in-csv-format` | Reseñas de cine | 26.9 MB | 1.0 | ⬜ Candidato — variante más grande de IMDb, útil para prueba de volumen |
| `abdallahwagih/emotion-dataset` | Emociones (no solo polaridad) | 218 KB | 1.0 | ⬜ Candidato — dominio distinto: clasificación de emociones, no sentimiento binario/ternario |
| `niraliivaghani/flipkart-product-customer-reviews-dataset` | Reseñas de producto (e-commerce) | 3.97 MB | 1.0 | ⬜ Candidato — dominio de e-commerce, no probado aún |
| `harshalhonde/starbucks-reviews-dataset` | Reseñas de servicio | 173 KB | 1.0 | ⬜ Candidato — dominio de servicio al cliente |
| `arunavakrchakraborty/covid19-twitter-dataset` | Twitter, tema específico | 51 MB | 1.0 | ⬜ Candidato — mismo dominio que Tirendaz, pero temática distinta y volumen mucho mayor |
| `kazanova/sentiment140` | Twitter | 84.9 MB | 0.88 | ⬜ Candidato — el más popular históricamente (275K descargas), útil para prueba de escala |
| `hbaflast/french-twitter-sentiment-analysis` | Twitter, francés | 50.7 MB | 1.0 | ⬜ Candidato — prueba de generalización de idioma, no solo de dominio |

**Descartados de esta ronda y por qué:** `saurabhshahane/twitter-sentiment-dataset`,
`crowdflower/twitter-airline-sentiment`, `arkhoshghalb/twitter-sentiment-analysis-hatred-speech`
y otros datasets de Twitter repiten el mismo dominio que Tirendaz sin
aportar prueba de generalización nueva. `dunyajasim/twitter-dataset-for-sentiment-analysis`
(210 MB) se descartó por tamaño desproporcionado para una prueba rápida.
