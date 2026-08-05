# AXIGNAL — Contrato canónico de cierre E2E con checklist ejecutable

**Contract ID:** `AX-GE2E-FINISH-003`  
**Versión contractual:** `1.1.0-checklist.1`  
**Fecha de ratificación original:** `2026-08-05T17:00:45+02:00`  
**Fecha de enmienda operativa:** `2026-08-05T20:23:00+02:00`  
**Estado:** `RATIFIED / ACTIVE / BINDING`  
**Autoridad humana:** `Rafael López`  
**Repositorio:** `LowToHi/axignal`  
**Rama de materialización:** `agent/axignal-c0-canonical-reconciliation-v1`  
**Aplicación objetivo:** `AXIGNAL B2G Opportunity Intelligence & Operations v1.0`  
**Resultado contractual:** una aplicación completa, desplegable, cobrable, operable y utilizable de extremo a extremo para contratación pública.

---

## 0. Enmienda vinculante

La autoridad humana ordena sustituir el formato narrativo y los snapshots de avance del contrato por una checklist contractual única y actualizable.

Desde esta versión:

1. este archivo contiene la lista completa de tareas necesarias para alcanzar el E2E contratado;
2. `[ ]` significa tarea pendiente y `[x]` significa tarea cumplida;
3. el progreso se determina exclusivamente contando tareas marcadas, no mediante porcentajes estimados, relatos de avance ni declaraciones informales;
4. cada tarea cumplida debe conservar evidencia verificable;
5. las tareas cumplidas pueden reabrirse si una regresión invalida su evidencia;
6. el ledger debe reflejar el mismo work package y tarea activos;
7. quedan eliminados los snapshots históricos de avance del cuerpo operativo del contrato;
8. los documentos y attestations anteriores se conservan únicamente como audit trail.

```text
HUMAN_AUTHORITY_APPROVAL     APPROVED
APPROVED_BY                  Rafael López
AMENDMENT_EFFECTIVE_AT       2026-08-05T20:23:00+02:00
CONTRACT_STATUS              RATIFIED_ACTIVE
PUBLIC_LAUNCH_AUTHORITY      false
```

---

## 1. Reglas de uso de la checklist

### 1.1 Semántica

```text
[ ]  pendiente: no existe evidencia completa o la evidencia ha quedado invalidada
[x]  cumplida: todos los criterios de la tarea pasan y su evidencia está registrada
```

No existen estados implícitos. Una tarea parcialmente implementada permanece `[ ]`.

### 1.2 Regla para marcar `[x]`

Una tarea sólo puede marcarse `[x]` cuando:

1. todos sus criterios materiales están satisfechos;
2. las pruebas afectadas pasan;
3. la evidencia identifica el SHA ejecutable validado;
4. los jobs, artefactos, manifests o aprobaciones requeridos están registrados;
5. no se ha obtenido el PASS mediante retries, fixtures finales, bypasses o ampliaciones arbitrarias de timeout;
6. no existe una regresión conocida que contradiga el cierre;
7. la modificación de la casilla y el ledger se realizan en el mismo cambio documental o en cambios consecutivos inequívocamente ligados.

### 1.3 Exact-head y actualizaciones documentales

Marcar una casilla en un commit documental no transforma ese commit en evidencia de producto. Cada `[x]` debe señalar el `EVIDENCE_SHA` sobre el que pasó la tarea.

Antes de cerrar un work package se exige una validación exact-head del estado integrado vigente. Antes de P27 se exige una validación exact-head completa que incluya código, configuración, contratos, ledger y manifiesto final.

### 1.4 Reapertura

Una tarea `[x]` vuelve a `[ ]` cuando:

- una regresión material reproduce el fallo;
- cambia su contrato de aceptación;
- el SHA o artefacto queda invalidado;
- el merge introduce una divergencia;
- una autoridad humana, legal, de seguridad o de datos revoca la aceptación.

### 1.5 Orden de ejecución

```text
WP0 → WP1 → WP2 → WP3 → WP4 → WP5 → WP6
```

Dentro de cada work package se ejecutará primero la primera tarea pendiente, salvo dependencia técnica explícita o enmienda humana. No se iniciará un work package posterior para evitar resolver el anterior.

---

## 2. Definición contractual de E2E

AXIGNAL B2G v1.0 sólo estará terminado cuando complete de forma real y persistente:

```text
visitante
→ registro y verificación
→ passkey y sesión revocable
→ organización, tenant, roles, seats y trial
→ fuente oficial admitida
→ ingestión, normalización y recuperación
→ Navigator
→ ResearchRun persistente
→ AXENT con contexto gobernado
→ Evidence Objects
→ Candidate Claims
→ admisión determinista
→ InvestigationContext
→ Opportunity
→ Pursuit
→ Bid Workspace
→ requisitos, evidencias, tareas, hitos, documentos y aprobaciones
→ decisión humana
→ exportación o activación registrada
→ outcome y aprendizaje
→ facturación, renovación, impago y cancelación
→ soporte, observabilidad, backup, restauración y auditoría
→ aceptación privada
→ P27 y autorización humana final
```

No constituye E2E:

- una interfaz sin backend real;
- una demo basada en fixtures;
- una ejecución sin persistencia;
- un buscador que termina antes de Opportunity Operations;
- una respuesta de modelo sin evidencia gobernada;
- una attestation no ligada al SHA;
- un PASS obtenido mediante retry o timeout artificial;
- un cierre declarado únicamente en una rama no fusionada.

---

## 3. Alcance y límites

### 3.1 Alcance obligatorio

```text
AXIGNAL B2G v1.0
= O01 contratación pública
+ fundaciones necesarias
+ investigación y evidencia
+ Opportunity y Bid Workspace
+ billing y Founder Operations
+ producción, seguridad, UX y distribución
+ aceptación privada
+ P27 y autorización humana final
```

### 3.2 Fuera de la ruta crítica

`O02–O09`, nuevas bibliotecas y capacidades futuras no son blockers de este cierre salvo que una dependencia concreta sea materialmente necesaria para O01.

### 3.3 Prohibiciones

Durante el cierre no se permite:

1. crear autoridades paralelas de identidad, tenant, claims, entitlements, tareas o billing;
2. añadir otra base de datos sin imposibilidad material demostrada;
3. introducir Kubernetes, service mesh, streaming o infraestructura no requerida por un fallo observado;
4. crear nuevos root workflows de CI;
5. incorporar O02–O09 a la ruta crítica;
6. refactorizar módulos ajenos al blocker;
7. sustituir integraciones reales por fixtures en gates finales;
8. usar retries para convertir flakiness en PASS;
9. elevar timeouts sin requisito funcional demostrado;
10. mantener varios PR o work packages de cierre simultáneos;
11. declarar cierre canónico antes del merge protegido y smoke post-merge;
12. alterar el contrato para evitar corregir la primera tarea pendiente.

---

## 4. Jerarquía de autoridad

```text
1. Enmienda contractual aprobada por la autoridad humana
2. Este contrato AX-GE2E-FINISH-003
3. Checklist y evidencias registradas en este archivo
4. Ledger docs/roadmap/AXIGNAL_E2E_FINISH_LEDGER.json
5. Código y migraciones del exact HEAD activo
6. Resultado terminal de CI ligado al exact HEAD
7. Attestations y artefactos content-addressed
8. Documentos históricos y conversaciones
```

---

## 5. Panel de progreso contractual

| Work package | Cumplidas | Total | Estado |
|---|---:|---:|---|
| `WP0` Canonicalización C0–C4 | 5 | 12 | `IN_PROGRESS` |
| `WP1` Investigación, AXENT y evidencia real | 0 | 10 | `BLOCKED_BY_WP0` |
| `WP2` O01, Opportunity y Bid Workspace | 0 | 12 | `BLOCKED_BY_WP1` |
| `WP3` Comercial, billing y Founder Operations | 0 | 12 | `BLOCKED_BY_WP2` |
| `WP4` Producción, seguridad, UX y distribución | 0 | 12 | `BLOCKED_BY_WP3` |
| `WP5` Aceptación privada | 0 | 7 | `BLOCKED_BY_WP4` |
| `WP6` P27, release y lanzamiento | 0 | 10 | `BLOCKED_BY_WP5` |
| **TOTAL** | **5** | **75** | **E2E INCOMPLETE** |

```text
ACTIVE_WORK_PACKAGE          WP0
ACTIVE_TASK                  WP0-T05
NEXT_CANONICAL_MARKER        AX_C0_C4_CANONICAL_MAIN_PASS
PUBLIC_LAUNCH                NO_GO
```

El panel se actualizará en el mismo cambio que marque o reabra una tarea. En caso de discrepancia, prevalecen las casillas individuales.

---

# 6. Checklist contractual E2E

## WP0 — Canonicalización del baseline C0–C4

**Objetivo:** obtener un baseline C0–C4 integrado, exact-head, fusionado de forma protegida y reproducible desde `main`.

- [x] **WP0-T01 — Reconciliar C0 como baseline canónico único.**  
  **Cierre:** no existen autoridades divergentes; baseline y contratos apuntan a una única línea de producto.  
  **Evidencia:** `AX_C0_CANONICAL_BASELINE_PASS`.

- [x] **WP0-T02 — Cerrar el Subscriber Shell C1 de extremo a extremo.**  
  **Cierre:** alta de suscriptor, consentimiento, confirmación, gestión y revocación persisten con autoridad server-side.  
  **Evidencia:** `AX_C1_SUBSCRIBER_SHELL_FULL_E2E_PASS`.

- [x] **WP0-T03 — Cerrar identidad, sesión, tenant, seats y trial C2.**  
  **Cierre:** passkey, recuperación, revocación, tenant, roles, seats, trial, límites y aislamiento pasan.  
  **Evidencia:** `AX_C2_IDENTITY_TENANT_TRIAL_PASS`; `EVIDENCE_SHA=2ca1cf0451ff0a1544047a2426cf397dae0bb99a`.

- [x] **WP0-T04 — Cerrar la autoridad de producto C3 de persistencia y migraciones.**  
  **Cierre:** migraciones, tenant-private authority, retención, backup y restore de producto quedan demostrados.  
  **Evidencia:** `AX_C3_PERSISTENCE_MIGRATIONS_RESTORE_PASS`; `EVIDENCE_SHA=8a81d2a417d5645899c3ba50489552bbeb3f829a`; `artifact_id=8913254281`.

- [ ] **WP0-T05 — Cerrar el comparador C3 de ciclos consecutivos 140→142.**  
  **Cierre:** snapshot restaurado en schema 140; equivalencia de datos y autoridad en 140; aplicación determinista de 141–142; equivalencia final de schema, datos y autoridad; hashes materiales preservados; CI afectada PASS.  
  **Evidencia requerida:** job y artefacto C3 PASS sobre el mismo `EVIDENCE_SHA`.  
  **Restricción:** no modificar las migraciones 141–142, no relajar ACL, no ignorar schema drift y no retirar hashes.

- [x] **WP0-T06 — Cerrar el runtime técnico C4 de Research/AXENT.**  
  **Cierre:** recorrido técnico C4, autoridad y persistencia pasan sin sustituir evidencia por fixtures finales.  
  **Evidencia:** `C4_FINAL_RUNTIME_PASS`; `EVIDENCE_SHA=dd119139555e885cc73d24d13e4b7b148797576e`; `job_id=92338125477`.

- [ ] **WP0-T07 — Ejecutar y cerrar la full migration matrix exact-head.**  
  **Cierre:** bootstrap, upgrade paths, replay, backup, restore, retention y migraciones soportadas pasan en toda la matriz requerida.  
  **Evidencia requerida:** run terminal SUCCESS y artefactos ligados al exact HEAD.

- [ ] **WP0-T08 — Ejecutar y cerrar los root gates exact-head.**  
  **Cierre:** `Core`, `Runtime`, `Domain`, `Procurement Admission` y `Remote Pilot Operations` pasan sobre el mismo producto candidato.  
  **Evidencia requerida:** IDs de runs, conclusiones SUCCESS y SHA común.

- [ ] **WP0-T09 — Incorporar el último `main` y resolver sólo conflictos materiales.**  
  **Cierre:** rama actualizada respecto a `main`, sin pérdida de cambios ni ampliación de alcance; pruebas afectadas PASS.  
  **Evidencia requerida:** merge-base, head reconciliado y diff revisado.

- [ ] **WP0-T10 — Dejar el PR contractual listo y protegiblemente fusionable.**  
  **Cierre:** PR no draft, mergeable, checks obligatorios PASS, expected head verificado y cero conversaciones bloqueantes.  
  **Evidencia requerida:** snapshot del PR y `expected_head_sha`.

- [ ] **WP0-T11 — Completar el merge protegido a `main`.**  
  **Cierre:** merge realizado mediante la protección configurada, sin bypass y sobre el head esperado.  
  **Evidencia requerida:** SHA canónico de `main` y registro de merge.

- [ ] **WP0-T12 — Ejecutar smoke post-merge y emitir el marcador WP0.**  
  **Cierre:** instalación/arranque, login, recorrido crítico C0–C4 y persistencia pasan desde `main`; ledger registra el SHA canónico.  
  **Evidencia requerida:** `AX_C0_C4_CANONICAL_MAIN_PASS`.

---

## WP1 — Investigación, AXENT y evidencia real

**Objetivo:** demostrar el recorrido real desde una intención en Navigator hasta un InvestigationContext gobernado y persistente.

- [ ] **WP1-T01 — Admitir al menos una fuente oficial O01 para evidencia real.**  
  **Cierre:** autoridad humana, derechos, alcance, calidad, límites, retención, revocación y kill switch aprobados.

- [ ] **WP1-T02 — Crear un ResearchRun persistente desde Navigator.**  
  **Cierre:** submit real, `runId` durable, redirección canónica `/research-runs/{runId}` y estados server-side.

- [ ] **WP1-T03 — Cerrar el ciclo de worker.**  
  **Cierre:** lease, heartbeat, progreso, reanudación, terminalidad e idempotencia sin doble procesamiento.

- [ ] **WP1-T04 — Recuperar y normalizar evidencia oficial real.**  
  **Cierre:** contenido, metadatos, identificadores, idioma, timestamps y procedencia se preservan sin fixtures finales.

- [ ] **WP1-T05 — Materializar Evidence Objects verificables.**  
  **Cierre:** hash, fuente, ubicación, captura, licencia/derechos, temporalidad y trazabilidad quedan persistidos.

- [ ] **WP1-T06 — Producir Candidate Claims con incertidumbre explícita.**  
  **Cierre:** cada claim referencia evidencia suficiente, conserva contradicciones y no se presenta como hecho admitido.

- [ ] **WP1-T07 — Ejecutar admisión determinista y Claim Ledger.**  
  **Cierre:** reglas independientes del modelo deciden admisión/rechazo; ledger append-only, reproducible y auditable.

- [ ] **WP1-T08 — Construir InvestigationContext y respuesta AXENT gobernada.**  
  **Cierre:** AXENT usa únicamente contexto autorizado, cita evidencia, distingue hechos/hipótesis y mantiene autoridad humana.

- [ ] **WP1-T09 — Probar continuidad, aislamiento y recuperación.**  
  **Cierre:** reload, restart, backup/restore, logout, route protection y cross-tenant preservan o deniegan correctamente el estado.

- [ ] **WP1-T10 — Cerrar el recorrido navegador→investigación completo.**  
  **Cierre:** journey browser real desde login hasta paquete de investigación, sin bypasses y con manifest exact-head.  
  **Evidencia requerida:** `AX_WP1_RESEARCH_EVIDENCE_FULL_E2E_PASS`.

---

## WP2 — O01, Opportunity y Bid Workspace

**Objetivo:** convertir investigación admitida en una operación completa de oportunidad pública hasta outcome y aprendizaje.

- [ ] **WP2-T01 — Cerrar el manifiesto O01 de fuentes, derechos y cobertura.**  
  **Cierre:** países, idiomas, sectores, profundidad histórica, actualización, calidad, lag, límites y fuentes suspendidas quedan declarados.

- [ ] **WP2-T02 — Cerrar ingestión y actualización O01.**  
  **Cierre:** alta inicial, actualización incremental, deduplicación, corrección, revocación, kill switch y rollback pasan.

- [ ] **WP2-T03 — Cerrar descubrimiento O01 en Navigator.**  
  **Cierre:** búsqueda, filtros, relevancia, multilingüismo, disclosure de cobertura y enlaces a evidencia funcionan con datos reales.

- [ ] **WP2-T04 — Crear Opportunity desde InvestigationContext admitido.**  
  **Cierre:** lineage completo, tenant, fuente, claims, elegibilidad no garantizada, estado y auditoría persisten.

- [ ] **WP2-T05 — Implementar el ciclo de vida Pursuit.**  
  **Cierre:** qualify, watch, pursue, hold, no-bid, won, lost y archived tienen transiciones autorizadas y auditables.

- [ ] **WP2-T06 — Cerrar Requirements, Evidence y WorkItems del Bid Workspace.**  
  **Cierre:** requisitos, evidencias, gaps, tareas, responsables, prioridades y dependencias funcionan server-side.

- [ ] **WP2-T07 — Cerrar Milestones, Documents, Comments y colaboración.**  
  **Cierre:** hitos, versiones documentales, comentarios, asignaciones y concurrencia preservan integridad y tenant isolation.

- [ ] **WP2-T08 — Cerrar Decision y Approval con autoridad humana.**  
  **Cierre:** bid/no-bid y aprobaciones materiales no pueden ser ejecutadas autónomamente por el modelo.

- [ ] **WP2-T09 — Cerrar exportación y SubmissionOrActivationRecord.**  
  **Cierre:** exportación reproducible, registro de activación/envío, actor, timestamp, versión y audit trail persisten.

- [ ] **WP2-T10 — Cerrar Outcome y Learning.**  
  **Cierre:** resultado, razón, feedback y aprendizaje tenant-private se registran sin contaminar autoridad global.

- [ ] **WP2-T11 — Probar aislamiento, retención, eliminación y restauración O01.**  
  **Cierre:** RLS, IDOR/BOLA, tombstones, legal hold, purge y restore preservan el contrato.

- [ ] **WP2-T12 — Cerrar el E2E O01 completo en UI.**  
  **Cierre:** fuente real→Navigator→investigación→Opportunity→Pursuit→Bid Workspace→decisión→registro→outcome funciona en navegadores, móvil y teclado.  
  **Evidencia requerida:** `AX_WP2_O01_BID_WORKSPACE_FULL_E2E_PASS`.

---

## WP3 — Comercial, billing y Founder Operations

**Objetivo:** demostrar que AXIGNAL puede conceder trial, cobrar, renovar, restringir, cancelar, reconciliar y operar clientes de forma auditable.

- [ ] **WP3-T01 — Congelar price book y paquetes server-side.**  
  **Cierre:** Trial, Professional, Team y Enterprise tienen precio/quote, seats, límites, features, impuestos y versión inequívocos.

- [ ] **WP3-T02 — Cerrar trial y economía de uso.**  
  **Cierre:** READY→ACTIVE→EXPIRED, siete días, budgets transaccionales, concurrencia y read-only final pasan.

- [ ] **WP3-T03 — Cerrar seats, roles y entitlements.**  
  **Cierre:** reservas, altas, bajas, límites Professional/Team, cambios de rol y revocación se aplican server-side.

- [ ] **WP3-T04 — Completar checkout y alta real en Stripe sandbox.**  
  **Cierre:** customer, price, checkout/subscription, tenant binding, invoice y entitlement inicial quedan reconciliados.

- [ ] **WP3-T05 — Completar renovación e invoice paid.**  
  **Cierre:** ciclo renovado, periodo, factura, pago, ledger y continuidad de acceso coinciden.

- [ ] **WP3-T06 — Completar impago y dunning.**  
  **Cierre:** payment failure, retries propios de Stripe, grace policy, notificación, restricción y recuperación son deterministas.

- [ ] **WP3-T07 — Completar upgrade, downgrade, cancelación y reactivación.**  
  **Cierre:** prorrateo/política, effective dates, seats, entitlements y auditoría son correctos.

- [ ] **WP3-T08 — Cerrar webhooks y reconciliación.**  
  **Cierre:** firma, replay denial, idempotencia, eventos duplicados/fuera de orden, backfill y reconciliación manual pasan.

- [ ] **WP3-T09 — Cerrar refunds, disputes, credit notes e invoices.**  
  **Cierre:** cada mutación tiene autoridad tipada, estado durable y trazabilidad financiera.

- [ ] **WP3-T10 — Cerrar Founder Operations de Growth y Customers/Billing.**  
  **Cierre:** SEO, páginas, alerts, CRM, customers, trials y billing tienen controles reales o aparecen explícitamente bloqueados/read-only.

- [ ] **WP3-T11 — Cerrar Founder Operations de Risk, Abuse, Sources y Coverage.**  
  **Cierre:** decisiones, revisiones, fuentes, derechos, cobertura, consentimiento y eliminación tienen autoridad server-side y audit.

- [ ] **WP3-T12 — Cerrar Founder Operations de Platform y soporte.**  
  **Cierre:** queues, workers, SLO, incidents, DR, flags, settings, audit y soporte operan sin controles simulados.  
  **Evidencia requerida:** `AX_WP3_COMMERCIAL_FOUNDER_OPS_FULL_E2E_PASS`.

---

## WP4 — Producción, seguridad, UX y distribución

**Objetivo:** obtener un artefacto reproducible, seguro, operable y desplegable en producción sin depender del checkout de desarrollo.

- [ ] **WP4-T01 — Crear distribución reproducible e instalable.**  
  **Cierre:** builds independientes, imágenes, bundle, checksums y SBOM reproducibles; fresh install sin checkout.

- [ ] **WP4-T02 — Cerrar despliegue de producción.**  
  **Cierre:** VPS, dominio, TLS, DNS, configuración, secretos y rollback quedan versionados y documentados sin secretos en artefactos.

- [ ] **WP4-T03 — Endurecer runtime y persistencia.**  
  **Cierre:** usuarios no-root, redes mínimas, healthchecks, `pull_policy`, persistencia tras restart y cero bind mounts de desarrollo.

- [ ] **WP4-T04 — Cerrar identidad, RBAC y aislamiento de producción.**  
  **Cierre:** sesiones, recuperación, roles, tenant resolution, IDOR/BOLA y cross-tenant pasan bajo configuración productiva.

- [ ] **WP4-T05 — Cerrar seguridad web, red y agente.**  
  **Cierre:** CSRF, CORS, replay, rate limits, SSRF, DNS rebinding, prompt injection, egress y tool permissions pasan.

- [ ] **WP4-T06 — Cerrar supply chain y vulnerabilidades.**  
  **Cierre:** dependencias, imágenes, firmas/checksums, secrets scan y vulnerabilidades tienen cero hallazgos críticos explotables.

- [ ] **WP4-T07 — Cerrar rendimiento, carga, soak y capacidad.**  
  **Cierre:** SLO, concurrencia, colas, latencias, capacidad, costes y límites se demuestran con carga representativa.

- [ ] **WP4-T08 — Cerrar observabilidad, alertas e incident response.**  
  **Cierre:** logs, métricas, trazas, alertas accionables, runbooks, escalado, kill switches y postmortem template están operativos.

- [ ] **WP4-T09 — Cerrar backup, restauración, rollback y DR.**  
  **Cierre:** RPO/RTO, backups cifrados, restore limpio, mutación/restore, rotación y recuperación desde proceso fresco pasan.

- [ ] **WP4-T10 — Cerrar privacidad, legal, consentimiento y derechos.**  
  **Cierre:** términos, privacidad, DPA cuando aplique, cookies, email consent, retención, exportación, eliminación y source rights están aprobados.

- [ ] **WP4-T11 — Cerrar UX/UI y accesibilidad del producto terminado.**  
  **Cierre:** recorridos canónicos, estados vacíos/error/carga, copy veraz, responsive, teclado, lectores, contraste y navegadores soportados pasan.

- [ ] **WP4-T12 — Ejecutar smoke productivo y gate de release técnico.**  
  **Cierre:** install→bootstrap→login→O01 E2E→billing sandbox→backup/restore→logout funciona en el artefacto desplegado.  
  **Evidencia requerida:** `AX_WP4_PRODUCTION_SECURITY_UX_DISTRIBUTION_PASS`.

---

## WP5 — Aceptación privada sobre producto terminado

**Objetivo:** validar el producto completo con organizaciones expresamente admitidas, sin rebajar el alcance ni presentarlo como lanzamiento público.

- [ ] **WP5-T01 — Desplegar un release candidate completo para aceptación privada.**  
  **Cierre:** mismo artefacto, configuración y manifiesto que se propone para release, con límites visibles.

- [ ] **WP5-T02 — Admitir organizaciones y usuarios de aceptación.**  
  **Cierre:** identidad, términos, roles, seats, soporte, billing si aplica, revocación y tratamiento de datos quedan autorizados.

- [ ] **WP5-T03 — Completar el recorrido de valor con usuarios reales.**  
  **Cierre:** usuarios externos ejecutan fuente→investigación→Opportunity→Bid Workspace→decisión→outcome sin asistencia que oculte defectos.

- [ ] **WP5-T04 — Obtener evidencia comercial controlada.**  
  **Cierre:** al menos una relación privada de aceptación pagada o contractualmente comprometida sobre el producto terminado, con valor entregado y límites declarados.

- [ ] **WP5-T05 — Probar soporte y operación durante uso real.**  
  **Cierre:** incidencias, consultas, tiempos de respuesta, auditoría, recuperación y revocación funcionan con carga real de aceptación.

- [ ] **WP5-T06 — Resolver findings materiales y repetir journeys afectados.**  
  **Cierre:** cero findings abiertos de severidad crítica o bloqueante; regresión completa sobre el RC corregido.

- [ ] **WP5-T07 — Emitir aceptación privada humana.**  
  **Cierre:** resultados, limitaciones, soporte, valor, pricing y riesgos son revisados por la autoridad humana.  
  **Evidencia requerida:** `AX_WP5_PRIVATE_ACCEPTANCE_PASS`.

---

## WP6 — P27, release candidate y lanzamiento

**Objetivo:** ligar toda la evidencia a un único SHA, aprobar el release y habilitar únicamente las autoridades expresamente concedidas.

- [ ] **WP6-T01 — Congelar alcance y SHA del release candidate final.**  
  **Cierre:** código, configuración, migraciones, contratos, price book y assets quedan content-addressed.

- [ ] **WP6-T02 — Construir el manifiesto P27.**  
  **Cierre:** todas las tareas `[x]`, evidencias, digests, runs, artefactos, approvals, limitaciones y rollback están ligados al RC.

- [ ] **WP6-T03 — Ejecutar la matriz exact-head final completa.**  
  **Cierre:** todos los root gates y suites críticas pasan sobre el mismo SHA sin retries ni bypasses.

- [ ] **WP6-T04 — Revalidar instalación, upgrade, persistencia y DR del artefacto final.**  
  **Cierre:** fresh install, bootstrap, upgrade soportado, restart, backup, mutation, restore y rollback pasan desde proceso fresco.

- [ ] **WP6-T05 — Completar reaceptación de seguridad, privacidad, legal y accesibilidad.**  
  **Cierre:** threat model actualizado, cero críticos, derechos O01, consentimiento, identidad, abuso, UX y accesibilidad aprobados.

- [ ] **WP6-T06 — Completar reconciliación comercial final.**  
  **Cierre:** trial, plans, seats, Stripe sandbox, invoices, renewal, impago, cancellation, webhooks, entitlements y Founder Ops coinciden.

- [ ] **WP6-T07 — Completar el journey O01 productivo final.**  
  **Cierre:** usuario real y fuente oficial recorren toda la cadena E2E bajo el RC, con auditoría y recuperación.

- [ ] **WP6-T08 — Fusionar, etiquetar y publicar el release técnico.**  
  **Cierre:** protected merge, tag/version, imágenes/bundle, SBOM, checksums, notas y rollback corresponden al mismo SHA.

- [ ] **WP6-T09 — Ejecutar smoke post-deploy y confirmar operabilidad.**  
  **Cierre:** salud, login, investigación, Bid Workspace, billing, email, observabilidad, backup y soporte funcionan en producción.

- [ ] **WP6-T10 — Obtener autorización humana final y emitir el cierre E2E.**  
  **Cierre:** la autoridad humana aprueba el digest P27 y decide explícitamente qué modos se habilitan.  
  **Evidencia requerida:** `AXIGNAL_E2E_COMPLETE`; disposición `ACCEPTED_FOR_PUBLIC_LAUNCH` o `NO_GO`.

---

## 7. Condiciones de parada

Se detendrá la progresión y se reabrirá la tarea afectada ante:

- pérdida o corrupción de datos;
- aislamiento tenant fallido;
- autenticación o recuperación insegura;
- claim no trazable presentado como hecho;
- fuente sin autoridad o derechos;
- mutación externa autónoma;
- cobro incorrecto;
- restauración no demostrada;
- vulnerabilidad crítica explotable;
- recorrido canónico roto;
- accesibilidad que impida la tarea principal;
- manifiesto no ligado al SHA desplegado.

No se detendrá por bibliotecas O02–O09, mejoras cosméticas, dashboards auxiliares, abstracciones futuras, integraciones no contratadas, warnings no materiales o métricas que sólo puedan existir después del lanzamiento.

---

## 8. Ledger obligatorio

El estado máquina se mantiene en:

```text
docs/roadmap/AXIGNAL_E2E_FINISH_LEDGER.json
```

El ledger debe reflejar:

- `contract_id` y versión;
- `active_work_package`;
- `active_task`;
- rama, PR y exact HEAD;
- estados WP0–WP6;
- blocker material;
- transición permitida;
- evidencia y artefactos;
- autoridad de lanzamiento;
- última enmienda humana.

En caso de discrepancia, se corrige el ledger; no se crea otro roadmap operativo paralelo.

---

## 9. Autoridades reservadas

Hasta completar WP6 y recibir aprobación humana explícita:

```text
PUBLIC_LAUNCH_AUTHORIZED    false
COMMERCIAL_LIVE_MODE        false
STRIPE_LIVE_MODE            false
PUBLIC_SIGNUP               false
PRODUCTION_SOURCE_ADMISSION false
GLOBAL_COVERAGE_CLAIM       false
AUTONOMOUS_EXTERNAL_ACTIONS false
```

La ejecución de este contrato no autoriza por sí sola el lanzamiento.

---

## 10. Firma

```text
HUMAN_AUTHORITY_APPROVAL     APPROVED
APPROVED_BY                  Rafael López
CONTRACT_ID                  AX-GE2E-FINISH-003
CONTRACT_VERSION             1.1.0-checklist.1
CONTRACT_STATE               ACTIVE_BINDING
ACTIVE_WORK_PACKAGE          WP0
ACTIVE_TASK                  WP0-T05
NEXT_CANONICAL_MARKER        AX_C0_C4_CANONICAL_MAIN_PASS
PUBLIC_LAUNCH                NO_GO
```

Este contrato se completa únicamente cuando las 75 tareas están `[x]`, el manifiesto P27 está ligado al SHA final y la autoridad humana emite `AXIGNAL_E2E_COMPLETE`.
