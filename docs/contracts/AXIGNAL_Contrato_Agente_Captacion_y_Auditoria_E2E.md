# AXIGNAL — Contrato de desarrollo y auditoría del agente de captación comercial

```text
CONTRACT_ID             AX-CAPTURE-E2E-001
VERSION                 1.1
DATE                    2026-08-07
PRODUCT                 AXIGNAL
REPOSITORY              LowToHi/axignal
GOAL_ID                 AXIGNAL-GOAL-001
GOVERNING_CONTRACT      AX-GE2E-FINISH-004 v2.0.0
CONTRACT_ROLE           SPECIALIZED_SUBORDINATE_CONTRACT
PRIMARY_PRODUCT_SHELL   AXIGNAL_OPPORTUNITY_INTELLIGENCE
SECOND_PRODUCT_SHELL    AXIGNAL_PUBLIC_EMPLOYMENT
SHELL_COUNT_SCOPE       2
PROCUREMENT_STATUS      O01_LIBRARY_NOT_A_SHELL
COUNTRY_STATUS          JURISDICTION_CONFIGURATION_NOT_A_SHELL
STATUS                  AUTHORITATIVE SPECIALIZED DEVELOPMENT CONTRACT
PUBLIC_OUTREACH         NOT_AUTHORIZED
AUTOMATIC_SENDING       NOT_AUTHORIZED
```

---

## 0. Autoridad, arquitectura multishell y límites de este contrato

### 0.1 Naturaleza subordinada

Este contrato regula exclusivamente el desarrollo y la auditoría del agente de captación e inteligencia comercial utilizado para identificar empresas potencialmente interesadas en AXIGNAL.

No define, limita ni sustituye la arquitectura global del producto.

La autoridad arquitectónica superior es:

```text
AX-GE2E-FINISH-004 v2.0.0
```

La jerarquía aplicable es:

```text
decisión humana explícita
→ AXIGNAL-GOAL-001
→ AX-GE2E-FINISH-004
→ este contrato AX-CAPTURE-E2E-001
→ tareas de implementación
→ código
→ evidencia exact-head
```

Una capa inferior no puede reducir, reinterpretar, dividir o reemplazar silenciosamente una obligación superior.

### 0.2 Arquitectura canónica de dos shells

La arquitectura vigente de producto contiene exactamente dos shells en el alcance actual:

```text
AXIGNAL PLATFORM
│
├── SHELL 1 — AXIGNAL_OPPORTUNITY_INTELLIGENCE
│   ├── AXIGNAL Core
│   ├── F01–F07 Foundational Libraries
│   ├── O01 Public Procurement
│   ├── O02 Grants & Non-Dilutive Funding
│   ├── O03 Regulation & Policy-Induced Demand
│   ├── O04 Infrastructure & Capital Projects
│   ├── O05 Corporate, Filings & Ownership Signals
│   ├── O06 Sovereign, Macro & Public Investment
│   ├── O07 Trade, Supply Chain & Market Flows
│   ├── O08 Energy & Climate Transition
│   ├── O09 Innovation, Research & IP
│   └── workspaces especializados por biblioteca
│
└── SHELL 2 — AXIGNAL_PUBLIC_EMPLOYMENT
    ├── oposiciones
    ├── procesos selectivos
    ├── concurso y concurso-oposición
    ├── bolsas de empleo público
    ├── listas de admitidos y excluidos
    ├── pruebas, resultados y nombramientos
    └── workspace de candidatura y examen
```

Esta decisión es vinculante para cualquier implementación derivada del presente contrato.

### 0.3 Qué no constituye un shell

No se creará un shell por:

- país;
- territorio;
- idioma;
- fuente;
- portal;
- biblioteca;
- buyer persona;
- plan comercial;
- workspace.

Los países y territorios son jurisdicciones y configuraciones de cobertura gobernadas principalmente por `F01`.

Las bibliotecas `F01–F07` y `O01–O09` son módulos de conocimiento y oportunidad dentro de `AXIGNAL_OPPORTUNITY_INTELLIGENCE`.

Los workspaces son superficies operativas especializadas dentro del shell empresarial.

### 0.4 Procurement no es un tercer shell

La contratación pública se clasifica canónicamente como:

```text
O01_PUBLIC_PROCUREMENT
→ biblioteca de oportunidad
→ Bid Workspace
→ módulo del shell AXIGNAL_OPPORTUNITY_INTELLIGENCE
```

Por tanto, queda prohibido modelar, documentar o implementar `AXIGNAL Procurement` como un tercer shell independiente.

Cualquier referencia histórica que lo denomine shell deberá interpretarse como nombre funcional del módulo `O01` o corregirse mediante la enmienda contractual correspondiente.

### 0.5 Ubicación del agente de captación

El agente definido en este contrato pertenece al plano comercial de:

```text
AXIGNAL_OPPORTUNITY_INTELLIGENCE
```

Su primer motion comercial puede concentrarse en empresas que compiten en contratación pública y utilizar prioritariamente señales de `O01`.

Eso no convierte a AXIGNAL en un producto limitado a Procurement ni autoriza a reducir el producto global a TED, O01 o B2G.

Cuando existan fuentes admitidas y utilidad comercial demostrada, el agente podrá utilizar señales de `O02–O09` para identificar cuentas, contactos y triggers, manteniendo el mismo contrato de evidencia, privacidad, estados y autoridad.

### 0.6 Núcleo compartido y prohibición de forks

El agente de captación debe reutilizar, cuando corresponda, los contratos y autoridades comunes de AXIGNAL:

- identidad y tenant;
- F01 jurisdicción y geografía;
- F02 entidades, organizaciones y ownership;
- F03 taxonomías;
- F04 tiempo, moneda, valor y unidades;
- F05 idiomas y terminología;
- F06 derechos, fuentes y procedencia;
- F07 documentos y contenido;
- Evidence Objects;
- Candidate Claims;
- admisión determinista;
- Claim Ledger;
- auditoría, retención y eliminación;
- observabilidad, kill switches y rollback.

Queda prohibido crear para captación:

- un backend de producto paralelo;
- un segundo sistema de identidad;
- un Claim Ledger incompatible;
- una autoridad de fuentes separada;
- una ontología nacional duplicada;
- una copia de las bibliotecas por país;
- una variante del producto que evite la arquitectura multishell.

### 0.7 Regla de conflicto

En caso de contradicción:

```text
AX-GE2E-FINISH-004
> AX-CAPTURE-E2E-001
> implementación
```

La cláusula de anti-sobreingeniería de este contrato sólo limita componentes innecesarios dentro del agente de captación.

No puede utilizarse para eliminar, posponer o impedir:

- Shell Registry;
- Domain Manifest;
- Workspace Factory;
- F01–F07;
- O01–O09;
- inteligencia cross-library;
- `AXIGNAL_PUBLIC_EMPLOYMENT`;
- cualquier otra obligación explícita de `AX-GE2E-FINISH-004`.

---

## 1. Propósito

Construir y cerrar E2E un agente de inteligencia comercial capaz de transformar señales públicas de contratación y, cuando estén admitidas, señales de otras bibliotecas de oportunidad en oportunidades comerciales verificables para AXIGNAL.

El agente no debe entregar una lista de empresas genéricas. Debe producir un embudo trazable:

```text
organización descubierta
→ cuenta ICP verificada
→ contacto nominativo
→ señal activa
→ horizonte temporal
→ canal verificable
→ siguiente acción
→ OUTREACH_READY
```

El propósito no es maximizar el número bruto de filas. El propósito es maximizar el número de oportunidades comercialmente ejecutables sin inventar personas, idiomas, correos, señales ni fechas.

Este agente capta clientes para AXIGNAL; no sustituye los workspaces del producto, no ejecuta oposiciones y no convierte los módulos informativos en shells independientes.

---

## 2. Diagnóstico vinculante

El punto de partida contiene quince empresas, no dieciséis. Las quince carecen de nombre profesional; sólo dos aportan correo directo; predominan formularios genéricos; trece dependen principalmente de TED; y casi todas las señales son retrospectivas.

Por tanto, la evidencia inicial representa cuentas potencialmente compatibles con el ICP, no quince deals.

### 2.1 Taxonomía obligatoria

```text
ACCOUNT
empresa que vende o puede vender al sector público o actuar en otros universos empresariales cubiertos por AXIGNAL

LEAD
ACCOUNT + persona concreta + canal verificable

OPPORTUNITY
LEAD + necesidad o evento activo + horizonte temporal

DEAL
OPPORTUNITY aceptada + conversación o acción comercial iniciada
```

Ningún proceso, interfaz, exportación, métrica o mensaje podrá emplear una categoría superior si no están presentes todos sus requisitos.

---

## 3. Resultado E2E requerido

El sistema debe producir cuatro conjuntos separados:

```text
ACCOUNTS_DISCOVERED
ICP_QUALIFIED
CONTACT_ENRICHED
OUTREACH_READY
```

No se permite fusionarlos en una única tabla que oculte el grado real de preparación comercial.

### 3.1 Embudo operativo de referencia

```text
300–500 organizaciones brutas
→ 100–150 cuentas ICP verificadas
→ 30–60 oportunidades con trigger
→ 10–20 contactos prioritarios inmediatos
```

Estas cifras son objetivos operativos de investigación, no garantías de conversión ni umbrales que autoricen relajar la calidad.

---

## 4. Principios no negociables

1. Una adjudicación histórica no equivale a una necesidad activa.
2. Un formulario genérico no equivale a un lead.
3. Un correo deducido no equivale a un correo verificado.
4. El país de una persona no prueba su idioma preferido.
5. Una empresa sin persona nominativa no es un lead comercial.
6. Una empresa sin trigger activo no es una oportunidad.
7. Una empresa sin fecha, ventana o evento no es un deal.
8. El agente no puede inventar nombres, idiomas, correos, teléfonos, cargos, fechas ni relaciones societarias.
9. Todo dato material debe conservar fuente, fecha de verificación y confianza.
10. Ningún envío automático queda autorizado por este contrato.
11. Ningún contacto puede realizarse sin política de privacidad, base jurídica y autoridad comercial independientes.
12. Los estados se derivan de reglas deterministas; el modelo puede proponer, pero no promover arbitrariamente una cuenta.
13. Una biblioteca no es un shell.
14. Un país no es un shell.
15. Procurement es `O01`, no un shell adicional.
16. El agente de captación no puede reducir AXIGNAL a TED, O01 o contratación pública.
17. La captación no puede crear una autoridad de evidencia incompatible con AXIGNAL Core.

---

## 5. Alcance funcional

### 5.1 Descubrimiento multifuente

El sistema debe admitir fuentes de estas categorías, siempre sujetas a `F06 Rights, Sources & Provenance` y a las decisiones de admisión aplicables:

- TED Search API:
  - PIN y anuncios previos;
  - CN y licitaciones abiertas;
  - CAN y adjudicaciones;
  - modificaciones;
  - acuerdos marco;
  - DPS;
  - notices de cadena de suministro cuando existan.
- Portales nacionales y regionales.
- Consultas preliminares de mercado.
- Procurement plans.
- Future opportunities.
- Buyer profiles.
- Finalizaciones, vencimientos y renovaciones estimadas.
- Funding & Tenders de la Unión Europea.
- Fuentes corporativas y profesionales públicas.
- Directorios de partners, asociaciones, cámaras, clústeres y consorcios.
- Señales admitidas de `O02–O09` cuando sean relevantes para la captación empresarial.

El conjunto inicial de países debe quedar congelado en configuración antes de ejecutar una campaña real. No se autoriza declarar «cobertura europea» o «cobertura global» por añadir conectores vacíos o superficiales.

La ampliación de países o fuentes no crea nuevos shells.

### 5.2 Expansión recursiva

Cada notice o señal puede generar un pequeño grafo comercial:

```text
comprador o entidad originadora
→ proveedor ganador
→ licitadores no adjudicatarios
→ miembros del consorcio
→ subcontratistas
→ lotes
→ acuerdos marco
→ DPS
→ contratos relacionados
→ contratos anteriores
→ contratos próximos a expirar
→ compradores del mismo CPV o taxonomía
→ socios tecnológicos
→ organizaciones relacionadas por señales de O02–O09
```

La expansión debe preservar procedencia y no convertir relaciones candidatas en relaciones confirmadas.

### 5.3 Resolución y deduplicación

La entidad corporativa debe normalizar:

- nombre legal;
- marca;
- VAT/NIF;
- identificadores nacionales;
- dominio;
- país;
- grupo empresarial;
- subsidiarias;
- variantes lingüísticas;
- fusiones, adquisiciones o cambios de nombre cuando estén acreditados.

La deduplicación no puede basarse únicamente en similitud textual.

Debe reutilizar `F02` cuando esté disponible y no crear una ontología corporativa paralela por país o biblioteca.

### 5.4 Enriquecimiento de contactos

Por cada cuenta ICP se intentarán localizar tres niveles:

```text
OPERATIONAL_USER
Bid Manager / Tender Manager / Proposal Manager o rol operativo equivalente

ECONOMIC_BUYER
Head of Public Sector / Sales Director / Commercial Director o rol económico equivalente

AUTHORITY
CEO / Managing Director / CRO / VP Sales o autoridad equivalente
```

No es obligatorio localizar tres personas para mantener una cuenta en `CONTACT_ENRICHED`, pero `OUTREACH_READY` exige al menos una persona nominativa con cargo relevante y canal verificable.

### 5.5 Idioma

Deben diferenciarse:

```text
company_working_language
website_primary_language
procurement_language
contact_preferred_language
recommended_outreach_language
language_evidence
language_confidence
```

Orden de decisión:

1. idioma explícito del contacto;
2. idioma corporativo predominante;
3. inglés como fallback en empresa internacional;
4. nacionalidad o país nunca como única evidencia.

Debe reutilizar `F05` cuando corresponda. Un idioma o locale no constituye un shell.

### 5.6 Correos y canales

Clases de correo:

```text
NAMED_PUBLIC_EMAIL
ROLE_BASED_EMAIL
TENDER_NOTICE_EMAIL
VERIFIED_CORPORATE_PATTERN
GENERIC_EMAIL
INFERRED_EMAIL
```

Orden de preferencia:

1. correo público nominativo;
2. correo funcional de licitaciones;
3. correo publicado en notice oficial;
4. patrón corporativo comprobado con evidencia suficiente;
5. correo comercial general;
6. formulario web como último recurso.

Un correo inferido debe conservar:

```text
email_status       INFERRED
email_confidence   MEDIUM | LOW
email_send_ready   false
```

Sólo una verificación independiente puede producir:

```text
email_status       VERIFIED
email_send_ready   true
```

Otros canales:

- LinkedIn o perfil profesional;
- teléfono público;
- formulario comercial especializado;
- webinar o conferencia;
- asociación o cámara;
- partner tecnológico;
- consorcio europeo;
- contacto oficial de contratación;
- ruta de introducción cálida.

---

## 6. Modelo de datos mínimo

### 6.1 Organización

```text
company_id
legal_name
brand_name
domain
country
jurisdiction_id
employees_min
employees_max
company_group_id
vat_or_national_id
company_primary_language
company_secondary_languages
website_language
procurement_language
language_source
language_confidence
entity_resolution_status
entity_resolution_confidence
source_refs[]
library_signal_refs[]
first_seen_at
last_verified_at
```

### 6.2 Notice y señal

```text
signal_id
notice_id
library_id
source_id
notice_type
buyer
buyer_id
CPV[]
taxonomy_refs[]
publication_date
deadline
contract_start
contract_end
renewal_estimate
estimated_value
currency
framework_or_dps
lots[]
consortium_members[]
bidders[]
awardees[]
active_trigger_type
active_trigger_description
trigger_start_at
trigger_end_at
trigger_source
trigger_confidence
```

### 6.3 Persona

```text
contact_id
company_id
contact_name
contact_role
contact_level
contact_country
contact_languages[]
contact_preferred_language
contact_linkedin
contact_public_email
contact_public_phone
contact_source
contact_last_verified
contact_confidence
employment_currentness
```

### 6.4 Canal

```text
channel_id
contact_id
channel_type
channel_value
channel_status
channel_confidence
channel_source
last_verified_at
send_ready
```

### 6.5 Calificación comercial

```text
icp_status
icp_segment
b2g_intensity_score
cross_library_relevance[]
active_trigger_status
named_contact_status
relevant_role_status
outreach_language_status
verified_channel_status
personalized_reason
next_action
next_action_due_at
score
state
state_reason
evaluated_at
evaluator_version
evidence_refs[]
```

### 6.6 Contexto arquitectónico obligatorio

```text
product_shell_id       AXIGNAL_OPPORTUNITY_INTELLIGENCE
source_library_id      O01 | O02 | O03 | O04 | O05 | O06 | O07 | O08 | O09
jurisdiction_id        <F01 identifier>
workspace_type         COMMERCIAL_ACQUISITION
```

No se persistirá un `shell_id` distinto por biblioteca, país o fuente.

---

## 7. Máquina de estados

### 7.1 Estados canónicos

```text
ACCOUNTS_DISCOVERED
ICP_QUALIFIED
CONTACT_ENRICHED
OUTREACH_READY
OUTREACH_IN_PROGRESS
OPPORTUNITY_ACCEPTED
DISQUALIFIED
STALE
```

### 7.2 Transiciones mínimas

#### ACCOUNTS_DISCOVERED → ICP_QUALIFIED

Requiere:

- entidad resuelta o suficientemente identificada;
- tamaño y segmento evaluados;
- actividad comercial relevante acreditada;
- fuente, biblioteca y fecha conservadas.

#### ICP_QUALIFIED → CONTACT_ENRICHED

Requiere:

- al menos una persona nominativa;
- cargo actual acreditado;
- fuente profesional o corporativa;
- fecha de verificación.

#### CONTACT_ENRICHED → OUTREACH_READY

Requiere todos:

```text
ICP_MATCH                      PASS
ACTIVE_TRIGGER                 PASS
NAMED_CONTACT                  PASS
CONTACT_ROLE_RELEVANT          PASS
OUTREACH_LANGUAGE              KNOWN
VERIFIED_CONTACT_CHANNEL       PASS
PERSONALIZED_REASON            PASS
NEXT_ACTION                    DEFINED
```

#### OUTREACH_READY → OUTREACH_IN_PROGRESS

Sólo mediante acción comercial explícitamente autorizada y registrada.

#### OUTREACH_IN_PROGRESS → OPPORTUNITY_ACCEPTED

Requiere respuesta, conversación, reunión, solicitud o aceptación verificable. Un envío sin respuesta no constituye un deal aceptado.

### 7.3 Promociones prohibidas

- `ACCOUNTS_DISCOVERED → OUTREACH_READY` sin estados intermedios.
- Promoción por score sin requisitos obligatorios.
- Promoción por decisión libre del LLM.
- Promoción por ausencia de datos.
- Promoción mediante campos sintéticos o fixtures en campaña real.
- Promoción por adjudicación antigua sin trigger actual.
- Promoción basada en una relación cross-library no admitida.
- Promoción basada en una cobertura nacional o global no demostrada.

---

## 8. Scoring explicable

```text
ICP y tamaño                         0–15
Intensidad B2G o relevancia vertical 0–15
Complejidad multinacional            0–10
Trigger activo                       0–20
Renovación, deadline o evento        0–15
Persona nominativa localizada        0–10
Canal directo verificable            0–10
Dolor explícito                       0–5
                                      ─────
Total                                0–100
```

### 8.1 Reglas

- El score no sustituye las condiciones obligatorias.
- Sin trigger activo: no es oportunidad.
- Sin persona nominativa: no es lead.
- Sin fecha o evento: queda en nutrición.
- Toda puntuación debe poder explicarse por componentes y evidencias.
- Los pesos deben ser versionados.
- Cualquier cambio de peso requiere una comparación antes/después sobre un conjunto congelado.
- Las señales de bibliotecas distintas no pueden sumarse como si fueran equivalentes sin regla versionada.
- `UNKNOWN` no puntúa como cero ni como evidencia negativa.

---

## 9. Arquitectura mínima, sin sobreingeniería

### 9.1 Componentes necesarios

1. `SourceAdapter`
2. `NoticeNormalizer`
3. `EntityResolver`
4. `CommercialGraphExpander`
5. `TriggerDetector`
6. `ICPClassifier`
7. `ContactEnricher`
8. `LanguageResolver`
9. `ContactChannelVerifier`
10. `CommercialStateEvaluator`
11. `EvidenceLedger`
12. `CampaignExporter`
13. integración con `LibraryRegistry`
14. resolución de `jurisdiction_id` mediante `F01`
15. resolución de `product_shell_id=AXIGNAL_OPPORTUNITY_INTELLIGENCE`

### 9.2 Componentes no justificados en esta fase

- motor autónomo de envío masivo;
- generación automática de secuencias comerciales;
- scraping indiscriminado de datos personales;
- enriquecimiento de pago sin autorización;
- grafo corporativo universal paralelo a `F02`;
- scoring por aprendizaje automático sin baseline explicable;
- CRM nuevo cuando el almacenamiento actual pueda ampliarse;
- shells adicionales por país, biblioteca, fuente, idioma o segmento;
- abstracciones multiverticales adicionales dentro del agente de captación que no sean necesarias para su E2E.

Esta última limitación no afecta ni puede utilizarse contra:

```text
Shell Registry
Domain Manifest
Workspace Factory
F01–F07
O01–O09
AXIGNAL_OPPORTUNITY_INTELLIGENCE
AXIGNAL_PUBLIC_EMPLOYMENT
```

---

## 10. Contrato de evidencia

Cada hecho material debe conservar:

```text
value
source_url_or_identifier
source_type
library_id
jurisdiction_id
observed_at
last_verified_at
confidence
verification_method
raw_evidence_digest
extractor_version
rights_snapshot_id
```

### 10.1 Valores desconocidos

Debe utilizarse un estado explícito:

```text
UNKNOWN
NOT_FOUND
NOT_APPLICABLE
STALE
CONFLICTING
INFERRED
VERIFIED
```

No se permite convertir `UNKNOWN` en falso, cero, cadena vacía o dato supuesto.

### 10.2 Conflictos

Si dos fuentes discrepan:

- conservar ambas observaciones;
- marcar `CONFLICTING`;
- no seleccionar silenciosamente una;
- definir la regla de autoridad;
- impedir `OUTREACH_READY` si el conflicto afecta identidad, cargo, canal o trigger.

### 10.3 Compatibilidad con Evidence Governance

Cuando el dato provenga de una biblioteca AXIGNAL, debe mantener enlace reversible con:

```text
Evidence Object
→ Candidate Claim
→ estado de admisión
→ Claim Ledger
→ source rights snapshot
```

El agente de captación no puede rebajar un claim rechazado, provisional o contradictorio a hecho comercial verificado.

---

## 11. Privacidad, legalidad y seguridad

Antes de contactar:

- definir finalidad y base jurídica;
- limitarse a datos profesionales públicos pertinentes;
- conservar origen y fecha;
- aplicar minimización;
- disponer de política de supresión;
- impedir el uso de datos personales no necesarios;
- separar investigación de envío;
- no usar correos inferidos hasta validación;
- no automatizar mensajes sin autoridad humana;
- mantener lista de exclusión y opt-out;
- impedir campañas en fuentes o jurisdicciones no autorizadas;
- respetar los estados de `F06` y los kill switches por fuente;
- impedir que un bloqueo legal de una fuente se convierta artificialmente en bloqueo global de todas las bibliotecas o shells.

El contrato técnico no constituye aprobación Legal ni Privacy/Data Rights.

Una aprobación o rechazo se aplica al scope exacto documentado: fuente, jurisdicción, finalidad, retención y uso. No se propagará globalmente sin dependencia material demostrada.

---

## 12. Plan de implementación

### Fase C0 — Baseline, autoridad y contrato

- [ ] Congelar este contrato.
- [ ] Registrar SHA del baseline de `main`.
- [ ] Registrar `AX-GE2E-FINISH-004` como contrato superior.
- [ ] Registrar la arquitectura exacta de dos shells.
- [ ] Probar que Procurement se resuelve como `O01`, no como shell.
- [ ] Probar que país, biblioteca, fuente e idioma no generan shells.
- [ ] Inventariar componentes existentes reutilizables.
- [ ] Localizar el CSV y conservarlo como evidencia histórica.
- [ ] Probar que las quince filas iniciales quedan como cuentas, no deals.
- [ ] Crear fixtures positivos y adversariales.

**Salida:**

```text
AX_CAPTURE_C0_BASELINE_AND_ARCHITECTURE_PASS
```

### Fase C1 — Esquema y estados

- [ ] Implementar tipos, esquema y migración mínima.
- [ ] Implementar máquina de estados determinista.
- [ ] Implementar razones de estado.
- [ ] Impedir promociones incompletas.
- [ ] Preservar unknown/conflicting/stale.
- [ ] Persistir `product_shell_id`, `library_id` y `jurisdiction_id` sin duplicar shells.

**Salida:**

```text
AX_CAPTURE_C1_STATE_MODEL_PASS
```

### Fase C2 — Ingestión y normalización

- [ ] TED PIN/CN/CAN/modificaciones/frameworks/DPS.
- [ ] Contrato común de adapters.
- [ ] Preparar compatibilidad con señales admitidas de O02–O09.
- [ ] Idempotencia.
- [ ] Procedencia.
- [ ] Deduplicación de notices y señales.
- [ ] Presupuesto y rate limiting.
- [ ] Sincronización incremental.
- [ ] Library Registry y rights boundary.

**Salida:**

```text
AX_CAPTURE_C2_MULTISIGNAL_INGESTION_PASS
```

### Fase C3 — Resolución de entidades y grafo comercial

- [ ] Normalización legal y de marca.
- [ ] VAT/NIF e identificadores.
- [ ] Grupos y subsidiarias.
- [ ] Consorcios, licitadores y lotes.
- [ ] Contratos relacionados y vencimientos.
- [ ] No convertir relaciones candidatas en confirmadas.
- [ ] Reutilizar F02 o sus contratos; no crear entity store paralelo por país.

**Salida:**

```text
AX_CAPTURE_C3_ENTITY_GRAPH_PASS
```

### Fase C4 — Trigger e ICP

- [ ] Separar señales retrospectivas y activas.
- [ ] Detectar deadlines, consultas, expansión, contratación y renovación.
- [ ] Admitir triggers procedentes de O02–O09 sólo cuando estén soportados.
- [ ] Clasificar SME/mid-market y enterprise.
- [ ] Implementar scoring explicable.
- [ ] Validar no-promoción sin trigger.

**Salida:**

```text
AX_CAPTURE_C4_TRIGGER_ICP_PASS
```

### Fase C5 — Contactos, idioma y canales

- [ ] Usuario operativo.
- [ ] Comprador económico.
- [ ] Autoridad.
- [ ] Idioma con evidencia.
- [ ] Correos tipados.
- [ ] Canales alternativos.
- [ ] Prohibición de correo inferido como verificado.
- [ ] Fecha de verificación.
- [ ] Reutilización de F05 y de las políticas de privacidad comunes.

**Salida:**

```text
AX_CAPTURE_C5_CONTACT_ENRICHMENT_PASS
```

### Fase C6 — OUTREACH_READY

- [ ] Evaluador determinista.
- [ ] Razón personalizada basada en evidencia.
- [ ] Siguiente acción concreta.
- [ ] Exportación separada por estado.
- [ ] Ningún formulario genérico como contacto suficiente.
- [ ] Ningún envío automático.
- [ ] Ningún claim de shell, país o biblioteca no demostrado.

**Salida:**

```text
AX_CAPTURE_C6_OUTREACH_READY_PASS
```

### Fase C7 — Campaña real controlada

- [ ] Conjunto de países congelado como configuración jurisdiccional, no como shells.
- [ ] Fuentes autorizadas.
- [ ] Bibliotecas utilizadas declaradas.
- [ ] Presupuesto congelado.
- [ ] Dataset sin fixtures.
- [ ] Muestra auditada manualmente.
- [ ] Falsos positivos medidos.
- [ ] Datos personales minimizados.
- [ ] Exportación saneada.
- [ ] Autoridad humana antes de contacto.

**Salida:**

```text
AX_CAPTURE_C7_REAL_CAMPAIGN_PASS
```

### Fase C8 — Cierre E2E

- [ ] Instalación limpia.
- [ ] Migraciones.
- [ ] Ingestión real.
- [ ] Reinicio y persistencia.
- [ ] Reejecución idempotente.
- [ ] Backup, mutación deliberada y restore.
- [ ] Tenant isolation cuando aplique.
- [ ] Exact-head CI.
- [ ] Artifact provenance.
- [ ] Auditoría humana.
- [ ] Prueba de que el agente opera dentro de `AXIGNAL_OPPORTUNITY_INTELLIGENCE`.
- [ ] Prueba negativa de ausencia de shell por país o biblioteca.
- [ ] Prueba de no-fork respecto de AXIGNAL Core.

**Salida final reservada:**

```text
AX_CAPTURE_COMMERCIAL_INTELLIGENCE_E2E_PASS
```

---

## 13. Matriz de pruebas obligatoria

### 13.1 Positivas

- PIN futuro + Bid Manager + correo público + idioma explícito.
- CN abierto + deadline + Tender Manager + LinkedIn verificable.
- Contrato próximo a expirar + responsable comercial + teléfono público.
- Empresa contratando Proposal Manager + expansión geográfica.
- Licitador no adjudicatario + dolor demostrable + contacto nominativo.
- Señal admitida de O02–O09 + trigger activo + persona nominativa + canal verificable.
- Misma empresa descubierta en dos países, resuelta como una entidad con varias jurisdicciones y un solo shell.
- Misma cuenta descubierta por O01 y O04, preservando dos señales de biblioteca sin duplicar la organización.
- Procurement resuelto como `library_id=O01` y `product_shell_id=AXIGNAL_OPPORTUNITY_INTELLIGENCE`.

### 13.2 Adversariales

- adjudicación antigua sin actividad actual;
- empresa con formulario genérico únicamente;
- correo `nombre.apellido@dominio` deducido;
- CEO antiguo;
- perfil profesional sin empresa actual;
- idioma inferido por nacionalidad;
- empresa duplicada por marca y sociedad;
- consorcio tratado como una sola empresa;
- notice duplicado en TED y portal nacional;
- fecha de renovación inventada;
- `UNKNOWN` convertido en cero;
- score alto pero sin trigger;
- score alto pero sin persona;
- correo publicado para el comprador público atribuido al proveedor;
- contacto de prensa tratado como decisor comercial;
- fixture mezclado con campaña real;
- fuente sin derechos admitidos;
- dato conflictivo promocionado a verificado;
- empresa enterprise evaluada con el mismo motion que una SME;
- envío automático desde `OUTREACH_READY`;
- creación de `AXIGNAL_SPAIN`, `AXIGNAL_FRANCE` o cualquier shell por país;
- creación de un shell por O01–O09;
- creación de `AXIGNAL_PROCUREMENT` como tercer shell;
- duplicación de entidades por biblioteca;
- duplicación del Claim Ledger para captación;
- propagación de un blocker legal de TED a bibliotecas sin dependencia material;
- señal de una biblioteca rechazada utilizada para promover `OUTREACH_READY`;
- causalidad cross-library inventada;
- cambio del shell de producto mediante un campo controlado por cliente.

Todos deben fallar de forma explícita y conservar una razón auditable.

---

## 14. Auditoría obligatoria de cada cambio del agente

La auditoría se ejecutará sobre cada commit candidato o PR antes de permitir avance de fase.

### 14.1 Paso A — Identidad exacta

Registrar:

```text
repository
base_branch
base_sha
head_branch
head_sha
changed_files
commits
```

No se audita una descripción verbal; se audita el diff exacto.

### 14.2 Paso B — Correspondencia contractual

Cada archivo cambiado debe mapearse a:

- contrato superior;
- fase;
- requisito;
- prueba;
- salida;
- riesgo;
- shell, biblioteca y jurisdicción afectados.

Un archivo sin justificación contractual se marca:

```text
OUT_OF_SCOPE
```

### 14.3 Paso C — Auditoría semántica

Comprobar:

- taxonomía Account/Lead/Opportunity/Deal;
- estados canónicos;
- reglas obligatorias;
- tratamiento de `UNKNOWN`;
- procedencia;
- confianza;
- currentness;
- no invención;
- no promoción libre por LLM;
- no automatización de envío;
- Procurement clasificado como O01;
- exactamente dos shells en el alcance actual;
- países y bibliotecas tratados como configuración o módulos;
- ausencia de forks de Core, identidad, evidencia y ledger.

### 14.4 Paso D — Auditoría de datos y migraciones

Comprobar:

- migración reversible;
- restricciones e índices;
- claves de deduplicación;
- idempotencia;
- tenant boundaries;
- datos personales;
- retención;
- rollback;
- compatibilidad con registros previos;
- `product_shell_id` server-authoritative;
- `library_id` y `jurisdiction_id` tipados;
- ausencia de tablas duplicadas por país o biblioteca sin justificación contractual.

### 14.5 Paso E — Auditoría de fuentes

Comprobar:

- fuente real;
- biblioteca correspondiente;
- jurisdicción;
- tipo de notice o señal;
- fecha;
- paginación;
- rate limit;
- retries;
- respuestas parciales;
- borrados y modificaciones;
- provenance;
- rights boundary;
- kill switch y blocked scope;
- ausencia de fixtures en evidencia real.

### 14.6 Paso F — Auditoría de lógica comercial

Comprobar:

- trigger activo;
- horizonte temporal;
- persona correcta;
- canal verificable;
- idioma acreditado;
- score explicable;
- segmento;
- siguiente acción;
- clasificación final;
- no doble conteo por señales cross-library;
- no uso de señales rechazadas o provisionales como hechos verificados.

### 14.7 Paso G — Pruebas

Requerir:

- unitarias;
- integración;
- property-based cuando ayude a estados/deduplicación;
- E2E sin fixtures;
- adversariales;
- regresión;
- exact-head;
- fresh install;
- restart;
- backup/restore;
- no-fork;
- no-shell-per-country;
- no-shell-per-library;
- aislamiento y autoridad server-side.

### 14.8 Paso H — Veredicto

Únicos veredictos permitidos:

```text
PASS
PASS_WITH_NON_BLOCKING_FINDINGS
REQUEST_CHANGES
BLOCKED_MISSING_EVIDENCE
OUT_OF_SCOPE
```

No se permite «parece correcto» ni cerrar por número de tests sin revisar su pertinencia.

---

## 15. Criterios de bloqueo inmediato

El auditor debe bloquear el cambio si detecta cualquiera:

- llama deal a una cuenta;
- usa adjudicaciones históricas como trigger activo por defecto;
- acepta formulario genérico como lead terminado;
- inventa o adivina correo y lo marca verificado;
- infiere idioma exclusivamente por país;
- elimina fuente o fecha de verificación;
- permite promoción por LLM sin reglas;
- mezcla fixtures con evidencia real;
- añade envío automático;
- amplía fuentes o países sin contrato;
- captura datos personales innecesarios;
- relaja tests para obtener PASS;
- declara cobertura o efectividad no demostrada;
- cambia scoring sin comparación;
- reescribe estados históricos;
- rompe idempotencia o deduplicación;
- introduce sobreingeniería sin necesidad E2E;
- crea un shell por país, biblioteca, fuente, idioma o segmento;
- implementa Procurement como tercer shell;
- reduce `AXIGNAL_OPPORTUNITY_INTELLIGENCE` a O01/TED;
- omite o contradice `AXIGNAL_PUBLIC_EMPLOYMENT` como segundo shell;
- duplica backend, identidad, Claim Ledger o Evidence Governance;
- permite que el cliente seleccione `product_shell_id`, tenant o autoridad;
- convierte un blocker local de fuente en bloqueo global sin dependencia demostrada;
- modifica la arquitectura multishell sin enmienda humana y contractual.

---

## 16. Formato de informe de auditoría

```markdown
# Audit Report — <HEAD_SHA>

## Verdict
REQUEST_CHANGES

## Governing authority
- AX-GE2E-FINISH-004 v2.0.0
- AX-CAPTURE-E2E-001 v1.1

## Architecture check
- product shells: 2
- AXIGNAL_OPPORTUNITY_INTELLIGENCE: PASS | FAIL
- AXIGNAL_PUBLIC_EMPLOYMENT: PASS | FAIL | NOT_APPLICABLE
- Procurement classified as O01: PASS | FAIL
- shell per country/library: ABSENT | FOUND
- no-fork: PASS | FAIL

## Contract mapping
- C4 / TriggerDetector
- C5 / ContactChannelVerifier

## Material findings
### F1 — Historical award promoted as active trigger
Severity: BLOCKER
Evidence: <file:line>
Contract: §4.1, §7.3, §15
Required correction: ...

## Non-blocking findings
...

## Tests observed
...

## Missing evidence
...

## Allowed next transition
...
```

---

## 17. Auditoría preliminar del estado actual

### 17.1 Fuente inicial

**Resultado: FAIL como lista de deals / PASS como inventario de cuentas.**

Razones:

- quince empresas;
- nombres profesionales vacíos;
- escasos correos directos;
- dependencia excesiva de TED;
- señales predominantemente retrospectivas;
- ausencia de oportunidades abiertas, renovaciones, fechas y responsables nominativos.

### 17.2 Implementación localizada en el repositorio

En la inspección preliminar no se ha localizado una implementación canónica que materialice conjuntamente:

```text
OUTREACH_READY
active_trigger
contact_name
contact_role
recommended_outreach_language
verified_contact_channel
next_action
```

El PR abierto más reciente observado, `#180`, se ocupa de gobernanza del almacenamiento de GitHub Actions. Es trabajo operativo potencialmente válido, pero no implementa este contrato de captación.

Por tanto:

```text
AX_CAPTURE_IMPLEMENTATION_FOUND     false
AX_CAPTURE_CURRENT_PHASE            C0
AX_CAPTURE_E2E                      NOT_STARTED
OUTREACH_READY_PROVEN               false
AUTOMATIC_OUTREACH_AUTHORIZED       false
```

Esta conclusión debe revisarse cuando el agente publique una rama, commit o PR específico de captación.

### 17.3 Estado arquitectónico inicial

La incorporación de esta versión contractual establece:

```text
PRODUCT_SHELLS_REQUIRED                    2
AXIGNAL_OPPORTUNITY_INTELLIGENCE           REQUIRED
AXIGNAL_PUBLIC_EMPLOYMENT                  REQUIRED_AS_SECOND_SHELL
PROCUREMENT                                O01_LIBRARY
SHELL_PER_COUNTRY                          PROHIBITED
SHELL_PER_LIBRARY                          PROHIBITED
CAPTURE_AGENT_PRODUCT_PLACEMENT             AXIGNAL_OPPORTUNITY_INTELLIGENCE
ARCHITECTURE_IMPLEMENTATION_EVIDENCE        PENDING
```

La presencia documental de esta regla no constituye todavía prueba de implementación.

---

## 18. Autoridad y cierre

Un agente puede:

- investigar;
- proponer;
- extraer;
- clasificar provisionalmente;
- calcular scoring;
- preparar una siguiente acción.

Un agente no puede:

- inventar evidencia;
- promover libremente estados;
- declarar un deal;
- decidir base jurídica;
- autorizar contacto;
- enviar comunicaciones;
- declarar éxito comercial;
- cerrar este contrato;
- crear shells adicionales;
- convertir Procurement en shell;
- reducir el shell empresarial a O01/TED;
- sustituir la arquitectura superior.

El cierre requiere:

```text
exact head
+ matriz crítica PASS
+ campaña real sin fixtures
+ muestra humana auditada
+ privacidad y derechos vigentes
+ evidencia de contactos verificables
+ estados deterministas
+ arquitectura de dos shells preservada
+ Procurement clasificado como O01
+ ausencia de shell por país o biblioteca
+ no-fork de Core, identidad, evidencia y ledger
+ cero blockers
```

Hasta entonces:

```text
AX_CAPTURE_COMMERCIAL_INTELLIGENCE_E2E_PASS = NOT_ISSUED
PUBLIC_OUTREACH                              = NOT_AUTHORIZED
MULTISHELL_ARCHITECTURE_IMPLEMENTATION       = NOT_YET_PROVEN
```

---

## 19. Enmienda y aprobación humana

Esta versión `1.1` incorpora la decisión humana vinculante de que AXIGNAL tendrá, en el alcance actual, exactamente dos shells de producto:

```text
1. AXIGNAL_OPPORTUNITY_INTELLIGENCE
2. AXIGNAL_PUBLIC_EMPLOYMENT
```

Y establece expresamente:

```text
Procurement = O01 library
Country = jurisdiction/configuration
Library = module
Workspace = operational surface
Shell = domain-level product experience
```

La integración de este documento en el repositorio no autoriza por sí sola:

- contacto comercial;
- envío automático;
- lanzamiento público;
- despliegue;
- merge;
- claims de cobertura;
- aprobación Legal o Privacy/Data Rights.
