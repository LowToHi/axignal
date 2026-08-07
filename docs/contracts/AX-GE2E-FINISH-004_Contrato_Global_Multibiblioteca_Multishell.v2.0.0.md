# AXIGNAL — Contrato canónico de cierre E2E global, multibiblioteca y de dos shells

| Campo | Valor |
|---|---|
| **Contract ID** | `AX-GE2E-FINISH-004` |
| **Versión** | `2.0.0` |
| **Fecha** | `2026-08-07` |
| **Estado** | `HUMAN_SCOPE_DECISION_APPROVED / READY_FOR_REPOSITORY_INTEGRATION / NO_PUBLIC_LAUNCH` |
| **Goal ID** | `AXIGNAL-GOAL-001` |
| **Autoridad humana** | Rafael López |
| **Repositorio** | `LowToHi/axignal` |
| **Rama de progreso reconocida** | `agent/axignal-local-finalization` |
| **Baseline de ingeniería auditado** | `b2ff4034416892d66385173d9aacd27bce9f055b` — local y remoto coincidentes |
| **Categoría normativa** | `Global Opportunity Intelligence, Opportunity Operations & Public Employment` |
| **Producto gobernado** | AXIGNAL Core + F01–F07 + O01–O09 + workspaces + exactamente 2 shells sobre un núcleo compartido |
| **Número contractual de shells** | `2` — cardinalidad cerrada; cualquier ampliación exige enmienda humana versionada |
| **Shell 1 — principal** | `AXIGNAL_OPPORTUNITY_INTELLIGENCE` — F01–F07 + O01–O09 + workspaces empresariales; `PRIMARY_PRODUCT_SHELL` |
| **Shell 2 — adicional** | `AXIGNAL_PUBLIC_EMPLOYMENT` — oposiciones, procesos selectivos y empleo público; `ARCHITECTURAL_PROOF_REQUIRED` |
| **No son shells** | países, jurisdicciones, idiomas, fuentes, bibliotecas, workspaces ni `O01 Procurement` |
| **Resultado contractual** | Producto global multibiblioteca acabado E2E, desplegable, operable, cobrable y auditable con exactamente dos shells sobre un único núcleo; cualquier tercer shell exige enmienda humana |
| **No autoriza** | lanzamiento público, facturación live general, merge automático, administración de GitHub ni despliegue sin mandato separado |

---

# 0. Decisión ejecutiva vinculante

La autoridad humana revoca la reducción de alcance que definía AXIGNAL terminado como:

```text
O01 Procurement
+ TED
+ fundaciones estrictamente necesarias
```

La definición canónica vuelve a ser:

```text
AXIGNAL acabado
=
AXIGNAL Core
+ F01–F07
+ O01–O09
+ Opportunity Operations
+ workspaces especializados
+ inteligencia cross-library
+ producto comercial y operación de producción
+ arquitectura de exactamente dos shells demostrada
```

## 0.1 Decisión canónica de shells

La plataforma tendrá exactamente dos shells contractuales:

```text
SHELL_01
ID: AXIGNAL_OPPORTUNITY_INTELLIGENCE
DISPLAY_NAME: AXIGNAL Opportunity Intelligence
Ámbito: AXIGNAL Core + F01–F07 + O01–O09 + workspaces especializados
Usuarios: empresas, equipos, organizaciones, consultoras y unidades de inteligencia
Cobertura: global y configurable por jurisdicción
Estado contractual: PRIMARY_PRODUCT_SHELL

SHELL_02
ID: AXIGNAL_PUBLIC_EMPLOYMENT
DISPLAY_NAME: AXIGNAL Public Employment
Ámbito: empleo público, oposiciones, concurso, concurso-oposición, bolsas y procesos selectivos
Usuarios: candidatos y, en futuras ampliaciones autorizadas, preparadores o academias
Cobertura: configurable por jurisdicción
Estado contractual: ARCHITECTURAL_PROOF_REQUIRED
```

Reglas vinculantes:

1. `O01 Public Procurement` es una biblioteca del Shell 1, no un shell.
2. `Bid Workspace` es el workspace especializado de O01, no un producto separado.
3. Ningún país, jurisdicción, idioma, fuente o portal constituye un shell.
4. Ninguna biblioteca F01–F07 u O01–O09 constituye un shell por sí sola.
5. No se creará `AXIGNAL_PROCUREMENT`, `AXIGNAL_SPAIN`, `AXIGNAL_FRANCE` ni identificadores equivalentes como shells.
6. El `Shell Registry` deberá contener exactamente los dos IDs canónicos anteriores.
7. Un tercer shell sólo podrá existir mediante una nueva decisión humana, enmienda contractual versionada, análisis de no-fork y actualización explícita de la cardinalidad.

La motivación arquitectónica es preservar una sola experiencia empresarial cross-library en el Shell 1 y separar únicamente el dominio de empleo público porque cambian de forma material sus usuarios, objetivos, vocabulario, navegación, permisos, estados, acciones, workspaces y obligaciones legales.

TED queda reconocido como:

```text
primera fuente real implementada
→ dentro de O01 Procurement
→ dentro de `AXIGNAL_OPPORTUNITY_INTELLIGENCE`
```

TED no es:

```text
la identidad de AXIGNAL
el único universo del producto
el límite del E2E
la condición suficiente de finalización
```

La decisión no invalida el trabajo ya realizado. La rama `agent/axignal-local-finalization` constituye un baseline de progreso de ingeniería para el Research Spine y la primera fuente de O01. Ese progreso deberá preservarse, auditarse y remapearse al presente contrato sin repetir trabajo ni declarar como probado aquello que no tenga evidencia reproducible.

---

# 1. Autoridad, supersession y conservación del historial

## 1.1 Jerarquía de autoridad

```text
decisión humana explícita de 2026-08-07
→ AXIGNAL-GOAL-001
→ este contrato AX-GE2E-FINISH-004
→ contratos maestros globales preservados
→ ADR aceptados
→ ledger único
→ tareas tipadas
→ implementación
→ evidencia exact-head
```

Una capa inferior no puede reducir, reinterpretar o diferir silenciosamente una obligación superior.

## 1.2 Documentos superseded operativamente

Este contrato sustituye como autoridad de ejecución activa:

- `AX-GE2E-FINISH-003` versión `1.0.0`;
- cualquier cláusula que permita declarar AXIGNAL acabado con O01/TED como único universo;
- cualquier dependencia que bloquee WP2–WP6 completos por una única aprobación legal de TED;
- cualquier salida final limitada a `AXIGNAL_B2G_V1_E2E_COMPLETE` cuando se utilice como sinónimo de AXIGNAL completo.

Los documentos superseded se conservan como historial de auditoría y no se borran ni reescriben retroactivamente.

## 1.3 Cláusulas preservadas sin reducción

Se preservan:

- separación entre hechos, inferencias, cálculos, predicciones, contradicciones y desconocidos;
- Evidence Objects con procedencia, derechos, temporalidad y anclaje;
- Candidate Claims sin autoridad canónica;
- admisión determinista independiente del modelo;
- Claim Ledger append-only;
- autoridad humana para decisiones materiales;
- tenant isolation y autorización server-side;
- passkey-first, sesiones revocables y step-up cuando proceda;
- retención, exportación, eliminación, legal hold y auditoría;
- source rights, kill switch, quarantine y rollback independientes;
- modelos en modo proposal-only;
- prohibición de firma, presentación, pago, aprobación o comunicación externa autónoma no autorizada;
- WCAG, multilingüe, seguridad, privacidad, observabilidad y recuperación;
- Stripe y entitlements gobernados por servidor;
- evidencia exact-head para cierres y candidatos de release;
- prohibición de claims de cobertura no demostrada.

## 1.4 Regla de no pérdida de progreso

Ninguna ampliación contractual obliga a rehacer una capacidad que cumpla simultáneamente:

1. implementación real;
2. contrato compatible;
3. pruebas reproducibles;
4. evidencia ligada a commit;
5. ausencia de regresión;
6. compatibilidad con la arquitectura global.

Las capacidades heredadas podrán marcarse:

```text
INHERITED_ENGINEERING_PASS
```

pero sólo alcanzarán:

```text
CANONICAL_ACCEPTED
```

tras auditoría exact-head e integración en la línea canónica.

---

# 2. Goal Lock y definición de producto acabado

## 2.1 Definición canónica

> **AXIGNAL es una plataforma global de inteligencia y operaciones de oportunidad que convierte señales y registros fragmentados en evidencia verificable, investigaciones persistentes y workspaces donde equipos humanos pueden decidir y actuar.**

## 2.2 Cadena de valor no reducible

```text
fuente admitida
→ adquisición
→ normalización
→ Evidence Object
→ Candidate Claim
→ admisión determinista
→ InvestigationContext
→ Opportunity
→ Pursuit
→ Workspace especializado
→ decisión humana
→ acción o handoff oficial
→ Outcome
→ Learning
```

AXIGNAL no está acabado si termina en:

- una alerta;
- un resultado de búsqueda;
- un resumen;
- un chat;
- un dossier sin operación;
- una pantalla sin persistencia;
- una API sin journey;
- un workspace con controles decorativos;
- una demo basada en fixtures presentada como producto real.

## 2.3 Qué significa “todas las bibliotecas”

“Tener todas las bibliotecas implementadas” no significa ingerir toda fuente existente en el planeta.

Significa que cada biblioteca F01–F07 y O01–O09 dispone de:

1. contrato de dominio versionado;
2. ontología y schemas;
3. Source Registry y rights record;
4. al menos una fuente oficial real técnicamente integrada y jurídicamente resuelta;
5. normalización reproducible;
6. Evidence Objects y Candidate Claims;
7. admisión determinista;
8. lifecycle y correcciones;
9. observabilidad y quality profile;
10. kill switch, quarantine y rollback;
11. disclosure de cobertura y límites;
12. entitlement;
13. E2E real;
14. workspace operativo en O01–O09;
15. Outcome y Learning.

## 2.4 Estados de completitud

```text
ARCHITECTURE_READY
SOURCE_PROBED
SOURCE_ADMITTED
ENGINEERING_PASS
PRODUCT_ACCEPTED
COMMERCIAL_READY
CANONICAL_ACCEPTED
```

Una biblioteca sólo cuenta como terminada para este contrato cuando alcanza `CANONICAL_ACCEPTED`.

## 2.5 Claims globales

AXIGNAL sólo podrá utilizar públicamente “global” como cobertura de producto cuando:

- F01–F07 estén aceptadas;
- O01–O09 estén aceptadas;
- exista cobertura admitida en las regiones declaradas;
- la UI muestre cobertura, periodos y gaps;
- no se use una fuente europea como sustituto de cobertura mundial;
- el multilingüe funcione semánticamente;
- jurisdicciones, monedas, fechas y taxonomías sean nativas;
- exista un E2E multinacional por biblioteca cuando el claim sea multinacional;
- las fuentes suspendidas o rechazadas no contribuyan a claims.

---

# 3. Estado base reconocido a 2026-08-07

## 3.1 Baseline de referencia

```text
base declarada        main@7c551728c7d750ee35b3607a3939df493f697592
rama de progreso      agent/axignal-local-finalization
head declarado        b2ff403
estado remoto         push declarado, pendiente de verificación independiente
```

El agente deberá sustituir `b2ff403` por el SHA completo de 40 caracteres mediante:

```bash
git rev-parse HEAD
git ls-remote origin refs/heads/agent/axignal-local-finalization
```

## 3.2 Evidencia heredada reconocida provisionalmente

Las siguientes capacidades se reconocen como `INHERITED_ENGINEERING_PASS`, sujetas a auditoría independiente:

- signup passwordless y WebAuthn real;
- sesión AAL2;
- Navigator → ResearchRun persistente;
- redirect canónico y polling;
- worker lease, heartbeat, release y crash recovery;
- PostgreSQL y Valkey locales reales;
- recuperación TED live;
- normalización de notices;
- Evidence Objects;
- Candidate Claims;
- admisión determinista;
- Claim Ledger;
- InvestigationContext;
- AXENT persistente y gobernada;
- restart persistence;
- cross-tenant isolation;
- legal hold y purga gobernada;
- build de producción;
- suites locales declaradas verdes.

## 3.3 Mapeo heredado de WP1

```text
WP1-T01  SOURCE_ADMISSION_PENDING / HUMAN_LEGAL_PRIVACY
WP1-T02  INHERITED_ENGINEERING_PASS
WP1-T03  INHERITED_ENGINEERING_PASS
WP1-T04  INHERITED_ENGINEERING_PASS
WP1-T05  INHERITED_ENGINEERING_PASS
WP1-T06  INHERITED_ENGINEERING_PASS
WP1-T07  INHERITED_ENGINEERING_PASS
WP1-T08  INHERITED_ENGINEERING_PASS
WP1-T09  INHERITED_ENGINEERING_PASS
WP1-T10  INHERITED_ENGINEERING_PASS
```

## 3.4 Regla sobre el blocker legal de TED

La aprobación Legal/Privacy de TED:

- bloquea `SOURCE_ADMITTED` y `COMMERCIAL_READY` para esa fuente;
- puede bloquear claims derivados de TED en entornos comerciales;
- no bloquea el desarrollo del Core;
- no bloquea F01–F07;
- no bloquea O02–O09;
- no bloquea el Workspace Factory;
- no bloquea la arquitectura de dos shells;
- no bloquea fuentes alternativas de O01;
- no bloquea pruebas con baselines permitidos, sanitizados y explícitamente no comerciales.

---

# 4. Arquitectura obligatoria

```text
AXIGNAL PLATFORM
│
├── AXIGNAL Core — autoridad compartida única
│   ├── Identity, tenants, roles, sessions
│   ├── Navigator and ResearchRuns
│   ├── Retrieval and worker runtime
│   ├── Evidence Objects
│   ├── Candidate Claims
│   ├── Deterministic Admission
│   ├── Claim Ledger
│   ├── InvestigationContext
│   ├── Globe, Graph, Timeline and dossiers
│   ├── Opportunity Operations
│   ├── Audit, retention, export and deletion
│   ├── Billing and entitlements
│   └── Observability, security and recovery
│
├── Shared Foundational Libraries — F01–F07
│   ├── F01 Jurisdiction & Geography
│   ├── F02 Entities, Organisations & Ownership
│   ├── F03 Taxonomies & Classifications
│   ├── F04 Time, Currency, Value & Units
│   ├── F05 Languages, Terminology & Translation
│   ├── F06 Rights, Sources & Provenance
│   └── F07 Documents & Content
│
└── EXACTLY TWO DOMAIN SHELLS
    │
    ├── SHELL 1 — AXIGNAL_OPPORTUNITY_INTELLIGENCE
    │   ├── O01 Public Procurement → Bid Workspace
    │   ├── O02 Grants & Non-Dilutive Funding → Application Workspace
    │   ├── O03 Regulation & Policy-Induced Demand → Market Entry & Compliance Workspace
    │   ├── O04 Infrastructure & Capital Projects → Project Pursuit Workspace
    │   ├── O05 Corporate, Filings & Ownership Signals → Account Opportunity Workspace
    │   ├── O06 Sovereign, Macro & Public Investment → Country & Market Strategy Workspace
    │   ├── O07 Trade, Supply Chain & Market Flows → Supply Opportunity Workspace
    │   ├── O08 Energy & Climate Transition → Transition Opportunity Workspace
    │   ├── O09 Innovation, Research & IP → Innovation Opportunity Workspace
    │   └── Cross-library intelligence, portfolio, pursuits, outcomes and learning
    │
    └── SHELL 2 — AXIGNAL_PUBLIC_EMPLOYMENT
        ├── oposiciones, concurso y concurso-oposición
        ├── bolsas y empleo temporal público
        ├── procesos selectivos y promoción interna
        ├── admitidos, excluidos y subsanaciones
        ├── exámenes, puntuaciones y resultados
        ├── nombramientos y bolsas
        └── Application & Examination Workspace
```

## 4.1 Cardinalidad cerrada: exactamente dos shells

El número contractual de shells es `2`. El runtime, el registro, las rutas, los entitlements y las pruebas de conformidad deberán reconocer únicamente:

```text
AXIGNAL_OPPORTUNITY_INTELLIGENCE
AXIGNAL_PUBLIC_EMPLOYMENT
```

Cualquier intento de registrar un tercer shell deberá fallar de forma determinista, salvo que exista una enmienda humana posterior que modifique expresamente este contrato.

## 4.2 País, jurisdicción e idioma no son shells

España, Francia, Alemania, Portugal, Estados Unidos o cualquier otra geografía se modelan mediante:

- F01 Jurisdiction & Geography;
- configuración por jurisdicción;
- adaptadores y Source Manifests;
- idiomas y terminología de F05;
- taxonomías de F03;
- reglas legales y de derechos de F06;
- disclosures de cobertura.

No se duplicarán identidad, navegación, backend o producto por país.

## 4.3 Fuente, biblioteca y workspace no son shells

Una fuente es un origen gobernado. Una biblioteca es un universo de conocimiento. Un workspace es una superficie operativa especializada. Ninguno de ellos constituye un shell.

Las bibliotecas O01–O09 conviven en `AXIGNAL_OPPORTUNITY_INTELLIGENCE` para permitir inteligencia cross-library. Separarlas en shells independientes está prohibido porque fragmentaría el grafo, la experiencia empresarial y el aprendizaje por outcomes.

## 4.4 Procurement es O01, no un tercer shell

```text
O01 Public Procurement
+ Bid Workspace
+ vistas y capacidades especializadas de contratación pública
= módulo de AXIGNAL_OPPORTUNITY_INTELLIGENCE
≠ shell independiente
```

No se creará un producto, navegación, identidad, backend, tenant model, ledger, billing ledger ni registro de shell separado bajo el nombre `AXIGNAL Procurement` o `AXIGNAL_PROCUREMENT`.

## 4.5 Prohibición de forks de producto

Un shell no puede:

- duplicar el backend;
- copiar el Claim Ledger;
- crear su propio modelo de tenant;
- mantener una segunda identidad;
- saltarse F06 Rights & Provenance;
- reimplementar ResearchRun de forma incompatible;
- crear una autoridad de claims diferente;
- divergir en seguridad, auditoría o retención.

Un shell sí puede especializar:

- vocabulario;
- navegación;
- rutas;
- home y dashboards;
- filtros;
- entidades de dominio;
- estados de workspace;
- tareas;
- permisos;
- notificaciones;
- copy;
- onboarding;
- packaging y entitlements.

---

# 5. Contratos horizontales obligatorios

## 5.1 Identidad y tenant

- tenant resuelto exclusivamente en servidor;
- identidad global persistente;
- memberships y capabilities;
- passkey-first;
- recovery y authenticator replacement;
- step-up para acciones críticas;
- sesiones revocables;
- security ledger append-only;
- cross-tenant access = `0`.

## 5.2 Research Spine

```text
browser
→ BFF
→ signed assertion
→ API
→ persistent ResearchRun
→ outbox
→ queue
→ leased worker
→ source adapter
→ evidence
→ claims
→ admission
→ context
→ canonical read model
→ browser reconciliation
```

Debe cubrir:

- idempotencia;
- lease;
- heartbeat;
- crash recovery;
- cancelación;
- retry;
- checkpoints;
- terminalidad;
- progreso observable;
- restart;
- no pérdida de contexto.

## 5.3 Evidence Governance

Cada Evidence Object debe contener, cuando aplique:

- `evidence_id`;
- `tenant_scope`;
- `library_id`;
- `source_id`;
- `source_record_id`;
- `retrieved_at`;
- `observed_at`;
- `published_at`;
- `effective_at`;
- `content_hash`;
- `source_version`;
- `rights_snapshot_id`;
- `language_original`;
- anchors;
- freshness;
- lifecycle state;
- retention class;
- provenance chain.

## 5.4 Candidate Claims y admisión

```text
model proposes
→ deterministic policy evaluates
→ evidence supports or contradicts
→ human reviews where required
→ ledger records
```

El modelo no puede:

- admitirse a sí mismo;
- escribir verdad canónica;
- ocultar contradicción;
- transformar unknown en false;
- transformar ausencia de evidencia en evidencia negativa;
- inventar cross-library causalidad.

## 5.5 Opportunity Operations Core

Entidades mínimas:

```text
Opportunity
Pursuit
Workspace
Decision
Requirement
WorkItem
Milestone
Document
Comment
Approval
SubmissionOrActivation
Outcome
Learning
Template
ActivityEvent
```

Estados comunes mínimos:

```text
DISCOVERED
SAVED
UNDER_REVIEW
DECISION_PENDING
DECLINED
APPROVED
IN_PREPARATION
IN_REVIEW
READY
SUBMITTED_OR_ACTIVATED
ACTIVE
WON_OR_COMPLETED
LOST_OR_REJECTED
CANCELLED
ARCHIVED
```

Cada vertical puede especializar estados, pero no romper auditoría, permisos, exportación ni lineage.

---

# 6. Bibliotecas fundacionales F01–F07

## F01 — Jurisdicción y geografía

Debe soportar:

- países y territorios;
- niveles administrativos;
- regiones y lugares de ejecución;
- NUTS y equivalentes;
- coordenadas y geometrías versionadas;
- zonas económicas;
- husos horarios;
- nombres multilingües;
- cambios históricos.

Gate:

```text
identifiers estables
+ temporalidad
+ geometría versionada
+ alias reversibles
+ licencia
+ precisión
+ coverage disclosure
```

## F02 — Entidades, organizaciones y ownership

Debe soportar:

- organismos públicos;
- buyers y suppliers;
- empresas;
- universidades y centros de investigación;
- fondos y agencias;
- personas sólo cuando exista base legal y minimización;
- identifiers nativos;
- nombres históricos;
- aliases;
- matrices, filiales y relaciones de control;
- ownership temporal observado;
- separación entre observado e inferido.

Gate:

```text
entity resolution reproducible
+ no silent merge
+ native identifiers retained
+ temporal ownership
+ tenant-private entities isolated
```

## F03 — Taxonomías y clasificaciones

Debe admitir, según derechos:

- CPV;
- NUTS;
- NACE/ISIC;
- NAICS/PSC;
- HS/SITC/CPC;
- COFOG;
- taxonomías de energía y clima;
- patentes;
- clasificaciones nacionales.

Regla:

```text
crosswalk proposed != canonical equivalence
```

## F04 — Tiempo, moneda, valor y unidades

Debe diferenciar:

- publicación;
- observación;
- vigencia;
- deadline;
- adjudicación;
- ejecución;
- corrección;
- cancelación.

Debe soportar:

- monedas;
- FX versionado;
- nominal/real;
- impuestos;
- rangos;
- unidades y magnitudes;
- intervalos y unknown.

## F05 — Idiomas, terminología y traducción

Idiomas mínimos de producto:

```text
English
Spanish
French
German
Portuguese
Italian
```

Debe preservar:

- original;
- idioma detectado;
- traducción;
- transliteración;
- glosarios;
- provenance;
- confidence;
- human override;
- equivalencia semántica de acciones críticas.

La traducción no sustituye a la evidencia original.

## F06 — Derechos, fuentes y procedencia

Cada fuente requiere:

- propietario;
- endpoint o mecanismo de acceso;
- ToS/licencia;
- uso comercial;
- redistribución;
- documentos;
- datos personales;
- retención;
- atribución;
- rate limits;
- revocación;
- fecha de revisión;
- legal decision;
- privacy/data-rights decision;
- kill switch;
- quarantine.

## F07 — Documentos y contenido

Formatos mínimos:

```text
HTML XML JSON CSV PDF DOCX XLSX images ZIP feeds XBRL eForms SDMX OCDS
```

Pipeline:

```text
acquire
→ hash
→ malware scan
→ validate type
→ enforce rights
→ extract text/structure
→ OCR only when necessary
→ anchor pages/elements
→ detect language
→ chunk
→ create evidence references
→ propose claims
→ admit or reject
```

---

# 7. Bibliotecas de oportunidad O01–O09

## O01 — Global Public Procurement

### Alcance

- notices;
- prior information;
- opportunities;
- amendments;
- deadlines;
- lots;
- buyers;
- awards;
- contracts;
- frameworks;
- cancellations;
- outcomes;
- spend cuando sea admisible.

### Fuente inicial heredada

- TED.

### Expansión mínima de robustez

O01 no podrá declararse global por TED. Deberá resolver fuentes adicionales de al menos dos regiones fuera de la UE antes del claim global de Procurement.

### Workspace

`Bid Workspace`

- qualification;
- bid/no-bid;
- requirements;
- evidence matrix;
- workplan;
- milestones;
- clarification questions;
- amendments;
- commercial review;
- approvals;
- readiness;
- export/handoff;
- observed outcome;
- learning.

### Límite de autoridad

AXIGNAL no firma ni presenta una oferta salvo contrato futuro explícito y autoridad humana reforzada. Abrir un portal no equivale a presentar.

## O02 — Grants & Non-Dilutive Funding

### Alcance

- programmes;
- calls;
- topics;
- eligibility;
- beneficiaries;
- funding rates;
- budgets;
- deadlines;
- amendments;
- awards;
- reporting obligations.

### Workspace

`Application Workspace`

- eligibility evidence;
- consortium;
- work packages;
- budget;
- impact;
- documents;
- approvals;
- submission handoff;
- result;
- learning.

### Límite

No afirmar elegibilidad jurídica definitiva ni concesión probable sin gate específico.

## O03 — Regulation & Policy-Induced Demand

### Alcance

- legislation;
- regulations;
- consultations;
- delegated acts;
- standards references;
- obligations;
- effective dates;
- affected sectors;
- jurisdictions;
- enforcement and guidance.

### Workspace

`Market Entry & Compliance Workspace`

- obligation map;
- applicability questions;
- evidence;
- gap analysis;
- actions;
- owners;
- deadlines;
- approvals;
- market opportunity hypothesis;
- outcome.

### Límite

AXIGNAL no presta asesoramiento legal. Debe separar texto normativo, interpretación, hipótesis comercial y revisión humana.

## O04 — Infrastructure & Capital Projects

### Alcance

- programmes;
- projects;
- promoters;
- financing;
- permits;
- stages;
- geographies;
- contractors;
- packages;
- milestones;
- delays;
- procurement links.

### Workspace

`Project Pursuit Workspace`

- project thesis;
- stakeholders;
- package map;
- timeline;
- dependencies;
- partner strategy;
- pursuit;
- documents;
- approvals;
- outcome.

## O05 — Corporate, Filings & Ownership Signals

### Alcance

- filings;
- ownership;
- capex;
- acquisitions;
- restructuring;
- facilities;
- partnerships;
- material contracts;
- supply-chain disclosures;
- management changes cuando exista base legal.

### Workspace

`Account Opportunity Workspace`

- account map;
- signal timeline;
- opportunity thesis;
- stakeholders;
- evidence;
- actions;
- approvals;
- CRM handoff;
- outcome.

## O06 — Sovereign, Macro & Public Investment

### Alcance

- budgets;
- public investment plans;
- industrial policy;
- macro indicators;
- debt and sovereign context;
- development programmes;
- country risks;
- sector priorities.

### Workspace

`Country & Market Strategy Workspace`

- country thesis;
- sector priorities;
- evidence;
- scenarios;
- assumptions;
- risks;
- opportunity portfolio;
- decision;
- outcome.

### Límite

No convertir indicadores macro en recomendación financiera personalizada.

## O07 — Trade, Supply Chain & Market Flows

### Alcance

- trade flows;
- imports/exports;
- tariffs;
- routes;
- bottlenecks;
- capacity;
- suppliers;
- dependencies;
- commodities;
- restrictions;
- logistics signals.

### Workspace

`Supply Opportunity Workspace`

- dependency map;
- supplier landscape;
- route and tariff evidence;
- risk and opportunity hypotheses;
- actions;
- qualification;
- partner pursuit;
- outcome.

## O08 — Energy & Climate Transition

### Alcance

- generation;
- grids;
- capacity;
- permits;
- auctions;
- subsidies;
- transition plans;
- emissions obligations;
- climate finance;
- projects;
- offtake and infrastructure signals.

### Workspace

`Transition Opportunity Workspace`

- transition thesis;
- asset/project map;
- regulation;
- financing;
- procurement links;
- stakeholders;
- milestones;
- approvals;
- outcome.

## O09 — Innovation, Research & Intellectual Property

### Alcance

- patents;
- patent families;
- legal status temporal;
- assignees;
- R&D projects;
- research organisations;
- technology programmes;
- partnerships;
- calls and outputs.

### Workspace

`Innovation Opportunity Workspace`

- technology thesis;
- organisation map;
- patent/project evidence;
- partner pursuit;
- milestones;
- documents;
- decision;
- outcome;
- learning.

### Límite

No emitir conclusiones de patentabilidad, validez o freedom-to-operate.

---

# 8. Gate común de cada biblioteca O01–O09

Cada biblioteca debe demostrar:

| Dimensión | Evidencia obligatoria |
|---|---|
| Derechos | decisión jurídica, privacidad, atribución, retención y revocación |
| Acceso | endpoint, formatos, auth, rate limits, retries |
| Cobertura | geografías, periodos, entidades, campos y gaps |
| Calidad | missingness, duplicados, drift, lag, lifecycle |
| Semántica | identifiers, taxonomías, idiomas, reversibilidad |
| Operación | checkpoints, outage, replay, cost, observabilidad |
| Seguridad | tenant isolation, injection, malicious files, abuse |
| Producto | Opportunity + workspace + acciones persistentes |
| Authority | decisiones materiales gobernadas por servidor y humano |
| Outcome | resultado observado, no inferido como hecho |
| Learning | aprendizaje trazable y revocable |
| Rollback | kill switch, quarantine y rollback demostrados |
| Disclosure | cobertura y límites visibles al usuario |

## 8.1 E2E obligatorio por biblioteca

```text
real admitted source
→ ingest
→ normalize
→ Evidence Object
→ Candidate Claim
→ deterministic admission
→ InvestigationContext
→ Opportunity
→ specialized Workspace
→ persistent action
→ human decision
→ handoff or activation
→ observed Outcome
→ Learning
→ rollback test
```

## 8.2 Prohibiciones

No se acepta como E2E:

- fixture final;
- JSON manual introducido directamente en la base de datos;
- fuente real sustituida por mock;
- workspace sin persistencia;
- outcome inventado;
- acción visible sin contrato servidor;
- prueba que intercepta la llamada crítica;
- claims sin rights snapshot.

---

# 9. Plataforma de exactamente dos shells

## 9.1 Shell Registry canónico

Debe existir un registro versionado cuya cardinalidad válida sea exactamente `2` y cuyos únicos `shell_id` admitidos sean:

```text
AXIGNAL_OPPORTUNITY_INTELLIGENCE
AXIGNAL_PUBLIC_EMPLOYMENT
```

Schema mínimo:

```text
shell_id
version
status
brand
navigation
routes
required_libraries
optional_libraries
domain_manifest
workspace_types
capabilities
entitlements
locales
feature_flags
disclosure
```

Estado inicial normativo:

```json
{
  "shell_count_contractual": 2,
  "shells": {
    "AXIGNAL_OPPORTUNITY_INTELLIGENCE": {
      "status": "INHERITED_PARTIAL_IMPLEMENTATION",
      "role": "PRIMARY_PRODUCT_SHELL",
      "required_libraries": [
        "F01", "F02", "F03", "F04", "F05", "F06", "F07",
        "O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09"
      ]
    },
    "AXIGNAL_PUBLIC_EMPLOYMENT": {
      "status": "ARCHITECTURAL_PROOF_PENDING",
      "role": "SECOND_DOMAIN_SHELL",
      "required_libraries": ["F01", "F02", "F03", "F04", "F05", "F06", "F07"]
    }
  },
  "forbidden_shell_ids": [
    "AXIGNAL_PROCUREMENT",
    "AXIGNAL_GLOBAL",
    "COUNTRY_AS_SHELL",
    "LIBRARY_AS_SHELL",
    "SOURCE_AS_SHELL"
  ]
}
```

El validador deberá rechazar:

- un registro con un número de shells distinto de `2`;
- IDs distintos de los dos canónicos;
- `AXIGNAL_PROCUREMENT` como shell;
- un país, jurisdicción, idioma, fuente, biblioteca o workspace registrado como shell;
- alias que permitan recrear de forma encubierta un tercer shell.

## 9.2 Domain Manifest

Cada uno de los dos shells declara:

- entidades;
- vocabulario;
- filtros;
- acciones;
- estados;
- roles;
- permisos;
- eventos;
- notificaciones;
- formularios;
- workspaces;
- dashboards;
- disclosures;
- restricciones legales.

Los manifests pueden extender schemas de forma aditiva, pero no redefinir la autoridad del Core.

## 9.3 Shell 1 — AXIGNAL_OPPORTUNITY_INTELLIGENCE

Usuarios principales:

```text
empresa
organización
equipo de estrategia
business development
ventas
consultoría
inteligencia de mercado
```

Objetivo:

```text
detectar
→ investigar
→ cualificar
→ perseguir
→ presentar o activar
→ observar outcome
→ aprender
```

Estados operativos comunes:

```text
DETECTED
QUALIFYING
QUALIFIED
REJECTED
PURSUING
SUBMITTED_OR_ACTIVATED
WON
LOST
WITHDRAWN
CANCELLED
```

Relación biblioteca-workspace obligatoria:

| Biblioteca | Dominio | Workspace |
|---|---|---|
| `O01` | Public Procurement | Bid Workspace |
| `O02` | Grants & Non-Dilutive Funding | Application Workspace |
| `O03` | Regulation & Policy-Induced Demand | Market Entry & Compliance Workspace |
| `O04` | Infrastructure & Capital Projects | Project Pursuit Workspace |
| `O05` | Corporate, Filings & Ownership Signals | Account Opportunity Workspace |
| `O06` | Sovereign, Macro & Public Investment | Country & Market Strategy Workspace |
| `O07` | Trade, Supply Chain & Market Flows | Supply Opportunity Workspace |
| `O08` | Energy & Climate Transition | Transition Opportunity Workspace |
| `O09` | Innovation, Research & IP | Innovation Opportunity Workspace |

Las nueve bibliotecas forman módulos coordinados del mismo shell. La navegación debe permitir cambiar de lente sin romper la identidad de oportunidad, el grafo, la evidencia, el pursuit o el outcome.

## 9.4 Shell 2 — AXIGNAL_PUBLIC_EMPLOYMENT

Usuarios principales:

```text
persona candidata
futuro preparador autorizado
futura academia autorizada
```

Objetivo:

```text
descubrir empleo público
→ evaluar requisitos con incertidumbre explícita
→ preparar solicitud
→ seguir admisión y subsanación
→ seguir pruebas y resultados
→ registrar nombramiento o bolsa
```

Estados de journey permitidos deberán incluir, cuando proceda:

```text
INTERESTED
ELIGIBILITY_REVIEW
APPLICATION_PREPARING
APPLICATION_SUBMITTED
PROVISIONALLY_ADMITTED
EXCLUDED
REMEDIATION
FINALLY_ADMITTED
EXAMINATION
PASSED
APPOINTED
EMPLOYMENT_POOL
```

## 9.5 Workspace Factory

Debe permitir crear un workspace especializado mediante composición de:

- operaciones comunes;
- schemas de dominio;
- state machine;
- permission matrix;
- templates;
- views;
- validation policies;
- audit event types;
- export formats;
- notifications.

No se acepta `switch(shell_id)` disperso por la aplicación como arquitectura principal.

## 9.6 Entitlements

Los entitlements deben poder aplicarse por:

- uno de los dos shells canónicos;
- biblioteca;
- workspace;
- usuarios;
- capacidad;
- conectores;
- API;
- funciones enterprise.

Un entitlement de O01 habilita capacidades Procurement dentro de `AXIGNAL_OPPORTUNITY_INTELLIGENCE`; no crea ni activa un shell Procurement.

## 9.7 Control de ampliación de shells

Una nueva biblioteca, país o fuente no requiere crear un shell. Un tercer shell sólo podrá proponerse cuando cambien materialmente el tipo de usuario, el objetivo, el vocabulario, la navegación, los permisos, los estados, las acciones, los workspaces y las obligaciones legales.

Incluso en ese caso será obligatoria una enmienda humana versionada. Hasta entonces, la cardinalidad `2` es una invariante normativa y técnica.

---

# 10. Shell 2 preparado: AXIGNAL_PUBLIC_EMPLOYMENT

## 10.1 Definición

`AXIGNAL_PUBLIC_EMPLOYMENT` (`AXIGNAL Public Employment`) cubre:

- oposiciones;
- concurso;
- concurso-oposición;
- bolsas de empleo;
- procesos selectivos;
- empleo temporal público;
- promoción interna;
- nombramientos;
- correcciones;
- listas de admitidos y excluidos;
- resultados.

No debe confundirse con O01 Procurement ni registrarse como una biblioteca O01–O09. Es el segundo shell de dominio sobre el mismo Core y las bibliotecas fundacionales compartidas.

## 10.2 Objetivo contractual

Este contrato no exige lanzar comercialmente el shell de empleo público. Exige demostrar que AXIGNAL puede incorporarlo sin fork, sin duplicación del Core y sin migración destructiva.

Estado final requerido:

```text
PUBLIC_EMPLOYMENT_SHELL_ARCHITECTURE_READY
```

## 10.3 Entidades de dominio mínimas

```text
PublicEmploymentNotice
SelectionProcess
Call
Position
Vacancy
PublicBody
AdministrativeLevel
BodyAndScale
ProfessionalCategory
AccessRoute
ReservedQuota
EligibilityRequirement
Qualification
ApplicationWindow
Fee
Syllabus
ExamStage
ExamEvent
SelectionBoard
AdmittedList
ExcludedList
Correction
Score
Result
Appointment
TemporaryEmploymentPool
AppealWindow
CandidateApplication
CandidateEvidence
```

## 10.4 Journey del candidato

```text
official notice
→ evidence
→ selection process
→ positions and routes
→ requirements
→ eligibility assessment
→ application window
→ documents and fee
→ milestones
→ corrections
→ provisional lists
→ remediation
→ final lists
→ exam stages
→ scores
→ result
→ appointment or pool
```

## 10.5 Estados de elegibilidad

Sólo se permiten estados como:

```text
LIKELY_ELIGIBLE
REQUIRES_REVIEW
MISSING_EVIDENCE
NOT_MATCHED
```

Cada estado debe enlazar:

- requisito original;
- evidencia del candidato;
- regla aplicada;
- incertidumbre;
- revisión humana.

AXIGNAL no puede afirmar elegibilidad jurídica definitiva.

## 10.6 Workspace

`Application & Examination Workspace`

Debe poder componer:

- convocatoria;
- requisitos;
- checklist documental;
- tasas;
- plazos;
- calendario;
- temario;
- etapas de examen;
- sedes;
- listas provisionales;
- subsanación;
- resultados;
- recursos;
- bolsa;
- actividad y auditoría.

## 10.7 Prueba de extensibilidad

La prueba obligatoria utilizará:

1. un `Domain Manifest` real;
2. una convocatoria sintética claramente marcada como fixture contractual;
3. Evidence Objects y Candidate Claims reales sobre ese fixture;
4. admisión determinista;
5. creación del workspace;
6. una acción persistente;
7. auditoría;
8. exportación;
9. tenant isolation;
10. eliminación y retención.

Además, se registrará al menos una fuente oficial candidata como `TECHNICAL_PROBE`, sin claims comerciales ni activación automática.

## 10.8 Criterio de no acoplamiento

La prueba debe demostrar que añadir Public Employment no requiere modificar:

- Claim Ledger;
- tenant model;
- session model;
- Evidence Object base;
- deterministic admission authority;
- billing ledger;
- security ledger.

Las extensiones de schemas deben ser aditivas y versionadas.

## 10.9 Relación con las bibliotecas y el Core

`AXIGNAL_PUBLIC_EMPLOYMENT`:

- reutiliza AXIGNAL Core;
- reutiliza F01–F07;
- utiliza Source Admission Factory, Evidence Objects, Candidate Claims y admisión determinista;
- mantiene entidades, vocabulario, estados y workspace propios mediante su Domain Manifest;
- no es `O10`;
- no es una subbiblioteca de O01;
- no crea un segundo Claim Ledger ni una segunda identidad;
- puede consumir señales contextuales admitidas de O01–O09 cuando los derechos, entitlements y propósito lo permitan, sin mezclar sus claims ni alterar su clase epistémica.

Las fuentes de empleo público se registrarán como fuentes del dominio `PUBLIC_EMPLOYMENT`, no como portales Procurement y no como shells.

---

# 11. Source Admission Factory y legal gates

## 11.1 Estados de fuente

```text
DISCOVERED
LEGAL_REVIEW
PRIVACY_REVIEW
TECHNICAL_PROBE
EVIDENCE_READY
PRODUCT_ADMITTED
COMMERCIAL
SUSPENDED
REVOKED
REJECTED
```

## 11.2 Scope del bloqueo

Un blocker de fuente se propaga sólo a:

- esa fuente;
- los datos derivados de esa fuente;
- los claims dependientes;
- los E2E que requieran específicamente esa fuente;
- los claims comerciales de cobertura asociados.

No se propaga automáticamente a:

- otras fuentes de la misma biblioteca;
- otras bibliotecas;
- contratos del Core;
- Workspace Factory;
- shells;
- billing;
- UX general;
- producción general.

## 11.3 Fuente rechazada

Una fuente `REJECTED`:

- no se consulta en runtime comercial;
- no genera Evidence Objects comerciales;
- no contribuye a coverage;
- mantiene el record de decisión;
- puede conservar únicamente metadatos permitidos para auditoría;
- puede ser sustituida por otra fuente sin rediseñar la biblioteca.

## 11.4 Datos personales

Toda fuente con datos personales requiere:

- finalidad;
- base jurídica;
- minimización;
- categorías;
- retención;
- acceso;
- rectificación/eliminación cuando aplique;
- transferencias;
- subprocessors;
- DPIA cuando proceda;
- owner humano.

---

# 12. Work packages canónicos

## WP0 — Integración contractual y baseline

**Objetivo:** convertir este contrato en la única autoridad operativa sin perder historial.

Tareas:

- `WP0-T01` incorporar `AX-GE2E-FINISH-004`;
- `WP0-T02` marcar `AX-GE2E-FINISH-003` como superseded;
- `WP0-T03` obtener SHA completo local y remoto del baseline `b2ff403`;
- `WP0-T04` auditar commits, diff y working tree;
- `WP0-T05` remapear las 75 tareas antiguas;
- `WP0-T06` migrar el ledger a schema v2;
- `WP0-T07` crear dependency graph sin bloqueo global por TED;
- `WP0-T08` crear Library Registry F01–F07/O01–O09;
- `WP0-T09` crear Shell Registry con exactamente `AXIGNAL_OPPORTUNITY_INTELLIGENCE` y `AXIGNAL_PUBLIC_EMPLOYMENT`, rechazando `AXIGNAL_PROCUREMENT` y cualquier país/biblioteca/fuente como shell;
- `WP0-T10` ejecutar Contract Validation.

Salida:

```text
AX_WP0_GLOBAL_CONTRACT_CANONICALIZED_PASS
```

## WP1 — Research Spine, AXENT y Evidence Governance

Se preservan `WP1-T02..T10` como heredadas hasta auditoría.

Tareas restantes o de ratificación:

- `WP1-T01` resolver source admission de TED sin bloquear otros WP;
- `WP1-T02..T10` verificar evidencia exact-head heredada;
- `WP1-T11` generalizar worker y adapters por `library_id/source_id`;
- `WP1-T12` cancelar, reintentar y reanudar por checkpoint;
- `WP1-T13` contamination containment cross-library;
- `WP1-T14` source-independent contract tests;
- `WP1-T15` multi-library ResearchRun.

Salida:

```text
AX_WP1_RESEARCH_EVIDENCE_PLATFORM_PASS
```

## WP2 — Ontología, Library Registry y Source Factory

Tareas:

- `WP2-T01` contrato base `LibraryManifest`;
- `WP2-T02` contrato base `SourceManifest`;
- `WP2-T03` schema de estados y versionado;
- `WP2-T04` adapter SDK interno;
- `WP2-T05` quality profile;
- `WP2-T06` rights profile;
- `WP2-T07` privacy profile;
- `WP2-T08` outage/retry profile;
- `WP2-T09` coverage disclosure;
- `WP2-T10` kill switch/quarantine;
- `WP2-T11` schema migration strategy;
- `WP2-T12` conformance suite.

Salida:

```text
AX_WP2_LIBRARY_SOURCE_FACTORY_PASS
```

## WP3 — Foundational Libraries F01–F07

Tareas:

- `WP3-T01` F01 Geography;
- `WP3-T02` F02 Entities & Ownership;
- `WP3-T03` F03 Taxonomies;
- `WP3-T04` F04 Time/Currency/Units;
- `WP3-T05` F05 Languages/Terminology;
- `WP3-T06` F06 Rights/Provenance;
- `WP3-T07` F07 Documents/Content;
- `WP3-T08` cross-foundation resolution;
- `WP3-T09` multilingual and temporal regression;
- `WP3-T10` foundational E2E.

Salida:

```text
AX_WP3_ALL_FOUNDATIONAL_LIBRARIES_PASS
```

## WP4 — Opportunity Operations y Workspace Factory

Tareas:

- `WP4-T01` Opportunity;
- `WP4-T02` Pursuit;
- `WP4-T03` Workspace;
- `WP4-T04` requirements/evidence;
- `WP4-T05` work items/milestones;
- `WP4-T06` documents/comments;
- `WP4-T07` approvals;
- `WP4-T08` submission or activation record;
- `WP4-T09` Outcome;
- `WP4-T10` Learning;
- `WP4-T11` Workspace Factory;
- `WP4-T12` generic E2E and rollback.

Salida:

```text
AX_WP4_OPPORTUNITY_OPERATIONS_FACTORY_PASS
```

## WP5 — O01 Procurement y Bid Workspace

Tareas:

- `WP5-T01` TED heredado y source admission;
- `WP5-T02` segunda fuente Procurement;
- `WP5-T03` tercera fuente/segunda macroregión;
- `WP5-T04` notice lifecycle;
- `WP5-T05` lot and amendment semantics;
- `WP5-T06` buyer/supplier resolution;
- `WP5-T07` awards/contracts/outcomes;
- `WP5-T08` relevance and qualification;
- `WP5-T09` Bid Workspace;
- `WP5-T10` approvals and readiness;
- `WP5-T11` official handoff record;
- `WP5-T12` O01 E2E + rollback.

Salida:

```text
AX_WP5_O01_PROCUREMENT_PASS
```

## WP6 — O02 Grants

Tareas:

- source admission;
- grants ontology;
- eligibility;
- calls/topics;
- budgets and rates;
- beneficiaries/awards;
- lifecycle;
- Application Workspace;
- E2E;
- rollback.

Salida:

```text
AX_WP6_O02_GRANTS_PASS
```

## WP7 — O03 Regulation

Tareas:

- source admission;
- legal document lifecycle;
- jurisdiction/effective dates;
- obligations;
- affected sectors;
- amendments/repeals;
- Market Entry & Compliance Workspace;
- legal-authority disclosures;
- E2E;
- rollback.

Salida:

```text
AX_WP7_O03_REGULATION_PASS
```

## WP8 — O04 Infrastructure

Tareas:

- source admission;
- project ontology;
- promoters/funders;
- stages/milestones;
- permits;
- packages/procurement links;
- Project Pursuit Workspace;
- E2E;
- rollback.

Salida:

```text
AX_WP8_O04_INFRASTRUCTURE_PASS
```

## WP9 — O05 Corporate

Tareas:

- source admission;
- company identifiers;
- filings;
- ownership;
- material events;
- capex/expansion signals;
- Account Opportunity Workspace;
- E2E;
- rollback.

Salida:

```text
AX_WP9_O05_CORPORATE_PASS
```

## WP10 — O06 Sovereign & Macro

Tareas:

- source admission;
- indicators and revisions;
- budgets/investment plans;
- policy priorities;
- country/sector context;
- scenario boundaries;
- Country & Market Strategy Workspace;
- E2E;
- rollback.

Salida:

```text
AX_WP10_O06_SOVEREIGN_MACRO_PASS
```

## WP11 — O07 Trade & Supply

Tareas:

- source admission;
- trade classifications;
- flows;
- tariffs/restrictions;
- routes/capacity;
- dependencies;
- Supply Opportunity Workspace;
- E2E;
- rollback.

Salida:

```text
AX_WP11_O07_TRADE_SUPPLY_PASS
```

## WP12 — O08 Energy & Climate

Tareas:

- source admission;
- assets/capacity;
- permits/auctions;
- transition plans;
- climate obligations;
- projects/finance;
- Transition Opportunity Workspace;
- E2E;
- rollback.

Salida:

```text
AX_WP12_O08_ENERGY_CLIMATE_PASS
```

## WP13 — O09 Innovation & IP

Tareas:

- source admission;
- patents/families;
- legal status temporal;
- assignees;
- R&D projects;
- research organisations;
- Innovation Opportunity Workspace;
- legal-limit disclosures;
- E2E;
- rollback.

Salida:

```text
AX_WP13_O09_INNOVATION_IP_PASS
```

## WP14 — Cross-library Intelligence

Tareas:

- `WP14-T01` entity graph;
- `WP14-T02` event lineage;
- `WP14-T03` temporal alignment;
- `WP14-T04` contradiction propagation;
- `WP14-T05` causal hypotheses, never canonical facts;
- `WP14-T06` Globe layers;
- `WP14-T07` Graph lenses;
- `WP14-T08` Timeline reconstruction;
- `WP14-T09` cross-library Navigator;
- `WP14-T10` portfolio;
- `WP14-T11` entitlements;
- `WP14-T12` mandatory cross-library E2E.

E2E mínimo:

```text
regulatory change
→ infrastructure programme
→ procurement notices
→ corporate signals
→ trade dependency
→ energy context
→ opportunity graph
→ pursuit
→ outcome
```

Salida:

```text
AX_WP14_CROSS_LIBRARY_INTELLIGENCE_PASS
```

## WP15 — Two-Shell Platform

Tareas:

- `WP15-T01` crear Shell Registry con cardinalidad exacta `2`;
- `WP15-T02` registrar una sola vez `AXIGNAL_OPPORTUNITY_INTELLIGENCE`;
- `WP15-T03` registrar una sola vez `AXIGNAL_PUBLIC_EMPLOYMENT`;
- `WP15-T04` implementar y versionar el Domain Manifest de ambos shells;
- `WP15-T05` componer navegación sin duplicar identidad ni tenant model;
- `WP15-T06` componer rutas con autorización server-side por shell y capability;
- `WP15-T07` componer workspaces mediante Workspace Factory;
- `WP15-T08` cerrar capability matrix y entitlements por shell/biblioteca/workspace;
- `WP15-T09` implementar analytics y disclosures conscientes del shell;
- `WP15-T10` probar aislamiento entre superficies sin separar el Core;
- `WP15-T11` ejecutar no-fork conformance test;
- `WP15-T12` rechazar `AXIGNAL_PROCUREMENT` y sus alias como shell;
- `WP15-T13` rechazar países, jurisdicciones, idiomas, fuentes, bibliotecas y workspaces como shells;
- `WP15-T14` rechazar un tercer shell sin enmienda humana versionada;
- `WP15-T15` demostrar que O01–O09 permanecen en `AXIGNAL_OPPORTUNITY_INTELLIGENCE` y que Public Employment permanece como segundo shell diferenciado.

Criterios de salida:

```text
shell_count = 2
registered_shell_ids = {
  AXIGNAL_OPPORTUNITY_INTELLIGENCE,
  AXIGNAL_PUBLIC_EMPLOYMENT
}
AXIGNAL_PROCUREMENT registered_as_shell = false
country_as_shell = false
library_as_shell = false
source_as_shell = false
core_forks = 0
```

Salida:

```text
AX_WP15_TWO_SHELL_PLATFORM_PASS
```

## WP16 — Public Employment architectural proof

Tareas:

- domain model;
- manifest;
- routes;
- vocabulary;
- roles/capabilities;
- application/examination workspace;
- eligibility policy states;
- fixture E2E;
- official source technical probe;
- audit/export;
- retention/deletion;
- no-core-modification proof.

Salida:

```text
AX_WP16_PUBLIC_EMPLOYMENT_ARCHITECTURE_READY_PASS
```

## WP17 — Enterprise, Commercial Runtime y Billing

Tareas:

- plans by shell/library;
- seats;
- capacity;
- trial;
- Stripe sandbox;
- checkout/webhooks;
- entitlement reconciliation;
- upgrade/downgrade;
- cancellation/dunning/refund;
- invoices/tax;
- API/webhooks;
- SSO/SCIM;
- private connectors;
- margin and cost telemetry;
- Founder Operations.

Salida:

```text
AX_WP17_ENTERPRISE_COMMERCIAL_RUNTIME_PASS
```

## WP18 — Producción, seguridad, privacidad, UX y distribución

Tareas:

- reproducible deploy;
- staging/production topology;
- secrets;
- SLO/alerts;
- backup/restore/DR;
- incident rehearsal;
- security review;
- privacy/legal;
- source disclosures;
- accessibility WCAG 2.2 AA;
- responsive;
- six languages;
- performance budgets;
- public landing and library pages;
- support runbooks;
- rollback.

Salida:

```text
AX_WP18_PRODUCTION_SECURITY_UX_PASS
```

## WP19 — Aceptación global y release gate

Tareas:

- E2E horizontal;
- E2E F01–F07;
- E2E O01–O09;
- E2E cross-library;
- two-shell proof;
- Public Employment architecture proof;
- Stripe external sandbox;
- security/privacy/legal approvals;
- paid evidence and economics;
- exact-head manifest;
- fresh-process verification;
- human signature.

Salidas posibles:

```text
AXIGNAL_GLOBAL_E2E_COMPLETE
AXIGNAL_GLOBAL_ACCEPTED_FOR_PUBLIC_LAUNCH
REJECTED
IN_PROGRESS
```

No existe `PARTIAL_LAUNCH` como declaración de AXIGNAL completo.

---

# 13. Dependencias y paralelización

## 13.1 Cadena principal

```text
WP0
→ WP1 + WP2
→ WP3 + WP4
→ WP5–WP13
→ WP14
→ WP15 + WP16
→ WP17 + WP18
→ WP19
```

## 13.2 Paralelización autorizada

Tras contratos mínimos de WP2:

```text
WP3 Foundational Libraries
├── WP4 Opportunity Operations
├── source probes WP5–WP13
└── WP15 Two-Shell contracts
```

WP5–WP13 pueden desarrollarse en paralelo cuando:

- `LibraryManifest` esté frozen;
- Source Factory tenga conformance suite;
- F06 Rights exista;
- los foundational services necesarios estén disponibles;
- no se duplique infraestructura común.

WP16 puede comenzar después de WP15 y de los contratos base de WP4, aunque las nueve bibliotecas no estén aceptadas. Su salida es arquitectónica, no comercial.

## 13.3 Bloqueos externos

Un estado `BLOCKED_EXTERNAL` no paraliza trabajo independiente. El ledger deberá contener:

```text
blocked_scope
unblocked_parallel_work
required_external_action
owner
expiry_or_review_date
```

---

# 14. Estados de tarea y cierre

Estados permitidos:

```text
NOT_STARTED
READY
IN_PROGRESS
BLOCKED_INTERNAL
BLOCKED_EXTERNAL
INHERITED_ENGINEERING_PASS
ENGINEERING_PASS
SOURCE_ADMISSION_PENDING
PRODUCT_ACCEPTANCE_PENDING
CANONICAL_ACCEPTED
REJECTED
SUPERSEDED
```

## 14.1 Regla de cierre

Una tarea alcanza `CANONICAL_ACCEPTED` sólo si:

- está integrada en la rama canónica autorizada;
- el SHA completo está registrado;
- el working tree rastreado está limpio;
- las pruebas afectadas son frescas;
- no existen skips inesperados;
- la evidencia es reproducible;
- el contrato y el ledger coinciden;
- no se ha ocultado un blocker externo.

## 14.2 Ingeniería vs aceptación

```text
ENGINEERING_PASS
!= SOURCE_ADMITTED
!= PRODUCT_ACCEPTED
!= PUBLIC_LAUNCH_AUTHORIZED
```

Esta separación impide tanto declarar terminado prematuramente como detener toda la ingeniería por una firma externa.

---

# 15. Matriz E2E final

Todos los siguientes deben ser `PASS`:

```text
fresh install
build reproducible
migrations from zero
upgrade from accepted baseline
bootstrap
signup
passkey
session
recovery
organisation
roles/capabilities
tenant isolation
trial
ResearchRun
worker lease/heartbeat/recovery
multi-library retrieval
Evidence Objects
Candidate Claims
deterministic admission
Claim Ledger
InvestigationContext
Globe/Graph/Timeline
Opportunity
Pursuit
Workspace Factory
O01 Bid Workspace
O02 Application Workspace
O03 Market Entry & Compliance Workspace
O04 Project Pursuit Workspace
O05 Account Opportunity Workspace
O06 Country & Market Strategy Workspace
O07 Supply Opportunity Workspace
O08 Transition Opportunity Workspace
O09 Innovation Opportunity Workspace
Outcome
Learning
cross-library E2E
Shell Registry
Public Employment shell proof
billing and entitlements
Stripe sandbox
seats
export
retention
deletion
legal hold
backup
restore
disaster recovery
security
privacy
source rights
accessibility
responsive
multilingual
observability
kill switches
rollback
support
fresh-process verification
```

---

# 16. Seguridad, privacidad y autoridad

Bloqueadores absolutos de lanzamiento:

- acceso cross-tenant;
- modelo con autoridad canónica;
- fuente sin rights record;
- datos personales sin base y minimización;
- secreto en Git;
- firma o submission autónomo;
- billing live sin autorización;
- restore no probado;
- critical security finding;
- eliminación/exportación no funcional;
- fixture presentado como dato real;
- claim global sin coverage.

Cada shell y biblioteca hereda estas reglas sin excepción.

---

# 17. UX, accesibilidad y multilingüe

## 17.1 Superficies

Debe existir coherencia entre:

- landing global;
- páginas por biblioteca;
- shell principal `AXIGNAL_OPPORTUNITY_INTELLIGENCE`;
- módulo `O01 Public Procurement` y su Bid Workspace dentro del shell principal;
- shell `AXIGNAL_PUBLIC_EMPLOYMENT` preparado;
- Navigator;
- ResearchRun;
- Opportunity;
- workspaces;
- Founder Operations;
- billing;
- settings;
- disclosures.

## 17.2 Estados de interfaz

Toda superficie de datos debe contemplar:

```text
loading
empty
partial
stale
restricted
suspended source
denied
error
recovery
```

## 17.3 Accesibilidad

- WCAG 2.2 AA;
- keyboard-only;
- focus visible;
- landmarks;
- labels;
- dialogs/drawers accesibles;
- zoom/reflow;
- reduced motion;
- equivalentes no visuales para Globe/Graph/Timeline.

## 17.4 Idiomas

Las acciones críticas deben mantener equivalencia semántica en:

```text
en es fr de pt it
```

No se acepta traducir etiquetas y dejar contratos, errores o permisos divergentes.

---

# 18. Comercial, pricing y packaging

La arquitectura comercial debe ser:

```text
AXIGNAL Core
+ shell
+ libraries
+ users
+ workspace capacity
+ enterprise controls
```

Los precios son hipótesis hasta aceptación comercial.

Debe probarse:

- trial gobernado;
- selección explícita de plan;
- no conversión silenciosa;
- checkout sandbox;
- webhook firmado;
- entitlement;
- upgrade/downgrade;
- cancelación;
- dunning;
- refund/dispute;
- seats;
- additional libraries;
- margin por biblioteca;
- source maintenance cost;
- soporte.

El lanzamiento no puede depender de vender una versión reducida que no represente el producto contratado.

---

# 19. Anti-sobreingeniería

La ampliación de alcance no autoriza:

- reescribir el Core ya válido;
- crear microservicios sin necesidad;
- event sourcing universal;
- un segundo grafo o ledger por shell;
- un framework genérico fuera de requisitos demostrados;
- incorporar todas las fuentes conocidas antes de cerrar una biblioteca;
- añadir modelos o agentes sin problema contractual;
- cambiar branding o diseño sin necesidad;
- migraciones destructivas evitables;
- añadir blockchain;
- añadir autonomía de submission;
- construir Public Employment completo antes de demostrar la arquitectura shell.

Regla:

```text
shared contract first
→ one real vertical implementation
→ conformance test
→ reuse
```

---

# 20. Ledger único v2

Ruta:

```text
docs/roadmap/AXIGNAL_E2E_FINISH_LEDGER.json
```

Schema mínimo:

```json
{
  "contract": "AX-GE2E-FINISH-004",
  "contract_version": "2.0.0",
  "goal": "AXIGNAL-GOAL-001",
  "canonical_main_sha": null,
  "recognized_progress_branch": "agent/axignal-local-finalization",
  "recognized_progress_sha": "b2ff4034416892d66385173d9aacd27bce9f055b",
  "public_launch": "NO_GO",
  "global_completion": "IN_PROGRESS",
  "active_work_packages": ["WP0"],
  "external_blockers": [
    {
      "id": "AX-SOURCE-O01-TED-LEGAL-PRIVACY",
      "scope": ["O01:TedSourceAdmission", "TED_COMMERCIAL_CLAIMS"],
      "does_not_block": ["WP2", "WP3", "WP4", "WP6-WP16"],
      "required_action": "human legal and privacy decision"
    }
  ],
  "work_packages": {
    "WP0": "IN_PROGRESS",
    "WP1": "INHERITED_ENGINEERING_PASS",
    "WP2": "READY",
    "WP3": "BLOCKED_INTERNAL",
    "WP4": "READY",
    "WP5": "IN_PROGRESS",
    "WP6": "READY",
    "WP7": "READY",
    "WP8": "READY",
    "WP9": "READY",
    "WP10": "READY",
    "WP11": "READY",
    "WP12": "READY",
    "WP13": "READY",
    "WP14": "BLOCKED_INTERNAL",
    "WP15": "READY",
    "WP16": "BLOCKED_INTERNAL",
    "WP17": "READY",
    "WP18": "READY",
    "WP19": "BLOCKED_INTERNAL"
  },
  "libraries": {
    "F01": "NOT_STARTED",
    "F02": "NOT_STARTED",
    "F03": "NOT_STARTED",
    "F04": "NOT_STARTED",
    "F05": "INHERITED_PARTIAL_IMPLEMENTATION",
    "F06": "INHERITED_PARTIAL_IMPLEMENTATION",
    "F07": "INHERITED_PARTIAL_IMPLEMENTATION",
    "O01": "INHERITED_ENGINEERING_PASS",
    "O02": "NOT_STARTED",
    "O03": "NOT_STARTED",
    "O04": "NOT_STARTED",
    "O05": "NOT_STARTED",
    "O06": "NOT_STARTED",
    "O07": "NOT_STARTED",
    "O08": "NOT_STARTED",
    "O09": "NOT_STARTED"
  },
  "shell_count_contractual": 2,
  "shells": {
    "AXIGNAL_OPPORTUNITY_INTELLIGENCE": "INHERITED_PARTIAL_IMPLEMENTATION",
    "AXIGNAL_PUBLIC_EMPLOYMENT": "ARCHITECTURAL_PROOF_PENDING"
  },
  "forbidden_shell_ids": [
    "AXIGNAL_PROCUREMENT",
    "COUNTRY_AS_SHELL",
    "LIBRARY_AS_SHELL",
    "SOURCE_AS_SHELL"
  ],
  "allowed_next_transition": "WP0_CANONICALIZE_AND_REMAP_ONLY"
}
```

Los estados del ejemplo son estados normativos iniciales; cualquier cambio deberá quedar ligado a evidencia exact-head y a una transición permitida del ledger.

---

# 21. Evidencia exact-head

Cada cierre de WP debe entregar:

- base SHA completo;
- head SHA completo;
- tree SHA;
- branch;
- commit list;
- diff stat;
- files changed;
- migrations;
- tests afectados;
- integration tests;
- E2E;
- skips y justificación;
- source calls sanitizadas;
- rights decisions;
- coverage report;
- security checks;
- secrets check con comando exacto;
- build fresco;
- working tree status;
- rollback;
- unresolved blockers;
- owner;
- output marker.

No se aceptan como prueba suficiente:

- resumen narrativo sin comandos;
- SHA abreviado para cierre final;
- screenshot sin artefacto;
- test cacheado presentado como fresco;
- “diff limpio” con cambios rastreados pendientes;
- push no confirmado remotamente.

---

# 22. Primera transición autorizada

La primera ejecución bajo este contrato será exclusivamente contractual y de auditoría.

```text
AX-GE2E-FINISH-004 / WP0
```

El agente deberá:

1. no modificar funcionalidad;
2. incorporar este contrato en `docs/contracts/AX-GE2E-FINISH-004.md`;
3. marcar `AX-GE2E-FINISH-003` como superseded sin borrarlo;
4. obtener SHA completo de base, HEAD local y HEAD remoto;
5. auditar el baseline heredado;
6. migrar el ledger a v2;
7. mapear las 75 tareas anteriores a WP0–WP19;
8. preservar `WP1-T02..T10` como `INHERITED_ENGINEERING_PASS` hasta verificación;
9. convertir el blocker de TED en blocker de scope local;
10. crear Library Registry y Shell Registry iniciales con exactamente los dos IDs canónicos;
11. producir dependency graph;
12. ejecutar validación documental;
13. realizar commit y push sólo si el mandato del agente lo autoriza expresamente;
14. no desplegar;
15. no administrar GitHub;
16. no comenzar O02–O09 hasta cerrar la integración contractual.

Salida:

```text
AX_WP0_GLOBAL_CONTRACT_CANONICALIZED_PASS
```

---

# 23. Definition of Done global

AXIGNAL sólo se considera acabado cuando:

```text
Core                               CANONICAL_ACCEPTED
F01–F07                            7/7 CANONICAL_ACCEPTED
O01–O09                            9/9 CANONICAL_ACCEPTED
Opportunity Operations             CANONICAL_ACCEPTED
Workspace Factory                  CANONICAL_ACCEPTED
workspaces especializados          9/9 CANONICAL_ACCEPTED
cross-library E2E                  PASS
Shell Registry cardinality         EXACTLY_2_PASS
Registered shell IDs               EXACT_CANONICAL_SET_PASS
AXIGNAL_OPPORTUNITY_INTELLIGENCE   CANONICAL_ACCEPTED
AXIGNAL_PUBLIC_EMPLOYMENT          ARCHITECTURE_PASS
AXIGNAL_PROCUREMENT as shell       REJECTED_BY_CONTRACT
Country/library/source as shell    REJECTED_BY_CONTRACT
Third shell registered             0
Public Employment architecture     PASS
Commercial Runtime                 PASS
Production/Security/Privacy        PASS
Accessibility/Multilingual         PASS
Source rights                      PASS
Backup/Restore/DR                  PASS
Global rollback                    PASS
Critical security findings         0
Exact-head final manifest          PASS
Human launch authority             SIGNED
```

Hasta entonces:

```text
AXIGNAL_GLOBAL_E2E_COMPLETE = false
PUBLIC_LAUNCH = NO_GO
```

---

# 24. Firma y activación

## Decisión de la autoridad humana

```text
SCOPE_DECISION:
- implementar F01–F07;
- implementar O01–O09;
- conservar TED como primera fuente de O01;
- no limitar AXIGNAL a Procurement;
- mantener Opportunity Operations;
- implementar una plataforma con exactamente dos shells;
- establecer `AXIGNAL_OPPORTUNITY_INTELLIGENCE` como shell principal de F01–F07 + O01–O09;
- mantener O01 Procurement como biblioteca y Bid Workspace, nunca como shell;
- demostrar `AXIGNAL_PUBLIC_EMPLOYMENT` como segundo shell sin fork;
- prohibir shells por país, fuente o biblioteca;
- no lanzar públicamente hasta completar este contrato.
```

## Activación técnica

Este documento adquiere autoridad operativa en el repositorio cuando:

1. se incorpora con su `Contract ID` intacto;
2. el ledger referencia `AX-GE2E-FINISH-004`;
3. el contrato anterior queda marcado `SUPERSEDED`;
4. la autoridad humana aprueba el diff contractual;
5. la validación documental pasa.

---

# Anexo A — Marcadores canónicos

```text
AX_WP0_GLOBAL_CONTRACT_CANONICALIZED_PASS
AX_WP1_RESEARCH_EVIDENCE_PLATFORM_PASS
AX_WP2_LIBRARY_SOURCE_FACTORY_PASS
AX_WP3_ALL_FOUNDATIONAL_LIBRARIES_PASS
AX_WP4_OPPORTUNITY_OPERATIONS_FACTORY_PASS
AX_WP5_O01_PROCUREMENT_PASS
AX_WP6_O02_GRANTS_PASS
AX_WP7_O03_REGULATION_PASS
AX_WP8_O04_INFRASTRUCTURE_PASS
AX_WP9_O05_CORPORATE_PASS
AX_WP10_O06_SOVEREIGN_MACRO_PASS
AX_WP11_O07_TRADE_SUPPLY_PASS
AX_WP12_O08_ENERGY_CLIMATE_PASS
AX_WP13_O09_INNOVATION_IP_PASS
AX_WP14_CROSS_LIBRARY_INTELLIGENCE_PASS
AX_WP15_TWO_SHELL_PLATFORM_PASS
AX_WP16_PUBLIC_EMPLOYMENT_ARCHITECTURE_READY_PASS
AX_WP17_ENTERPRISE_COMMERCIAL_RUNTIME_PASS
AX_WP18_PRODUCTION_SECURITY_UX_PASS
AXIGNAL_GLOBAL_E2E_COMPLETE
AXIGNAL_GLOBAL_ACCEPTED_FOR_PUBLIC_LAUNCH
```

# Anexo B — Salidas prohibidas

```text
AXIGNAL_COMPLETE_WITH_TED_ONLY
AXIGNAL_GLOBAL_COMPLETE_WITH_O01_ONLY
PUBLIC_LAUNCH_WITH_UNADMITTED_SOURCES
PUBLIC_LAUNCH_WITH_PARTIAL_LIBRARIES
PUBLIC_EMPLOYMENT_COMMERCIAL_WITH_FIXTURES
AXIGNAL_PROCUREMENT_SHELL_REGISTERED
COUNTRY_REGISTERED_AS_SHELL
LIBRARY_REGISTERED_AS_SHELL
SOURCE_REGISTERED_AS_SHELL
THIRD_SHELL_WITHOUT_HUMAN_AMENDMENT
MODEL_ADMITTED_CLAIM
AUTONOMOUS_BID_SUBMISSION
AUTONOMOUS_LEGAL_ELIGIBILITY_DECISION
```

# Anexo C — Regla operativa resumida

```text
No rehacer lo que ya funciona.
No fingir lo que aún no existe.
No bloquear todo por una fuente.
No duplicar el núcleo para un shell.
Mantener exactamente dos shells salvo nueva enmienda humana.
No convertir Procurement, un país, una fuente o una biblioteca en shell.
No llamar global a una cobertura local.
No lanzar hasta cerrar F01–F07, O01–O09 y los E2E.
```

# Anexo D — Matriz canónica de clasificación

| Elemento | Clasificación contractual | ¿Puede registrarse como shell? |
|---|---|---:|
| `AXIGNAL_OPPORTUNITY_INTELLIGENCE` | Shell 1 principal | Sí |
| `AXIGNAL_PUBLIC_EMPLOYMENT` | Shell 2 de dominio | Sí |
| `O01 Public Procurement` | Biblioteca de oportunidad | No |
| `O02–O09` | Bibliotecas de oportunidad | No |
| `F01–F07` | Bibliotecas fundacionales compartidas | No |
| Bid/Application/Project/etc. Workspace | Workspace especializado | No |
| España, Francia, Alemania u otro país | Jurisdicción/geografía | No |
| TED u otro portal/API | Fuente | No |
| idioma o taxonomía | Configuración/biblioteca fundacional | No |

Invariante final:

```text
platform_count = 1
core_count = 1
shell_count = 2
foundational_library_count = 7
opportunity_library_count = 9
procurement_shell_count = 0
country_shell_count = 0
source_shell_count = 0
unauthorised_third_shell_count = 0
```

