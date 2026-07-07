# SIGMA — Sistema Integrado para la Gestión Multiagente

> **SIGMA no es una respuesta. Es el sistema que aprende a responder.**

🇬🇧 [English version available here](README.en.md)

---

SIGMA es un ecosistema de agentes autónomos de código abierto para
analizar, diseñar, calcular y decidir, construido mediante una
metodología de desarrollo asistido por IA (*vibecoding*) y documentado
desde su arquitectura hasta la resolución real de incidentes en
producción.

Múltiples agentes especializados colaboran bajo una arquitectura de
orquestación central triangular — el patrón Director/Engineer de tres
orquestadores (ver ADR-016) — para abordar proyectos en Ingeniería de
Datos, Data Science, Análisis de Datos, Ingeniería General, Física,
Matemática y Axiometría.

## Por qué SIGMA es distinto

La mayoría de proyectos de agentes construyen primero una funcionalidad
vistosa y añaden gobernanza después, si acaso. SIGMA se construyó al
revés, deliberadamente: memoria epistémica, seguridad automática,
gestión de secretos y contención de alucinaciones (`K ⊆ X`) existieron
**antes** de que hubiera un solo dashboard que mostrar. Cada decisión
arquitectónica está respaldada por un Architecture Decision Record (ADR)
explícito — 16 hasta la fecha — no por convención tácita.

## Escalones de costo

SIGMA se adapta a cuatro niveles de presupuesto, del mismo stack
arquitectónico:

| Variante | Costo | Para quién |
|---|---|---|
| **SIGMA-FE** (Full Engineer) | $0 | Ingeniería propia, stack 100% autoalojado |
| **SIGMA-LE** (Low-Cost Engineer) | Bajo | Servicios premontados esenciales |
| **SIGMA-ME** (Medium-Cost Engineer) | ~50% pago | Equipos con presupuesto moderado |
| **SIGMA-HE** (High-Cost Engineer) | Alto | Empresas que requieren alto desempeño |

Cada variante puede además operar en submodo **Dev** (depuración) o
**Runtime** (producción con datos reales). Detalle completo en
[SIGMA_v1.7.md](SIGMA_v1.7.md).

## Empezar

```bash
sigma init mi-proyecto
cd mi-proyecto
cp .env.example .env
docker compose up -d
python -m sigma run pipelines/analisis_opinion_twitter.yaml
```

Guía completa, paso a paso, en [INSTALL.md](INSTALL.md).

## Documentación

| Documento | Qué encontrarás ahí |
|---|---|
| [SIGMA_v1.7.md](SIGMA_v1.7.md) | Plan Maestro completo — arquitectura, variantes, roadmap |
| [AGENTS_CREATOR.md](AGENTS_CREATOR.md) | Acta fundacional — contrato de todos los agentes |
| [docs/adr/](docs/adr/) | 16 Architecture Decision Records |
| [PIPELINES.md](PIPELINES.md) | Cómo crear y ejecutar pipelines propios |
| [INSTALL.md](INSTALL.md) | Instalación detallada, de cero a pipeline corriendo |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | Incidentes reales encontrados y su solución exacta |

## Estado del proyecto

Hito 1 completado: pipeline de 6 skills corriendo de extremo a extremo
contra datos reales, con 65/65 pruebas automatizadas pasando. Hito 2 en
diseño: orquestación jerárquica de tres niveles (Director/Engineer).

## Licencia

[MIT](LICENSE)
