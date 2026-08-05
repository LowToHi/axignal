# AXIGNAL — Contrato canónico de cierre E2E sin sobreingeniería

**Contract ID:** `AX-GE2E-FINISH-003`  
**Versión contractual:** `1.0.0-ratified.1`  
**Fecha de entrada en vigor:** `2026-08-05T17:00:45+02:00`  
**Estado:** `RATIFIED / ACTIVE / BINDING`  
**Autoridad humana:** `Rafael López`  
**Repositorio:** `LowToHi/axignal`  
**Rama de materialización:** `agent/axignal-c0-canonical-reconciliation-v1`  
**Aplicación objetivo:** `AXIGNAL B2G Opportunity Intelligence & Operations v1.0`  
**Resultado contractual:** una aplicación completa, desplegable, cobrable, operable y utilizable de extremo a extremo en el dominio inicial de contratación pública.

---

## 0. Acto de ratificación

La autoridad humana ha ordenado expresamente elevar a contrato el documento:

```text
AXIGNAL_Contrato_Roadmap_Cierre_E2E_Sin_Sobreingenieria.md
```

En consecuencia, desde la fecha de entrada en vigor:

1. el documento queda aprobado y deja de estar en estado `PROPOSED / HUMAN APPROVAL REQUIRED`;
2. sus definiciones de producto terminado, alcance, work packages, reglas de cambio mínimo, prohibiciones de sobreingeniería, gates y condiciones de parada pasan a ser vinculantes;
3. este archivo materializa en el repositorio la ratificación y prevalece como autoridad operativa frente a roadmaps, estados, attestations o interpretaciones anteriores que entren en conflicto;
4. los documentos anteriores se conservan como audit trail, pero no pueden ampliar, reducir ni alterar silenciosamente este contrato;
5. toda modificación futura requiere una enmienda expresa aprobada por la autoridad humana.

```text
HUMAN_AUTHORITY_APPROVAL     APPROVED
APPROVED_BY                  Rafael López
APPROVED_AT                  2026-08-05T17:00:45+02:00
CONTRACT_STATUS              RATIFIED_ACTIVE
PUBLIC_LAUNCH_AUTHORITY      false
```

---

## 1. Incorporación del documento aprobado

Se incorpora por referencia, íntegramente y sin reducción material, el contenido de:

```text
filename       AXIGNAL_Contrato_Roadmap_Cierre_E2E_Sin_Sobreingenieria.md
contract_id    AX-GE2E-FINISH-003
version        1.0.0
source_date    2026-08-05
source_file_id file_00000000416c81f4a516bd5fc4f97431
```

Quedan ratificados, en particular:

- la decisión de cerrar AXIGNAL B2G v1.0 como vertical comercial completa;
- la separación entre `AXIGNAL B2G v1.0` y el programa de expansión `O02–O09`;
- la prohibición de rebajar el producto a maqueta, demo, buscador aislado o MVP incompleto;
- la cadena de valor desde identidad y fuente admitida hasta oportunidad, Bid Workspace, billing, soporte, backup y restauración;
- la autoridad server-side para identidad, tenant, roles, entitlements, billing y admisión;
- el carácter proposal-only de los modelos y la reserva humana de decisiones materiales;
- la política de un único PR, un único work package activo y un único ledger operativo;
- la regla de cambio mínimo basada en fallo observado y causa reproducible;
- la prohibición de retries, fixtures finales, timeouts artificiales y refactors no vinculados al blocker;
- el cierre canónico sólo después de merge protegido a `main` y smoke post-merge;
- el orden estricto `WP0 → WP1 → WP2 → WP3 → WP4 → WP5 → WP6`;
- las condiciones de parada por pérdida de datos, aislamiento tenant, autoridad, seguridad, cobro, restore, accesibilidad o manifiesto no ligado al SHA;
- la reserva de la matriz global exact-head para hitos contractuales, no para microcambios documentales.

---

## 2. Objeto contractual

AXIGNAL B2G v1.0 sólo podrá considerarse terminado cuando complete de forma real y persistente la cadena:

```text
visitante
→ registro y verificación
→ passkey y sesión revocable
→ organización, tenant y trial
→ fuente oficial admitida
→ ingestión y normalización
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
→ requisitos, evidencias, tareas, hitos y documentos
→ decisión y aprobación humana
→ exportación o activación registrada
→ outcome y aprendizaje
→ facturación, renovación, impago y cancelación
→ soporte, observabilidad, backup, restauración y auditoría
```

No constituye cumplimiento contractual:

- una interfaz sin backend real;
- un flujo basado en fixtures;
- una demo sin persistencia;
- un buscador sin operaciones de oportunidad;
- una respuesta de modelo sin evidencia gobernada;
- un PASS obtenido mediante retry o ampliación arbitraria de timeout;
- una attestation no ligada al SHA ejecutado;
- un cierre declarado exclusivamente en una rama no fusionada.

---

## 3. Alcance y no sobreingeniería

### 3.1 Alcance inicial obligatorio

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

### 3.2 Expansión posterior

```text
AXIGNAL Global Programme
= O02–O09
+ nuevas fuentes
+ nuevas bibliotecas
+ nuevas capacidades empresariales
```

La expansión posterior no es blocker de O01 salvo que una dependencia concreta sea materialmente necesaria para completar la cadena B2G contratada.

### 3.3 Prohibiciones vinculantes

Durante el cierre no se permite:

1. crear autoridades paralelas de identidad, tenant, claims, entitlements, tareas o billing;
2. añadir otra base de datos sin imposibilidad material demostrada;
3. introducir Kubernetes, service mesh, streaming o infraestructura no requerida por un fallo observado;
4. crear nuevos root workflows de CI;
5. incorporar O02–O09 en la ruta crítica;
6. refactorizar módulos ajenos al blocker;
7. sustituir integraciones reales por fixtures en gates finales;
8. usar retries para convertir flakiness en PASS;
9. elevar timeouts sin demostrar que representan un requisito funcional legítimo;
10. abrir varios PR o work packages de cierre simultáneos;
11. declarar `CLOSED` antes del merge protegido a `main`;
12. ampliar el contrato para evitar corregir el fallo activo.

---

## 4. Jerarquía de autoridad

En caso de contradicción se aplicará este orden:

```text
1. Enmienda contractual aprobada por la autoridad humana
2. Este contrato ratificado AX-GE2E-FINISH-003
3. Ledger canónico AXIGNAL_E2E_FINISH_LEDGER.json
4. Código y migraciones del exact HEAD activo
5. Resultado terminal de CI ligado al exact HEAD
6. Attestations y artefactos content-addressed
7. Documentos históricos y conversaciones
```

Una conversación, comentario, roadmap histórico o marcador anterior no puede modificar por sí solo el alcance o el estado contractual.

---

## 5. Modelo de cierre

### 5.1 Ingeniería

```text
NOT_STARTED
IN_PROGRESS
AFFECTED_TESTS_PASS
SUBSYSTEM_E2E_PASS
RELEASE_CANDIDATE_PASS
```

### 5.2 Canonicalidad

```text
UNMERGED
MERGE_READY
CANONICAL_CLOSED
PRODUCTION_DEPLOYED
PRIVATE_ACCEPTED
PUBLIC_LAUNCH_AUTHORIZED
```

### 5.3 Regla de cierre

Un work package sólo queda `CANONICAL_CLOSED` cuando:

1. el alcance está congelado;
2. las pruebas afectadas pasan;
3. la matriz del subsistema pasa;
4. la rama está reconciliada con `main`;
5. el merge protegido se completa;
6. el SHA resultante de `main` queda registrado;
7. el smoke post-merge pasa.

---

## 6. Work packages vinculantes

```text
WP0  Canonicalización del baseline C0–C4
WP1  Investigación, AXENT y evidencia real
WP2  O01, Opportunity y Bid Workspace completos
WP3  Comercial, billing y Founder Operations
WP4  Producción, seguridad, UX y distribución
WP5  Aceptación privada sobre producto terminado
WP6  P27, release candidate y lanzamiento
```

No se inicia un work package posterior para evitar resolver el anterior.

Las únicas preparaciones paralelas permitidas son externas y no mutantes:

- credenciales de producción;
- correo;
- Stripe;
- contacto de aceptación;
- revisión legal de fuente;
- provisioning del VPS.

---

## 7. Enmienda operativa de ratificación

El documento incorporado contiene un snapshot histórico del comienzo de WP0. Desde entonces, C4 ha superado su recorrido técnico y el blocker material activo se ha desplazado al verificador C3 de ciclos consecutivos.

Esta actualización no modifica el alcance, los criterios de calidad ni la secuencia WP0–WP6. Sustituye exclusivamente el snapshot operativo obsoleto.

### 7.1 Estado exacto al ratificar

```text
PR                         #169
BRANCH                     agent/axignal-c0-canonical-reconciliation-v1
BASE                       main
EXACT_HEAD_PRE_RATIFICATION dd119139555e885cc73d24d13e4b7b148797576e
PR_STATE                   OPEN / DRAFT / UNMERGED
PR_MERGEABLE               true
WP0                        IN_PROGRESS
WP1–WP6                    BLOCKED
PUBLIC_LAUNCH              NO_GO
```

### 7.2 Evidencia preservada

```text
Core                       PASS
Domain                     PASS
Specialized source         PASS
Remote pilot               PASS
Data integrity             PASS
C4 final runtime           PASS
C3 final closure           FAIL
```

### 7.3 Blocker vigente

```text
ID                         AX-CLOSE-BLK-002
ámbito                     C3 backup/restore consecutive-cycle verification
síntoma                     C3 first full-cycle hash drifted
causa acotada               comparación de evidencia generada bajo schema 140
                            con estado restaurado/actualizado bajo schema 142
naturaleza                  discrepancia de verificación; no evidencia de pérdida de datos
cambio permitido            comparador/verificador C3 exclusivamente
prohibido                   relajar integridad, ignorar schema drift, retirar hashes,
                            modificar producto, C4, billing, fuentes o arquitectura
criterio de cierre          equivalencia de datos en schema de origen,
                            upgrade determinista 141–142,
                            equivalencia final de schema/datos/autoridad,
                            matriz exact-head PASS
estado                      ROOT_CAUSE_CONFIRMED
```

### 7.4 Transición exacta autorizada

```text
ratification HEAD
→ localizar el comparador exacto de ciclos C3
→ corregir sólo la semántica de comparación entre schema 140 y schema 142
→ preservar la prueba de determinismo y todos los hashes materiales
→ ejecutar pruebas afectadas
→ full migration matrix PASS
→ Core PASS
→ Runtime PASS
→ Domain PASS
→ incorporar latest main
→ resolver únicamente conflictos materiales
→ full exact-head matrix PASS
→ PR #169 mergeable y ready
→ protected merge
→ smoke post-merge
→ registrar SHA canónico
→ AX_C0_C4_CANONICAL_MAIN_PASS
→ iniciar WP1
```

Cualquier otra transición material queda fuera de contrato hasta cerrar WP0.

---

## 8. Ledger obligatorio

La ejecución se gobernará mediante:

```text
docs/roadmap/AXIGNAL_E2E_FINISH_LEDGER.json
```

El ledger debe reflejar únicamente hechos verificables y contener, como mínimo:

- contract ID y versión;
- SHA canónico de `main`;
- rama, PR y exact HEAD activos;
- work package activo;
- blocker activo;
- transición permitida;
- estado de WP0–WP6;
- autoridad de lanzamiento;
- evidencia de CI y artefactos;
- último cambio aprobado por autoridad humana.

No habrá otro documento operativo paralelo con igual autoridad.

---

## 9. Condiciones de parada

El lanzamiento se detendrá ante:

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

No se detendrá por:

- bibliotecas futuras fuera de O01;
- mejoras cosméticas;
- preferencias de diseño;
- integraciones no contratadas;
- dashboards auxiliares;
- abstracciones futuras;
- warnings no materiales;
- métricas que sólo puedan existir después del lanzamiento.

---

## 10. Autoridades reservadas

Hasta el cierre de WP6 permanecen denegadas:

```text
PUBLIC_LAUNCH_AUTHORIZED    false
COMMERCIAL_LIVE_MODE        false
STRIPE_LIVE_MODE            false
PUBLIC_SIGNUP               false
PRODUCTION_SOURCE_ADMISSION false
GLOBAL_COVERAGE_CLAIM       false
AUTONOMOUS_EXTERNAL_ACTIONS false
```

La aprobación de este contrato autoriza su ejecución, no el lanzamiento público.

---

## 11. Firma y entrada en vigor

```text
HUMAN_AUTHORITY_APPROVAL     APPROVED
APPROVED_BY                  Rafael López
APPROVED_AT                  2026-08-05T17:00:45+02:00
CONTRACT_ID                  AX-GE2E-FINISH-003
CONTRACT_VERSION             1.0.0-ratified.1
CONTRACT_STATE               ACTIVE_BINDING
CANONICAL_BASELINE_SHA       dd119139555e885cc73d24d13e4b7b148797576e
ACTIVE_WORK_PACKAGE          WP0
ACTIVE_BLOCKER               AX-CLOSE-BLK-002
ALLOWED_NEXT_TRANSITION      FIX_C3_CONSECUTIVE_CYCLE_COMPARATOR_ONLY
NEXT_CANONICAL_MARKER        AX_C0_C4_CANONICAL_MAIN_PASS
PUBLIC_LAUNCH                NO_GO
```

Este contrato entra en vigor con su materialización en la rama activa. Su canonicalidad definitiva se producirá al integrarse mediante el merge protegido de WP0 en `main` y superar el smoke post-merge.