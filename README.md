# AXIGNAL

**Global Opportunity Intelligence**

AXIGNAL es una plataforma premium de observación económica y exploración multiactivo. Convierte señales globales en claims trazables, escenarios dinámicos y oportunidades consultables mediante una metodología epistemológica auditable.

- Marca comercial: **AXIGNAL**
- Dominio: **axignal.com**
- Repositorio técnico: `LowToHi/axignal`
- Goal ID: `AXIGNAL-GOAL-001`
- Estado: **Consolidated executable baseline candidate**
- Naturaleza: inteligencia e investigación; no ejecución, custodia ni asesoramiento personalizado

## Principio central

> Signals reveal change. Claims establish evidence. AXIGNAL maps opportunity.

## Contratos normativos

La fuente contractual del producto vive en [`docs/contracts`](docs/contracts/README.md). El mapa de ejecución vive en [`docs/roadmap`](docs/roadmap/README.md). Ninguna implementación puede presentarse como producción si incumple esos contratos, el Goal Lock o sus gates.

## Espina ejecutable

```text
apps/
├── web       # Investigation Shell y Navigator
├── landing   # superficie pública de conversión
└── api       # FastAPI, ResearchRuns y runtimes de propuesta/admisión

packages/
└── design-tokens

infra/
└── postgres  # PostgreSQL + PostGIS + pgvector + fronteras de autoridad
```

Servicios locales adicionales:

- Valkey para colas y estado efímero;
- Playwright para el workflow canónico de navegador;
- Docker Compose para integración desechable;
- CI independiente para contratos, API, aplicaciones y persistencia.

Inicio rápido y gates: [`docs/runbooks/local-development.md`](docs/runbooks/local-development.md).

## Vertical slice gobernado

```text
identidad autenticada
→ Navigator
→ ResearchRun persistente
→ fuente o documento admitido
→ Evidence Objects
→ Candidate Claims
→ proposal worker sin autoridad canónica
→ admission handoff durable
→ runtime determinista independiente
→ Claim Ledger append-only
→ dossier e InvestigationContext
```

Los modelos pueden proponer. Solo el runtime epistemológico independiente puede admitir un claim canónico.

## Superficies previstas

- **AXIGNAL Navigator** — conversación multilingüe para navegar, investigar y explicar claims.
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

El repositorio contiene una primera alpha vertical gobernada y reproducible. No constituye producción: UX validada, universo comercial inicial, identidad multiusuario, fuentes amplias, revisión humana, billing, observabilidad operativa, seguridad productiva, modelos predictivos y general availability permanecen bajo gates específicos.
