# AX-GE2E-FINISH-004 — Contrato global rector de la finalización E2E AXIGNAL

```text
Contract ID: AX-GE2E-FINISH-004
Version: 2.0.0
Date: 2026-08-07
Status:
HUMAN_SCOPE_DECISION_APPROVED /
ACTIVE /
REPOSITORY_INTEGRATED /
NO_PUBLIC_LAUNCH
```

---

## 0. Autoridad y jerarquía contractual

La jerarquía obligatoria de este programa es:

```text
1. Decisiones humanas explícitas
2. AXIGNAL-GOAL-001
3. AX-GE2E-FINISH-004 v2.0.0
4. AX-CAPTURE-E2E-001 v1.1
5. Ledger y roadmap canónicos
6. Tareas de implementación
```

Roles contractuales:

```text
AX-GE2E-FINISH-004
= contrato global rector del producto

AX-CAPTURE-E2E-001
= contrato especializado subordinado para el agente de captación comercial

AX-GE2E-FINISH-003
= contrato histórico superseded
```

Una capa inferior no puede reducir, reinterpretar, dividir o reemplazar silenciosamente una obligación superior.

El contrato de captación no sustituye, limita ni redefine la arquitectura global.

---

## 1. Identidad del producto

- Public brand: **AXIGNAL**
- Public domain: **axignal.com**
- Repository and technical slug: **axignal**
- Goal ID: `AXIGNAL-GOAL-001`
- Parent category: **Global Opportunity Intelligence & Operations**
- Primer marco comercial: **Business-to-Government (B2G) Opportunity Intelligence**
- Primer universo de adquisición: **contratos públicos y licitaciones globales**

Las cadenas heredadas `ASIGNAL`, `asignal.com` y `ASIGNAL-GOAL-001` son defectos activos y deben fallar la validación del repositorio.

---

## 2. Arquitectura canónica de shells

Decisión humana vinculante: **AXIGNAL tiene exactamente dos shells de producto en el alcance actual.**

```text
AXIGNAL PLATFORM
│
├── AXIGNAL Core
│
├── Foundational Libraries
│   └── F01–F07
│
├── SHELL_01
│   └── AXIGNAL_OPPORTUNITY_INTELLIGENCE
│       ├── O01 Public Procurement
│       ├── O02 Grants
│       ├── O03 Regulation
│       ├── O04 Infrastructure
│       ├── O05 Corporate
│       ├── O06 Sovereign & Macro
│       ├── O07 Trade & Supply Chain
│       ├── O08 Energy & Climate
│       ├── O09 Innovation & IP
│       └── nueve workspaces especializados
│
└── SHELL_02
    └── AXIGNAL_PUBLIC_EMPLOYMENT
        └── prueba arquitectónica de oposiciones,
            procesos selectivos y empleo público
```

Valores canónicos:

```text
PRIMARY_SHELL_ID=AXIGNAL_OPPORTUNITY_INTELLIGENCE
SECOND_SHELL_ID=AXIGNAL_PUBLIC_EMPLOYMENT
SHELL_COUNT_SCOPE=2

PROCUREMENT_LIBRARY_ID=O01
PROCUREMENT_IS_SHELL=false

COUNTRY_IS_SHELL=false
JURISDICTION_IS_SHELL=false
SOURCE_IS_SHELL=false
LIBRARY_IS_SHELL=false
LANGUAGE_IS_SHELL=false
WORKSPACE_IS_SHELL=false
CAPTURE_AGENT_IS_SHELL=false
```

### 2.1 Qué no constituye un shell

No se creará un shell por país, territorio, idioma, fuente, portal, biblioteca, buyer persona, plan comercial ni workspace.

- Países y territorios son **jurisdicciones** y configuraciones de cobertura gobernadas principalmente por `F01`.
- `F01–F07` y `O01–O09` son **bibliotecas** (módulos de conocimiento y oportunidad) dentro de `AXIGNAL_OPPORTUNITY_INTELLIGENCE`.
- Los workspaces son superficies operativas especializadas dentro del shell empresarial.

### 2.2 Procurement no es un shell

La contratación pública se clasifica canónicamente como:

```text
O01=PUBLIC_PROCUREMENT_LIBRARY
→ biblioteca de oportunidad
→ Bid Workspace
→ módulo del shell AXIGNAL_OPPORTUNITY_INTELLIGENCE
```

Queda prohibido modelar, documentar o implementar `AXIGNAL Procurement` como shell independiente o tercer shell.

No se crearán `shell_id` como `AXIGNAL_GLOBAL`, `AXIGNAL_PROCUREMENT`, `AXIGNAL_SPAIN`, `AXIGNAL_FRANCE`, `AXIGNAL_O01` ni `AXIGNAL_O02`.

El término "Global Opportunity Intelligence" puede mantenerse como categoría o descripción del producto; el ID de shell será siempre `AXIGNAL_OPPORTUNITY_INTELLIGENCE`.

---

## 3. Domain Shells

```text
Domain Shells
├── AXIGNAL Opportunity Intelligence
└── AXIGNAL Public Employment
```

### 3.1 AXIGNAL Opportunity Intelligence

- `shell_id=AXIGNAL_OPPORTUNITY_INTELLIGENCE`
- `display_name=AXIGNAL Opportunity Intelligence`
- Estado: `INHERITED_PARTIAL_IMPLEMENTATION`
- Cobertura: `GLOBAL`
- Bibliotecas requeridas: `F01–F07`, `O01–O09`
- Contiene la biblioteca Procurement: `O01`
- Workspaces especializados: nueve (uno por biblioteca O01–O09)

### 3.2 AXIGNAL Public Employment

- `shell_id=AXIGNAL_PUBLIC_EMPLOYMENT`
- `display_name=AXIGNAL Public Employment`
- Estado: `ARCHITECTURAL_PROOF_PENDING`
- Lanzamiento comercial autorizado: `false`
- Dominio: `PUBLIC_EMPLOYMENT_AND_SELECTION_PROCESSES`
- Alcance de prueba: oposiciones, procesos selectivos, concurso y concurso-oposición, bolsas de empleo público, listas de admitidos y excluidos, pruebas, resultados y nombramientos, workspace de candidatura y examen

No se implementará funcionalmente Public Employment durante WP0; su arquitectura se demostrará mediante Domain Manifest y contratos de shell, reutilizando AXIGNAL Core y los servicios fundacionales que correspondan.

---

## 4. Agente de captación comercial

```text
CAPTURE_AGENT_CONTRACT=AX-CAPTURE-E2E-001
CAPTURE_AGENT_PRODUCT_SHELL=AXIGNAL_OPPORTUNITY_INTELLIGENCE
CAPTURE_AGENT_INITIAL_SIGNAL_LIBRARY=O01
CAPTURE_AGENT_IS_SHELL=false
```

El agente de captación:

- pertenece al shell empresarial;
- puede comenzar mediante señales O01;
- podrá usar O02–O09 cuando estén admitidas;
- no convierte Procurement en shell;
- no crea otro backend;
- no crea otra identidad;
- no crea otro Claim Ledger;
- no crea otra autoridad de evidencia;
- no autoriza outreach público o automático.

---

## 5. Experiencia de producto (UX)

El shell inicial operativo es:

```text
AXIGNAL Opportunity Intelligence
```

El shell adicional preparado es:

```text
AXIGNAL Public Employment
```

Dentro de `AXIGNAL Opportunity Intelligence`, la contratación pública se presenta como:

```text
módulo O01 Procurement y Bid Workspace
dentro de AXIGNAL Opportunity Intelligence
```

No existe una superficie de producto llamada "shell Procurement".

Ejemplo de estado de shells:

```json
{
  "shells": {
    "AXIGNAL_OPPORTUNITY_INTELLIGENCE": "INHERITED_PARTIAL_IMPLEMENTATION",
    "AXIGNAL_PUBLIC_EMPLOYMENT": "ARCHITECTURAL_PROOF_PENDING"
  }
}
```

---

## 6. Bibliotecas

Bibliotecas fundacionales: `F01–F07`.

Bibliotecas de oportunidad del shell empresarial: `O01–O09`.

```text
F01 jurisdicción y geografía
F02 entidades, organizaciones y ownership
F03 taxonomías
F04 tiempo, moneda, valor y unidades
F05 idiomas y terminología
F06 derechos, fuentes y procedencia
F07 documentos y contenido

O01 Public Procurement
O02 Grants & Non-Dilutive Funding
O03 Regulation & Policy-Induced Demand
O04 Infrastructure & Capital Projects
O05 Corporate, Filings & Ownership Signals
O06 Sovereign, Macro & Public Investment
O07 Trade, Supply Chain & Market Flows
O08 Energy & Climate Transition
O09 Innovation, Research & IP
```

No se creará `O10` durante WP0. No se creará una biblioteca nueva para Public Employment durante WP0.

---

## 7. Cadena de valor canónica

AXIGNAL combina:

```text
Global Opportunity Intelligence
+ Evidence-Governed Investigation
+ Opportunity Operations
```

Debe soportar el camino:

```text
señales
→ evidencia admitida
→ Candidate Claims
→ admisión determinista
→ InvestigationContext
→ Opportunity
→ Pursuit
→ Operational Workspace
→ Outcome
→ Learning
```

AXIGNAL no puede reducirse a chatbot, lista de alertas, espejo de datos públicos, dashboard estático, copiloto de investigación genérico ni generador de claims/dossiers sin flujo operativo.

---

## 8. Autoridad epistémica

- El vector descubre; el grafo contextualiza; el runtime admite.
- Los agentes pueden proponer Candidate Claims.
- Los validadores deterministas deciden la validez estructural.
- Las políticas de admisibilidad deciden si un claim entra en el ledger canónico.
- Modelos y workers no pueden admitir fuentes, admitir claims canónicos, otorgar autoridad de tenant, asignar seats, conceder trials, publicar páginas SEO, mutar Search Console, instalar conectores MCP ni autorizar el lanzamiento público.

---

## 9. Restricciones de WP0

WP0 es exclusivamente contractual, registral, documental y de auditoría.

Durante WP0 no se permite:

- implementar O02–O09;
- implementar Public Employment funcionalmente;
- implementar el agente de captación;
- cambiar lógica funcional;
- modificar worker, API o frontend;
- crear un shell Procurement;
- crear un shell por país, biblioteca, fuente o idioma;
- crear `O10`;
- duplicar Core o Claim Ledger;
- resolver el blocker legal fingiendo aprobación;
- autorizar outreach;
- enviar comunicaciones;
- desplegar;
- acceder al VPS;
- hacer merge;
- abrir PR;
- administrar GitHub;
- borrar archivos históricos;
- marcar AXIGNAL como terminado.

---

## 10. Baseline heredado y reservas de auditoría

```text
BASE_SHA=7c551728c7d750ee35b3607a3939df493f697592
INHERITED_HEAD=b2ff4034416892d66385173d9aacd27bce9f055b
REMOTE_MATCH=PASS
TRACKED_WORKTREE_CLEAN=PASS
```

Se preservan como herencia de ingeniería (no como aceptación canónica):

```text
WP1-T02..WP1-T10=INHERITED_ENGINEERING_PASS
```

Reservas de auditoría:

```text
TED_TECHNICAL_PROBE=PASS
TED_EVIDENCE_READY=PASS
TED_PRODUCT_ADMITTED=BLOCKED_BY_HUMAN_LEGAL_PRIVACY
TED_COMMERCIAL_READY=BLOCKED_BY_HUMAN_LEGAL_PRIVACY

APPLICATION_APPEND_ONLY=PASS
DATABASE_ENFORCED_APPEND_ONLY=PENDING

DIFF_SECRET_PATTERN_CHECK=PASS
FULL_SECRET_SCANNER=PENDING

IDENTITY_PASSWORDLESS_ISOLATED_E2E=PASS

COMMERCIAL_SHELL_E2E=E2E_DEFERRED_BY_TOPOLOGY
ORGANIC_DISCOVERY_E2E=E2E_DEFERRED_BY_TOPOLOGY
QUALIFIED_VALIDATION_E2E_1=E2E_DEFERRED_BY_TOPOLOGY
QUALIFIED_VALIDATION_E2E_2=E2E_DEFERRED_BY_TOPOLOGY
SEAT_GOVERNANCE_E2E=E2E_DEFERRED_BY_TOPOLOGY
```

Los cinco recorridos E2E diferidos no se declaran cubiertos por pruebas unitarias.

La prueba técnica de TED no constituye admisión comercial.

---

## 11. Definición de finalización E2E

AXIGNAL estará terminado cuando complete de forma real y persistente el recorrido completo:

```text
visitante
→ registro y verificación
→ passkey y sesión revocable
→ organización, tenant, roles, seats y trial
→ navegación y research persistente
→ evidencia admitida
→ Candidate Claims
→ admisión determinista
→ InvestigationContext
→ Opportunity y Pursuit
→ Bid Workspace
→ Outcome y Learning
→ billing, Founder Operations y producción
→ aceptación privada
→ autorización humana final de lanzamiento
```

Sin embargo, el alcance de este contrato exige que el bloqueo legal de TED **deje de bloquear globalmente el programa**: AXIGNAL Core, F01–F07, O02–O09, Workspace Factory, plataforma multishell y la prueba arquitectónica de Public Employment permanecen ejecutables en paralelo.

---

## 12. Estado contractual

```text
GLOBAL_CONTRACT=AX-GE2E-FINISH-004
GLOBAL_CONTRACT_VERSION=2.0.0
GLOBAL_CONTRACT_STATUS=HUMAN_SCOPE_DECISION_APPROVED/ACTIVE/REPOSITORY_INTEGRATED/NO_PUBLIC_LAUNCH
SPECIALIZED_CAPTURE_CONTRACT=AX-CAPTURE-E2E-001
SPECIALIZED_CAPTURE_CONTRACT_VERSION=1.1
OLD_CONTRACT_SUPERSESSION=AX-GE2E-FINISH-003 v1.5.0 SUPERSEDED 2026-08-07
```

Sólo una tarea de lanzamiento autorizada por la autoridad humana puede producir la disposición pública final.
