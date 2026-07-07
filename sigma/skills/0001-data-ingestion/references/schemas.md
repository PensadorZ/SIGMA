# schemas.md — Skill 0001: data-ingestion

## DataIngestionOutput (documentado, no Pydantic — consistente con el
resto del proyecto donde el output vive como dict dentro de SkillResult)

| Campo | Tipo | Descripción |
|---|---|---|
| `num_records` | `int` | Filas cargadas hacia `raw_data` |
| `source_path` | `str` | Ruta del archivo fuente (o `"synthetic"` en Dev) |
| `checksum_sha256` | `str \| None` | Checksum del archivo fuente. `None` en modo Dev |
| `chunks_processed` | `int` | Número de chunks leídos. `0` en modo Dev |
| `run_id` | `str` | ID de nivel pipeline, igual al de `0000` |
| `trace_id` | `str` | ID de trazabilidad Langfuse |
| `dev_mode` | `bool` | `True` si corrió con datos sintéticos |

## Excepciones

```python
class SourceNotFoundError(Exception):
    """Archivo fuente inexistente o ilegible."""

class EmptySourceError(Exception):
    """Archivo fuente existe pero no contiene filas."""

class SchemaValidationError(Exception):
    """Columna mínima requerida ('text') ausente en el archivo fuente."""
```

## Columnas mínimas del archivo fuente

| Columna | Requerida | Descripción |
|---|---|---|
| `text` | Sí | Contenido del tweet/texto a procesar |
| `row_id` | No | Se genera automáticamente si falta (`row-{i}`) |

## Tabla de salida: `raw_data`

Ver `db/init_schema.sql` — sin cambios en esta fusión, `raw_data` ya
tenía todas las columnas necesarias.
