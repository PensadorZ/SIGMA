# schemas.md — Skill 0003: data-preprocessor

## Output (dentro de SkillResult.output)

| Campo | Tipo | Descripción |
|---|---|---|
| `num_processed` | `int` | Filas escritas en `processed_data` |
| `lang_distribution` | `dict` | Conteo por idioma detectado |
| `target_column_detected` | `str \| None` | Nombre de la columna target encontrada, o `None` |
| `extra_numeric_features` | `list[str]` | Columnas numéricas adicionales encontradas en metadata |
| `pca_applied` | `bool` | Si PCA se aplicó realmente |
| `pca_components_used` | `int` | Número de componentes PCA generados (0 si no se aplicó) |
| `class_weights` | `dict \| None` | Pesos por clase, solo si `apply_class_weight=true` y hay target |
| `num_smote_synthetic_rows` | `int` | Filas sintéticas generadas por SMOTE (nunca persistidas) |
| `class_distribution_before` | `dict \| None` | Distribución de clases antes de SMOTE |
| `class_distribution_after` | `dict \| None` | Distribución de clases después de SMOTE (incluye sintéticas) |
| `run_id` | `str` | ID de nivel pipeline |
| `trace_id` | `str` | ID de trazabilidad |
| `dev_mode` | `bool` | Modo Dev activo |

## Excepciones

```python
class NoDataToProcessError(Exception):
    """cleaned_data vacía, o todas las filas quedaron vacías tras limpieza previa."""
```

## Tabla de salida: `processed_data`

Sin cambios de schema respecto a v1.0.0 — la columna `features` (JSONB,
ya existente) acomoda `scaled_*` y `pca_*` sin necesitar DDL nuevo.

```json
{
  "scaled_engagement_score": 0.42,
  "scaled__extra_likes": 1.15,
  "pca": [0.31, -0.08]
}
```

## Warnings posibles

| Warning | Significado |
|---|---|
| `leakage_excluded:[...]` | Columnas de metadata excluidas por configuración |
| `smote_skipped_no_target_column` | `apply_smote=true` pero no se detectó target |
| `smote_skipped_ratio_below_threshold:X<=Y` | Desbalance insuficiente para justificar SMOTE |
| `smote_skipped_imblearn_not_installed` | Dependencia `imbalanced-learn` ausente |
| `smote_skipped_minority_too_small:X<2` | La clase minoritaria tiene menos de 2 muestras — SMOTE no puede interpolar |
| `smote_synthetic_rows_not_persisted:...` | SMOTE se aplicó, pero ver SKILL.md sección 3 |
| `class_weight_skipped_no_target_column` | `apply_class_weight=true` pero no se detectó target |
| `pca_skipped_insufficient_features:X<Y` | Menos features numéricas que el mínimo configurado |
| `high_undetermined_language_rate` | >30% de filas con idioma `und` |
| `synthetic_data` | Modo Dev |
