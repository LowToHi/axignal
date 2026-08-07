# AXIGNAL — Contrato canónico de cierre E2E con checklist ejecutable

> **SUPERSEDED_BY:** AX-GE2E-FINISH-004 v2.0.0
> **SUPERSESSION_DATE:** 2026-08-07
> **HISTORICAL_AUDIT_RECORD:** PRESERVED
> **ACTIVE_EXECUTION_AUTHORITY:** NO
>
> Este documento queda conservado íntegramente como registro histórico y de auditoría.
> No posee autoridad de ejecución activa. Las explicaciones sobre por qué WP1-T01
> (admisión de fuente O01 con decisión humana Legal/Privacy) bloqueaba el avance
> de los work packages posteriores bajo este contrato se conservan sin reescritura.

**Contract ID:** `AX-GE2E-FINISH-003`  
**Versión contractual:** `1.1.0-checklist.4`  
**Fecha de ratificación original:** `2026-08-05T17:00:45+02:00`  
**Fecha de enmienda operativa:** `2026-08-06T18:31:34+02:00`  
**Estado:** `RATIFIED / ACTIVE / BINDING`  
**Autoridad humana:** `Rafael López`  
**Repositorio:** `LowToHi/axignal`  
**Rama de materialización:** `agent/axignal-wp0-post-merge-image-ref-repair`  
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
CONTROL_UPDATE_AT            2026-08-06T18:31:34+02:00
CONTRACT_STATUS              RATIFIED_ACTIVE
PUBLICATION_STRATEGY         RELEASE_THEN_ITERATE
CONTROLLED_PUBLIC_DEPLOYMENT true
E2E_COMPLETION_CLAIM         false
```

La actualización `1.1.0-checklist.4` conserva la estrategia aprobada de publicación controlada seguida de auditorías E2E, revisión humana e iteración. Registra además el merge controlado de PR `#177` en `main`, el fallo material observado por el smoke post-merge y la reparación acotada activa en PR `#179`.

La ausencia de branch protection o rulesets no bloquea la ejecución y permanece como hardening de repositorio diferido a `WP4-T06`.

Esta enmienda no relaja los controles técnicos del merge. Mientras `main` siga sin protección, todo merge deberá cumplir simultáneamente:

1. PR no draft y mergeable;
2. cero requested changes o conversaciones bloqueantes;
3. root gates exact-head terminales y verdes;
4. `expected_head_sha` reconsultado inmediatamente antes del merge;
5. merge mediante API, sin force push ni actualización directa del ref;
6. registro del SHA canónico y smoke post-merge;
7. reapertura inmediata ante regresión material.

La publicación controlada no equivale a declarar `AXIGNAL_E2E_COMPLETE`, ni habilita por sí sola Stripe live, claims globales o acciones externas autónomas.

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
11. declarar cierre canónico antes del merge controlado exact-head y smoke post-merge;
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
| `WP0` Canonicalización C0–C4 | 11 | 12 | `POST_MERGE_RELEASE_REPAIR_IN_PROGRESS` |
| `WP1` Investigación, AXENT y evidencia real | 9 | 10 | `9_COMPLETE_1_BLOCKED_BY_HUMAN_LEGAL_PRIVACY_AUTHORITY` |
| `WP2` O01, Opportunity y Bid Workspace | 0 | 12 | `BLOCKED_BY_WP1` |
| `WP3` Comercial, billing y Founder Operations | 0 | 12 | `BLOCKED_BY_WP2` |
| `WP4` Producción, seguridad, UX y distribución | 0 | 12 | `BLOCKED_BY_WP3` |
| `WP5` Aceptación privada | 0 | 7 | `BLOCKED_BY_WP4` |
| `WP6` P27, release y lanzamiento | 0 | 10 | `BLOCKED_BY_WP5` |
| **TOTAL** | **20** | **75** | **E2E INCOMPLETE** |

```text
ACTIVE_WORK_PACKAGE          WP0
ACTIVE_TASK                  WP0-T12
ACTIVE_BRANCH                agent/axignal-wp0-post-merge-image-ref-repair
ACTIVE_PULL_REQUEST          179
CANONICAL_MAIN_SHA           ccac72e286d778ab0187e447f45064d3c4d2d776
LAST_VALIDATED_PRODUCT_SHA   90edfb1e0697ced0e0b4eb90d7f18d93f4661c7f
CURRENT_REPAIR_HEAD          RESOLVE_FROM_PR_HEAD_AT_EXECUTION
TECHNICAL_VALIDATION         EXACT_HEAD_REVALIDATION_PENDING
ACTIVE_BLOCKER               AX-CLOSE-BLK-006_CROSS_DAEMON_IMAGE_LOOKUP
WP0_T12_STATUS               REPAIR_PR_179_IN_VALIDATION
NEXT_CANONICAL_MARKER        AX_C0_C4_CANONICAL_MAIN_PASS
PUBLIC_DEPLOYMENT            AUTHORIZED_RELEASE_THEN_ITERATE
```

El panel se actualizará en el mismo cambio que marque o reabra una tarea. En caso de discrepancia, prevalecen las casillas individuales.

---
# 6. Checklist contractual E2E

## WP0 — Canonicalización del baseline C0–C4

**Objetivo:** obtener un baseline C0–C4 integrado, exact-head, fusionado de forma controlada y reproducible desde `main`.

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

- [x] **WP0-T05 — Cerrar el comparador C3 de ciclos consecutivos 140→142.**  
  **Cierre:** snapshot restaurado en schema 140; equivalencia de datos y autoridad en 140; aplicación determinista de 141–142; equivalencia final de schema, datos y autoridad; hashes materiales preservados; CI afectada PASS.  
  **Evidencia:** `EVIDENCE_SHA=316f34d0ec3c2bc1fc91e0fa2494840a5aa8e243`; `run_id=31092162860`; `job_id=92585538939`; `artifact_id=8963978249`; `digest=sha256:e78c14cbf9e5480a0b66e1c8214a80250604c5b6dd1370733fb8f156c01f73be`; `same_schema_140_equivalence=PASS`; `deterministic_141_142_replay=PASS`; `final_authority_contraction=PASS`; `consecutive_cycle_comparator=PASS`.  
  **Restricción preservada:** migraciones 141–142 intactas, ACL no relajada, schema drift no ignorado y hashes materiales conservados.

- [x] **WP0-T06 — Cerrar el runtime técnico C4 de Research/AXENT.**  
  **Cierre:** recorrido técnico C4, autoridad y persistencia pasan sin sustituir evidencia por fixtures finales.  
  **Evidencia:** `C4_FINAL_RUNTIME_PASS`; `EVIDENCE_SHA=dd119139555e885cc73d24d13e4b7b148797576e`; `job_id=92338125477`.

- [x] **WP0-T07 — Ejecutar y cerrar la full migration matrix exact-head.**  
  **Cierre:** bootstrap, upgrade paths, replay, backup, restore, retention y migraciones soportadas pasan en toda la matriz requerida.  
  **Evidencia:** `EVIDENCE_SHA=316f34d0ec3c2bc1fc91e0fa2494840a5aa8e243`; `run_id=31092162860`; `job_id=92585538939`; `artifact_id=8963978249`; `digest=sha256:e78c14cbf9e5480a0b66e1c8214a80250604c5b6dd1370733fb8f156c01f73be`; conclusión `SUCCESS`.

- [x] **WP0-T08 — Ejecutar y cerrar los root gates exact-head.**  
  **Cierre:** `Core`, `Runtime`, `Domain`, `Procurement Admission` y `Remote Pilot Operations` pasan sobre el mismo producto candidato.  
  **Evidencia:** SHA común `316f34d0ec3c2bc1fc91e0fa2494840a5aa8e243`; `Core=31092164195 SUCCESS`; `Runtime=31092162860 SUCCESS`; `Domain=31092161635 SUCCESS`; `Procurement Admission=31092161086 SUCCESS`; `Remote Pilot Operations=31092162583 SUCCESS`.

- [x] **WP0-T09 — Incorporar el último `main` y resolver sólo conflictos materiales.**  
  **Cierre:** rama actualizada respecto a `main`, sin pérdida de cambios ni ampliación de alcance; pruebas afectadas PASS.  
  **Evidencia:** `MAIN_SHA=6091795f79aec19c9dcbac71bb8b6b19877f101b`; `MERGE_BASE=6091795f79aec19c9dcbac71bb8b6b19877f101b`; `RECONCILED_HEAD=316f34d0ec3c2bc1fc91e0fa2494840a5aa8e243`; comparación `ahead_by=983`, `behind_by=0`; commit `merge(main): reconcile latest storage governance baseline`; cinco root gates exact-head `SUCCESS`.

- [x] **WP0-T10 — Dejar el PR contractual listo para merge controlado exact-head.**  
  **Cierre:** PR no draft, mergeable, checks obligatorios PASS, expected head verificado y cero conversaciones bloqueantes.  
  **Evidencia vigente:** `PR=177`; `EVIDENCE_SHA=90edfb1e0697ced0e0b4eb90d7f18d93f4661c7f`; `draft=false`; `mergeable=true`; `blocking_requested_changes=0`; `Core=31113947505 SUCCESS`; `Runtime=31113950967 attempt 2 SUCCESS`; `Domain=31113954472 SUCCESS`; `Core gate job=92660535386 SUCCESS`; `Runtime gate job=92662147571 SUCCESS`; `Domain gate job=92659174165 SUCCESS`; fallo inicial de infraestructura `job=92660034439` anterior a checkout, clasificado y recuperado sin cambio de código ni criterios.  
  **Repair acotado:** preservación de identidad de imagen Docker local inmutable durante `save/load/deploy`; sin registry, credenciales, infraestructura o autoridad de producto nuevas.

- [x] **WP0-T11 — Completar el merge controlado exact-head a `main`.**  
  **Cierre:** merge realizado sobre el head reconsultado, con PR no draft y mergeable, root gates verdes y sin force push ni mutación directa del ref.  
  **Evidencia:** `PR=177`; `EXPECTED_HEAD_SHA=c75cd325f74f281f009264b87a050b1cf866face`; `CANONICAL_MAIN_SHA=ccac72e286d778ab0187e447f45064d3c4d2d776`; merge API `SUCCESS`; commit firmado y verificado por GitHub; parent de producto `c75cd325f74f281f009264b87a050b1cf866face`; `main` avanzó sin force push ni actualización directa del ref.  
  **Riesgo aceptado:** `main.protected=false`; issue `#176` permanece como hardening no bloqueante de `WP4-T06`.

- [ ] **WP0-T12 — Ejecutar smoke post-merge y emitir el marcador WP0.**  
  **Cierre:** instalación/arranque, login, recorrido crítico C0–C4 y persistencia pasan desde `main`; ledger registra el SHA canónico.  
  **Estado exacto:** `POST_MERGE_RELEASE_FAILED / BOUNDED_REPAIR_IN_PROGRESS`; `CANONICAL_MAIN_SHA=ccac72e286d778ab0187e447f45064d3c4d2d776`; `RUN_ID=31117419963`; `JOB_ID=92670463520`; fallo en `Deploy with rollback armed` después de build, checksum, SSH y transferencia correctos; la ruta externa y la evidencia final no se ejecutaron.  
  **Fallo observado:** `Error response from daemon: No such image: sha256:7945ce0aa266ca7f14003a3401afa2d581dff3deb0d384fecb769829d7636ffc`.  
  **Repair vigente:** `PR=179`; rama `agent/axignal-wp0-post-merge-image-ref-repair`; usar la etiqueta local determinista contenida en el archive como lookup, verificar que resuelve al ID inmutable esperado, mantener `pull_policy: never` y comprobar que el contenedor usa exactamente ese ID.  
  **Evidencia requerida:** `AX_C0_C4_CANONICAL_MAIN_PASS`.

### Registro operativo exacto del repair post-merge

```text
ORIGINAL_CANONICAL_MAIN_SHA          fae293b9f2c6cc1ebfffd2302f3ce6ddcfef00c2
FIRST_FAILED_POST_MERGE_RUN          31097383391
FIRST_FAILED_POST_MERGE_JOB          92602528596
FIRST_OBSERVED_FAILURE               AXIGNAL_LANDING_IMAGE_REPOSITORY missing
FIRST_REPAIR_PULL_REQUEST            177
FIRST_REPAIR_EXECUTABLE_EVIDENCE_SHA 90edfb1e0697ced0e0b4eb90d7f18d93f4661c7f
CONTROLLED_MERGE_EXPECTED_HEAD       c75cd325f74f281f009264b87a050b1cf866face
CANONICAL_MAIN_SHA                   ccac72e286d778ab0187e447f45064d3c4d2d776
CONTROLLED_MERGE                     SUCCESS
POST_MERGE_RELEASE_RUN               31117419963 FAILURE
POST_MERGE_RELEASE_JOB               92670463520 FAILURE
POST_MERGE_FAILURE_STEP              Deploy with rollback armed
POST_MERGE_OBSERVED_FAILURE          No such image: sha256:7945ce0aa266ca7f14003a3401afa2d581dff3deb0d384fecb769829d7636ffc
BUILD_IMAGE_ID                       sha256:7945ce0aa266ca7f14003a3401afa2d581dff3deb0d384fecb769829d7636ffc
BUNDLE_CHECKSUM                      PASS
SSH_HOST_PINNING                     PASS
TRANSFER_EXACT_BUNDLE                PASS
EXTERNAL_ROUTE_SMOKE                 NOT_EXECUTED
FINAL_DEPLOYMENT_EVIDENCE            NOT_EMITTED
CURRENT_REPAIR_PULL_REQUEST          179
CURRENT_REPAIR_BRANCH                agent/axignal-wp0-post-merge-image-ref-repair
CURRENT_REPAIR_HEAD                  RESOLVE_FROM_PR_HEAD_AT_EXECUTION
CURRENT_REPAIR_SCOPE                 verified local tag lookup bound to immutable image ID
MAIN_PROTECTION                      false ACKNOWLEDGED_RISK
DEFERRED_HARDENING_ISSUE             176
DEFERRED_HARDENING_TASK              WP4-T06
MERGE_AUTHORITY                      GRANTED_BY_HUMAN_AMENDMENT
```

---

## WP1 — Investigación, AXENT y evidencia real

**Objetivo:** demostrar el recorrido real desde una intención en Navigator hasta un InvestigationContext gobernado y persistente.

- [ ] **WP1-T01 — Admitir al menos una fuente oficial O01 para evidencia real.**  
  **Cierre:** autoridad humana, derechos, alcance, calidad, límites, retención, revocación y kill switch aprobados.  
  **Estado exacto:** `BLOCKED_BY_HUMAN_LEGAL_PRIVACY_AUTHORITY`; el runtime técnico de `src_ted_search_api_v3` está ADMITTED en el registro de fuentes con `COMMERCIAL_REUSE_WITH_ATTRIBUTION` y kill switch operativo, y el E2E real contra `api.ted.europa.eu` pasa; pero `legal_decision=MISSING` y `privacy_data_rights_decision=MISSING` en `data/acceptance/approvals/AX-LIB-O01-legal-privacy-approval-request.v0.1.json` (`blocking_reasons`: "No human signature is present", "No lawful-basis or retention decision has been supplied"). No simulable en local.

- [x] **WP1-T02 — Crear un ResearchRun persistente desde Navigator.**  
  **Cierre:** submit real, `runId` durable, redirección canónica `/research-runs/{runId}` y estados server-side.  
  **Evidencia:** E2E local real contra Postgres+Valkey: `POST /v1/research-runs` → 202 `{research_run_id, state:QUEUED, queue_delivery:PUBLISHED, synthetic:false}`; `GET /v1/research-runs/{id}` → 200 con vista server-side completa; journey browser real (passkey → Navigator submit → API real → redirect canónico → polling) PASS en `EVIDENCE_SHA=5b6001b`. El BFF traduce el context del subscriber al contrato `ctx_` del API (fix 5b6001b).

- [x] **WP1-T03 — Cerrar el ciclo de worker.**  
  **Cierre:** lease, heartbeat, progreso, reanudación, terminalidad e idempotencia sin doble procesamiento.  
  **Evidencia:** implementado en `EVIDENCE_SHA=299cf73` — `ValkeyResearchQueue.claim/renew_lease/release/recover_expired_leases` con lease hash en Valkey, ownership enforced, reanudación exacta de leases expirados (crash recovery), `ResearchWorker.run_once_leased` con heartbeat thread y release terminal en todos los caminos; 3 tests nuevos de contrato; simulación real contra Valkey: claim → crash → expiración → recover=1 → re-claim por otro worker → release → 0 leases colgados; worker real con TED live completó el run (COMPLETED, 12 evidence, 12 canonical).

- [x] **WP1-T04 — Recuperar y normalizar evidencia oficial real.**  
  **Cierre:** contenido, metadatos, identificadores, idioma, timestamps y procedencia se preservan sin fixtures finales.  
  **Evidencia:** worker con `AXIGNAL_TED_LIVE_SOURCES_ENABLED=true` → `POST https://api.ted.europa.eu/v3/notices/search` `HTTP/1.1 200 OK` (live, no fixture); 12 notices normalizados con `source_request_hash`, `publication-number`, `notice-title`, `buyer-name`, `notice-type`, `retrieved_at`, `content_hash`, `retrieval_mode=LIVE_API_TECHNICAL_PROBE` persistidos en Postgres. `EVIDENCE_SHA=299cf73`.

- [x] **WP1-T05 — Materializar Evidence Objects verificables.**  
  **Cierre:** hash, fuente, ubicación, captura, licencia/derechos, temporalidad y trazabilidad quedan persistidos.  
  **Evidencia:** 12 Evidence Objects en la vista persistente del run con `evidence_id`, `source_id=src_ted_search_api_v3`, `rights_status=COMMERCIAL_REUSE_WITH_ATTRIBUTION`, `relationship`, `observed_at`, `provisional=false`, payload con `source_request_hash` y campo observado; tabla `tenant_private.subscriber_evidence` con trazabilidad. `EVIDENCE_SHA=299cf73`.

- [x] **WP1-T06 — Producir Candidate Claims con incertidumbre explícita.**  
  **Cierre:** cada claim referencia evidencia suficiente, conserva contradicciones y no se presenta como hecho admitido.  
  **Evidencia:** 12 Candidate Claims con `fingerprint`, `kind=FACT`, `producer_type=DETERMINISTIC_PARSER`, `method_version=ted-search-observed-field@0.1.0`, `rejection_reasons` y `state` pre-admisión; los claims no admitidos se rechazan con razón tipada; `evaluate_ted_observed_field` separa hechos/hipótesis y conserva contradicciones. `EVIDENCE_SHA=299cf73`.

- [x] **WP1-T07 — Ejecutar admisión determinista y Claim Ledger.**  
  **Cierre:** reglas independientes del modelo deciden admisión/rechazo; ledger append-only, reproducible y auditable.  
  **Evidencia:** 12 canonical claims admitidos por `evaluate_ted_observed_field` (reglas deterministas, sin modelo); `tenant_private.research_runs` con `admission_batch_id`; `admission_ledger_store` con registro append-only; candidatos generativos rechazados (`generative_producer_cannot_auto_admit` verificado en suite). `EVIDENCE_SHA=299cf73`.

- [x] **WP1-T08 — Construir InvestigationContext y respuesta AXENT gobernada.**  
  **Cierre:** AXENT usa únicamente contexto autorizado, cita evidencia, distingue hechos/hipótesis y mantiene autoridad humana.  
  **Evidencia:** C4 E2E `prepare` PASS (`AX_C4_RESEARCH_AXENT_PREPARE_PASS`): contexto del run persistido como `system_content` cifrado (`ciphertext_verified=true`), conversación AXENT creada con `retention_class`, idempotencia de creación y de mensajes; `research_context_persisted=true`. `EVIDENCE_SHA=299cf73`.

- [x] **WP1-T09 — Probar continuidad, aislamiento y recuperación.**  
  **Cierre:** reload, restart, backup/restore, logout, route protection y cross-tenant preservan o deniegan correctamente el estado.  
  **Evidencia:** C4 E2E `verify` tras restart real del proceso API PASS (`AX_C4_RESEARCH_AXENT_RUNTIME_PASS`): `restart_persistence=true`, `transcript_integrity=true`, `cross_tenant_isolation=true` (otro tenant → 404 genérico), `same_tenant_identity_isolation=true`, `legal_hold_blocked_purge=true`, `governed_deletion_completed=true`, `post_purge_api_404=true`; logout real con rotación de sesión y revocación (spec P25 PASS); route protection con AuthGate verificado. `EVIDENCE_SHA=299cf73`.

- [x] **WP1-T10 — Cerrar el recorrido navegador→investigación completo.**  
  **Cierre:** journey browser real desde login hasta paquete de investigación, sin bypasses y con manifest exact-head.  
  **Evidencia:** journey real completo sin intercepción: signup passwordless → passkey WebAuthn real (CDP virtual authenticator) → sesión AAL2 → subscriber workspace → Navigator submit → API real → 202 durable → redirect canónico `/research-runs/{runId}` → polling → vista server-authoritative 200; spec P25 (`identity-passwordless`) PASS y suite canónica del repo 46 pass/0 fail contra el stack real; C4 prepare+verify PASS. `EVIDENCE_SHA=5b6001b`.

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

- [ ] **WP4-T06 — Cerrar supply chain, repositorio y vulnerabilidades.**  
  **Cierre:** dependencias, imágenes, firmas/checksums, secrets scan y vulnerabilidades tienen cero hallazgos críticos explotables; `main` dispone de branch protection o ruleset equivalente con PR requerido, checks obligatorios, bloqueo de force push/deletion y bypass explícitamente gobernado.

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
  **Cierre:** merge controlado exact-head, tag/version, imágenes/bundle, SBOM, checksums, notas y rollback corresponden al mismo SHA; el estado de protección del repositorio queda declarado y no se usa force push.

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

No se detendrá por bibliotecas O02–O09, mejoras cosméticas, dashboards auxiliares, abstracciones futuras, integraciones no contratadas, warnings no materiales, ausencia temporal de branch protection aceptada por la autoridad humana o métricas que sólo puedan existir después del lanzamiento.

La deuda de protección de `main` permanece trazada en `#176` y debe cerrarse en `WP4-T06`, pero no bloquea merges controlados exact-head ni publicación técnica.

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

## 9. Autoridades de publicación y límites

La autoridad humana aprueba una estrategia `RELEASE_THEN_ITERATE`: publicación técnica controlada antes de la perfección final, seguida de auditorías E2E, revisión humana y corrección continua.

```text
CONTROLLED_PUBLIC_DEPLOYMENT true
PUBLIC_COMPLETION_CLAIM      false
COMMERCIAL_LIVE_MODE         false
STRIPE_LIVE_MODE             false
PUBLIC_SIGNUP                false
PRODUCTION_SOURCE_ADMISSION  false
GLOBAL_COVERAGE_CLAIM        false
AUTONOMOUS_EXTERNAL_ACTIONS  false
```

La publicación no permite afirmar que AXIGNAL está terminado E2E hasta que las 75 tareas estén `[x]` y se emita `AXIGNAL_E2E_COMPLETE`.

---

## 10. Firma

```text
HUMAN_AUTHORITY_APPROVAL     APPROVED
APPROVED_BY                  Rafael López
CONTRACT_ID                  AX-GE2E-FINISH-003
CONTRACT_VERSION             1.1.0-checklist.4
CONTRACT_STATE               ACTIVE_BINDING
ACTIVE_WORK_PACKAGE          WP0
ACTIVE_TASK                  WP0-T12
ACTIVE_BRANCH                agent/axignal-wp0-post-merge-image-ref-repair
ACTIVE_PULL_REQUEST          179
CANONICAL_MAIN_SHA           ccac72e286d778ab0187e447f45064d3c4d2d776
LAST_VALIDATED_PRODUCT_SHA   90edfb1e0697ced0e0b4eb90d7f18d93f4661c7f
CURRENT_REPAIR_HEAD          RESOLVE_FROM_PR_HEAD_AT_EXECUTION
ACTIVE_BLOCKER               AX-CLOSE-BLK-006_CROSS_DAEMON_IMAGE_LOOKUP
DEFERRED_HARDENING           AX-CLOSE-BLK-005 / ISSUE_176 / WP4-T06
NEXT_CANONICAL_MARKER        AX_C0_C4_CANONICAL_MAIN_PASS
PUBLICATION_STRATEGY         RELEASE_THEN_ITERATE
PUBLIC_DEPLOYMENT            AUTHORIZED
```

Este contrato se completa únicamente cuando las 75 tareas están `[x]`, el manifiesto P27 está ligado al SHA final y la autoridad humana emite `AXIGNAL_E2E_COMPLETE`.
