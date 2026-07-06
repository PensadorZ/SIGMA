# tests/test_data_preprocessor.feature — 0003-data-preprocessor v2.0.0
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2 — fusión Opción C con config condicional
# Sintaxis Gherkin estricta: una línea por step

# language: es

Característica: Preprocesado con leakage, escalado real, y transformaciones condicionales
  Como Orquestador de SIGMA
  Quiero preprocesar datos con SMOTE/class_weight/PCA solo cuando aplica
  Para que el mismo skill sirva al pipeline Tirendaz y a futuros pipelines tipo Kaggle

  Contexto:
    Dado que el entorno tiene SIGMA_VARIANT configurado
    Y que cleaned_data está disponible con datos para el trace_id de la prueba

  @happy_path @hito1 @sin_target
  Escenario: Preprocesado estándar sin target_column — caso Tirendaz actual
    Dado que cleaned_data contiene 20 filas sin columna de target en metadata
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-001"
    Entonces el output indica target_column_detected como nulo
    Y el output indica num_smote_synthetic_rows igual a 0
    Y el output indica class_weights como nulo
    Y retorna status "success"

  @target_detection
  Escenario: Detección automática de target_column cuando existe
    Dado que cleaned_data contiene 20 filas con columna "sentiment_label" en metadata
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-002"
    Entonces el output indica target_column_detected igual a "sentiment_label"

  @smote @skipped
  Escenario: SMOTE activado pero sin target_column se omite sin error
    Dado que cleaned_data contiene 20 filas sin columna de target en metadata
    Y que apply_smote está activado en la configuración
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-003"
    Entonces el output tiene warnings con "smote_skipped_no_target_column"
    Y el output indica num_smote_synthetic_rows igual a 0
    Y retorna status success o success_with_warnings

  @smote @applied
  Escenario: SMOTE aplicado cuando hay target y desbalance suficiente
    Dado que cleaned_data contiene 30 filas con columna "sentiment_label" desbalanceada en metadata
    Y que apply_smote está activado en la configuración
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-004"
    Entonces el output indica num_smote_synthetic_rows mayor a 0
    Y el output tiene warnings con "smote_synthetic_rows_not_persisted"
    Y ninguna fila con clean_text sintético existe en processed_data

  @class_weight
  Escenario: class_weight calculado cuando hay target
    Dado que cleaned_data contiene 20 filas con columna "sentiment_label" en metadata
    Y que apply_class_weight está activado en la configuración
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-005"
    Entonces el output indica class_weights no nulo

  @pca @skipped
  Escenario: PCA omitido por features numéricas insuficientes
    Dado que cleaned_data contiene 20 filas sin columna de target en metadata
    Y que apply_pca está activado en la configuración
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-006"
    Entonces el output indica pca_applied como falso
    Y el output tiene warnings con "pca_skipped_insufficient_features"

  @leakage
  Escenario: Columna de leakage se excluye de las features
    Dado que cleaned_data contiene 20 filas con columna "future_engagement" en metadata
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-007"
    Entonces el output tiene warnings con "leakage_excluded"
    Y "future_engagement" no aparece en extra_numeric_features del output

  @error @empty
  Escenario: cleaned_data vacía
    Dado que cleaned_data no contiene ninguna fila
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-008"
    Entonces el skill lanza NoDataToProcessError

  @dev_mode
  Escenario: Modo Dev con datos sintéticos
    Dado que SIGMA_VARIANT es "Dev"
    Cuando el Orquestador invoca data-preprocessor con trace_id "wc-prep-009"
    Entonces el output indica dev_mode True
    Y retorna status success o success_with_warnings
