# AXIGNAL

**Global Opportunity Intelligence**

AXIGNAL es una plataforma premium de observación económica y exploración multiactivo. Convierte señales globales en claims trazables, escenarios dinámicos y oportunidades consultables mediante una metodología epistemológica auditable.

- Marca comercial: **AXIGNAL**
- Dominio: **axignal.com**
- Repositorio técnico: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`
- Estado: **Executable spine / Contract-first**
- Naturaleza: inteligencia e investigación; no ejecución, custodia ni asesoramiento personalizado

## Principio central

> Signals reveal change. Claims establish evidence. AXIGNAL maps opportunity.

## Contratos normativos

La fuente contractual del producto vive en [`docs/contracts`](docs/contracts/README.md). El mapa de ejecución vive en [`docs/roadmap`](docs/roadmap/README.md). Ninguna implementación puede presentarse como producción si incumple esos contratos o el Goal Lock.

## Espina ejecutable

```text
apps/
├── web       # Investigation Shell v0.2
├── landing   # sistema público de conversión, Pricing y FAQ
└── api       # FastAPI y contrato Navigator sintético

packages/
└── design-tokens

infra/
└── postgres  # PostgreSQL + PostGIS + pgvector
```

Servicios locales adicionales:

- Valkey para estado efímero y futuras colas;
- Playwright para el flujo Navigator → Graph → Evidence;
- Docker Compose para pruebas desechables;
- CI independiente para aplicaciones, API y extensiones de datos.

Inicio rápido y gates: [`docs/runbooks/local-development.md`](docs/runbooks/local-development.md).

## Superficies previstas

- **AXIGNAL Navigator** — conversación multilingüe para navegar, filtrar y explicar claims.
- **AXIGNAL Globe** — mapa mundial y capas de clima de oportunidad.
- **AXIGNAL Graph** — relaciones, transmisión, propiedad, cadenas y causalidad hipotética.
- **AXIGNAL Timeline** — reconstrucción histórica y comparación temporal.
- **AXIGNAL Claims** — claims, evidencia, contradicciones, vigencia y procedencia.
- **AXIGNAL Knowledge Tides** — señales agregadas de atención e intuición de usuarios.
- **AXIGNAL API** — acceso contractual a datos y productos derivados.

## Diseño seleccionado

Las referencias estructurales dark y light viven en [`design/references`](design/references/README.md). ADR-007 obliga a preservar Navigator, `AUTO / GLOBE / GRAPH / DUAL`, canvas dominante, oportunidades, Claim/Evidence Rail y Timeline.

## Regla de producto

La IA puede descubrir, extraer, clasificar, navegar y explicar. Solo el runtime epistemológico puede admitir un claim, promover una oportunidad o declarar un estado contractual.

La atención de usuarios puede priorizar una investigación. Nunca demuestra por sí misma que una oportunidad económica existe.

## Estado de madurez

El repositorio contiene ya una primera espina ejecutable con datos sintéticos. No constituye producción: buyer, pricing, universo inicial, fuentes reales, modelos predictivos, tokens finales y UX validada permanecen bajo gates comerciales, empíricos, jurídicos, de rendimiento y usabilidad.
