---
id: ADR-010
titulo: Directiva de Remediación de Secretos — Configuración 12-Factor
version: 1.4
estado: Aceptado
fecha-original: 2026-06
fecha-revision: 2026-06
supersede: ADR-010 v1.3
referencias-minimas: ADR-004, ADR-005, ADR-006
aprobado-por: Prof. Marx A. García Delgado
---

# ADR-010: Directiva de Remediación de Secretos — Configuración 12-Factor

## Resumen ejecutivo de cambios v1.4

Se amplía la sección de Contexto para explicar primero que este ADR es
el fundamento del que dependen ADR-004, ADR-005 y ADR-006 para su propia
gestión de secretos — antes de entrar al detalle del Principio de
Inyección Cero.

## Resumen ejecutivo de cambios v1.3

Se añade Fig. 1 con el flujo de los cuatro pasos del protocolo. Se añade
Tab. 1 con los tipos de secretos y su mecanismo de gestión. Se incorpora el
histórico de versiones.

---

## Contexto

La Directiva de Remediación de Secretos es el fundamento sobre el que se
apoyan varios otros mecanismos de gobernanza de SIGMA: la semilla TOTP
del Human-in-the-Loop (ADR-004), la configuración del Policy Server
(ADR-005), y la garantía del ContextResolver de nunca registrar un valor
resuelto en Langfuse (ADR-006) — todos asumen que existe una forma
disciplinada y única de manejar credenciales, y este ADR es esa forma.
Sin esta directiva, cada uno de esos mecanismos tendría que resolver el
problema de gestión de secretos por su cuenta, de forma inconsistente.

Las credenciales hardcodeadas representan el vector de ataque más
frecuente y evitable. En SIGMA el riesgo es especialmente alto porque el
repositorio puede ser público, los LLMs pueden incluir credenciales en
sus outputs, y los prompts que se loguean pueden exponer credenciales si
están embebidas.

---

## Decisión

**Principio de Inyección Cero:** queda estrictamente prohibido escribir
strings literales de credenciales en cualquier archivo del repositorio.

### Fig. 1 — Los cuatro pasos del protocolo de secretos

```
PASO 1: Crear archivo .env local
─────────────────────────────────
Operador crea .env con valores reales.
Este archivo NUNCA entra al repositorio.

PASO 2: Proteger el repositorio
─────────────────────────────────
.gitignore incluye:
  .env
  .env.local
  .env.*.local
  *.totp_seed  ← semilla TOTP cifrada

PASO 3: Plantilla pública .env.example
─────────────────────────────────
Mismas claves que .env pero con valores vacíos o descriptivos.
SÍ se versiona. Documenta las variables requeridas.
Ejemplo:
  GEMINI_API_KEY=tu_api_key_de_google_ai_studio
  DB_PASSWORD=tu_contrasena_aqui
  TOTP_SEED_PATH=/ruta/al/archivo/.sigma_totp.enc

PASO 4: Función get_required_env() en todo el código
─────────────────────────────────
def get_required_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Variable '{key}' no definida. "
            f"Ver .env.example para la lista completa."
        )
    return value
```

### Tab. 1 — Tipos de secretos y su mecanismo de gestión

| Tipo de secreto | Mecanismo | ¿En logs/Langfuse? |
|---|---|---|
| Claves de API (`GEMINI_API_KEY`) | `get_required_env()` en código Python | **Nunca** |
| Contraseñas de BD (`DB_PASSWORD`) | `get_required_env()` en código Python | **Nunca** |
| Tokens de Langfuse | `get_required_env()` en código Python | **Nunca** |
| Token del Approval Endpoint | `get_required_env()` en código Python | **Nunca** |
| Semilla TOTP cifrada | Archivo local cifrado con Fernet; ruta como placeholder en `.env.example` | **Nunca** el valor; sí la ruta |
| Token de MinIO | `get_required_env()` en código Python | **Nunca** |

### Semilla TOTP cifrada

La semilla TOTP para el MFA del Approval Endpoint se genera una vez con un
script de setup, se cifra con la contraseña del operador mediante Fernet, y
se almacena en un archivo local cubierto por `.gitignore`. El Approval
Endpoint descifra la semilla en memoria para validar el código TOTP. Sin
dependencias de servidores externos.

### Protocolo de rotación sin interrupción

La rotación de secretos solo se realiza entre ejecuciones. Un script de
verificación consulta el estado en Redis para confirmar que no hay pipelines
activos antes de proceder. Los servicios se reinician en el orden especificado
en INSTALL.md.

---

## Consecuencias positivas

- El repositorio puede ser público sin riesgo de exponer credenciales.
- El `fail-fast` hace el error explícito al inicio del pipeline, no a mitad.
- El `.env.example` documenta automáticamente todas las variables requeridas.

## Consecuencias negativas

- Requiere disciplina de equipo: la única forma de introducir una credencial
  hardcodeada es ignorar deliberadamente el protocolo.
- Si el `.env` está mal configurado, el sistema no arranca (comportamiento
  deseado, pero puede ser frustrante en las primeras configuraciones).

## Alternativas consideradas

| Alternativa | Por qué se descartó |
|---|---|
| Credenciales hardcodeadas con comentario "cambiar en prod" | Riesgo de olvido; quedan en historial Git |
| Archivo de configuración versionado por entorno | Las credenciales de prod quedan en el repositorio |
| Solo variables de entorno del sistema sin `.env` | Difícil de gestionar en desarrollo local |

---

## Histórico de versiones

**Cambios en v1.2:**
- **a.1.2** Se añadió la semilla TOTP cifrada como tipo de secreto
  gestionado por este ADR con instrucciones de generación y almacenamiento.
- **b.1.2** Se añadió el protocolo de rotación de secretos sin interrupción
  de ejecuciones en curso.

**Cambios en v1.3:**
- **a** Se añadió Fig. 1 con el flujo visual de los cuatro pasos del
  protocolo.
- **b** Se añadió Tab. 1 con los tipos de secretos, su mecanismo de gestión
  y sus restricciones de exposición.
