# tests/test_data_ingestion.feature — 0001-data-ingestion v2.0.0
# SIGMA v1.5 · Eco MultiAgentes 4 Skills 2
# Sintaxis Gherkin estricta: una línea por step (gherkin-official)

# language: es

Característica: Carga de datos desde archivo fuente hacia raw_data
  Como Orquestador de SIGMA
  Quiero que data-ingestion cargue el archivo fuente con checksum e integridad
  Para que el resto del pipeline parta de datos trazables

  Contexto:
    Dado que el entorno tiene SIGMA_VARIANT configurado
    Y que PostgreSQL está disponible con la tabla "raw_data"

  @happy_path @hito1
  Escenario: Carga exitosa del corpus Tirendaz con checksum
    Dado que el archivo "tirendaz.csv" existe con 22500 filas y columna "text"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-ingestion con trace_id "wc-ing-001"
    Entonces se escriben 22500 registros en "raw_data"
    Y el output incluye un checksum_sha256 no nulo
    Y el output incluye run_id igual al run_id del estado del pipeline
    Y retorna DataIngestionOutput con status "success"

  @chunked
  Escenario: Archivo grande se procesa en más de un chunk
    Dado que el archivo "grande.csv" existe con 60000 filas y columna "text"
    Y que el tamaño de chunk configurado es 25000
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-ingestion con trace_id "wc-ing-002"
    Entonces el output indica chunks_processed mayor a 1
    Y se escriben 60000 registros en "raw_data"

  @error @schema_drift
  Escenario: Columna requerida ausente
    Dado que el archivo "malo.csv" existe con 100 filas sin columna "text"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-ingestion con trace_id "wc-ing-003"
    Entonces el skill lanza SchemaValidationError
    Y NO se escribe ninguna fila en "raw_data"

  @error @not_found
  Escenario: Archivo fuente no encontrado
    Dado que el archivo "inexistente.csv" no existe en el sistema
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-ingestion con trace_id "wc-ing-004"
    Entonces el skill lanza SourceNotFoundError
    Y NO se escribe ninguna fila en "raw_data"

  @error @empty
  Escenario: Archivo fuente vacío
    Dado que el archivo "vacio.csv" existe con 0 filas y columna "text"
    Y que SIGMA_VARIANT es "Full"
    Cuando el Orquestador invoca data-ingestion con trace_id "wc-ing-005"
    Entonces el skill lanza EmptySourceError
    Y NO se escribe ninguna fila en "raw_data"

  @dev_mode
  Escenario: Modo Dev con datos sintéticos
    Dado que SIGMA_VARIANT es "Dev"
    Cuando el Orquestador invoca data-ingestion con trace_id "wc-ing-006"
    Entonces el output indica dev_mode True
    Y el output tiene checksum_sha256 nulo
    Y retorna DataIngestionOutput con status success o success_with_warnings
