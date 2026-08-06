# AXIGNAL — Auditoría técnica End-to-End

- **Fecha:** 2026-07-31
- **Repositorio:** `LowToHi/axignal`
- **Baseline canónica observada:** `main@b9a08a2a07d04d635164e161d1b27a7a53df8575`
- **Baseline de ingeniería auditada:** `cc2700ffcf06800461e77e9d09f45e54cdbf5842`
- **Rama de auditoría:** `agent/e2e-technical-audit-v1`
- **Head validado:** `15978f719351540ff63553f83025c7c29d27538d`
- **PR de auditoría:** `#87`
- **Dictamen:** **NO_GO para producción pública**

## 1. Resumen ejecutivo

AXIGNAL es una plataforma de inteligencia y operación de oportunidades globales con una primera envolvente comercial B2G. La arquitectura candidata combina dos aplicaciones Next.js, una API FastAPI, PostgreSQL/PostGIS/pgvector, Valkey, workers persistentes, contratos JSON Schema, migraciones SQL, validadores deterministas, Playwright y GitHub Actions.

La columna vertebral de ingeniería es material y ejecutable. La instalación limpia, compilación Python, typecheck TypeScript, builds Next.js, Docker Compose, PostgreSQL, Valkey, 151 tests Python, Playwright de escritorio y tablet, WebAuthn, sesiones, aislamiento de tenants, antiabuso del trial, investigación persistente, propuesta, admisión, revisión humana y restauraciones cubiertas por los workflows existentes han superado la validación realizada.

Sin embargo, el producto **no está listo para producción**. El propio repositorio declara `Public launch: NO_GO`, `main` solo representa P00 aceptado/P01 en progreso y la ingeniería P02–P26 permanece en PRs draft apiladas. Además, no existe una prueba acumulativa de todas las migraciones hasta la última versión, los tests de frontend declarados son procesos vacíos, la cobertura Python total es 59,62 % y varios workers y repositorios críticos tienen cobertura nula o muy baja.

### Resultado de los gates auditados

| Gate | Resultado |
|---|---|
| Instalación Python limpia | PASS |
| Instalación pnpm con lockfile | PASS |
| Compilación Python | PASS |
| Ruff | PASS |
| TypeScript | PASS |
| Builds Next.js | PASS |
| Docker Compose build/up/health | PASS |
| PostgreSQL y Valkey | PASS |
| Tests Python | PASS — 151 |
| Cobertura Python | 59,62 % — insuficiente como gate de producción |
| Playwright escritorio | PASS |
| Playwright tablet Chromium | PASS tras corrección |
| WebAuthn, sesiones y trial abuse | PASS |
| `pip-audit` | PASS — 0 vulnerabilidades conocidas tras corrección |
| `pnpm audit --prod` | PASS — 0 vulnerabilidades conocidas |
| Formato global | FAIL — 365 ficheros |
| Tests unitarios frontend | FAIL — scripts no-op |
| Rehearsal acumulativo de todas las migraciones | FAIL — cobertura parcial |
| Estado canónico y autorización de lanzamiento | FAIL / NO_GO |

## 2. Mapa de arquitectura

```text
Usuarios públicos / compradores / operadores / founder admin
                │
                ├── apps/landing — Next.js 16 / React 19 / WebGL
                │       ├── descubrimiento y adquisición
                │       ├── pilot intake
                │       └── salud pública
                │
                └── apps/web — Next.js 16 / React 19 / BFF
                        ├── identidad y sesiones
                        ├── billing y entitlements
                        ├── seats e invitaciones
                        ├── discovery, Navigator e InvestigationContext
                        ├── research runs y progreso
                        ├── human review y validation
                        └── founder/admin y páginas orgánicas
                                      │
                                      ▼
                         FastAPI composition root
                         axignal_api.application:app
                                      │
          ┌───────────────────────────┼────────────────────────────┐
          ▼                           ▼                            ▼
   Identity/Billing/Seats      Research/Workers/Queues      Admission/Review
          │                           │                            │
          └───────────────────────────┼────────────────────────────┘
                                      ▼
                   PostgreSQL + PostGIS + pgvector
                   Valkey queues/cache
                   content-addressed object store
                   OpenTelemetry boundary
```

### Flujo de producto

```text
signals
→ admitted sources
→ Evidence Objects
→ Candidate Claims
→ deterministic admission
→ InvestigationContext
→ Opportunity
→ Pursuit
→ Operational Workspace
→ Outcome
→ Learning
```

La separación conceptual entre propuesta de IA y autoridad determinista es coherente. Las configuraciones sensibles tienden a fallar de forma cerrada y los runtimes de prueba exigen entorno y flags explícitos.

### Deuda arquitectónica observada

- La composición de todos los routers sobre una aplicación base que todavía contiene fixtures sintéticas mezcla prototipo y runtime candidato.
- Varias capas HTTP y repositorios son excesivamente grandes: `identity_routes.py`, `billing_routes.py`, `seat_routes.py`, `organic_routes.py`, `proposal_repository.py` y el repositorio general concentran demasiadas responsabilidades.
- Existe una capa de contratos y validadores muy extensa, pero la evidencia contractual supera a la cobertura ejecutable de algunos runtimes.
- El repositorio canónico y la pila real de ingeniería han divergido; esto dificulta reproducibilidad, bisect, release y ownership.

## 3. Inventario de incidencias

### AX-AUD-001 — Estado no canónico y lanzamiento no autorizado

- **Prioridad:** 🔴 Crítica
- **Descripción:** la implementación auditada vive en una pila de PRs draft; `main` no contiene el producto candidato y el README declara `NO_GO`.
- **Impacto:** no existe una revisión única que pueda etiquetarse, desplegarse y restaurarse como release oficial.
- **Localización:** `README.md`, ADR-016, Contract 31, registro canónico v1.5 y pila `agent/ax-ge2e-*`.
- **Causa:** desarrollo por fases apiladas sin consolidación canónica completa.
- **Riesgo:** despliegue desde una revisión equivocada, pérdida de trazabilidad, gates aparentemente verdes sobre bases diferentes y rollback ambiguo.
- **Solución propuesta:** consolidar la pila en una rama de release reproducible; verificar ancestry y artefactos; ejecutar la matriz completa; aceptar fases mediante el proceso canónico; solo después fusionar/taggear.
- **Código sugerido:** workflow `release-candidate.yml` que reciba un SHA inmutable, verifique que todos los gates pertenecen a ese SHA y genere SBOM, imágenes por digest y manifiesto de release.
- **Complejidad:** Alta.
- **Tiempo estimado:** 2–5 días de ingeniería más decisiones de gobernanza.

### AX-AUD-002 — Rehearsal incompleto de migraciones y rollback

- **Prioridad:** 🔴 Crítica
- **Descripción:** el rehearsal acumulativo inspeccionado valida un subconjunto histórico de migraciones, mientras el repositorio contiene una cadena mucho más larga.
- **Impacto:** no se ha demostrado que una base real pueda actualizarse desde todos los estados soportados hasta el esquema actual ni restaurarse después de un fallo tardío.
- **Localización:** `scripts/verify_cumulative_migration_rehearsal.sh`, `infra/postgres/migrations/`.
- **Causa:** crecimiento incremental de migraciones sin matriz acumulativa automática equivalente.
- **Riesgo:** pérdida o corrupción de datos, bloqueos de deploy, esquemas parcialmente aplicados y rollback no operativo.
- **Solución propuesta:** ejecutar todas las migraciones en orden sobre bases vacía, N-1 y snapshots representativos; verificar checksums, idempotencia donde proceda, constraints, roles, RLS, índices y restauración.
- **Código sugerido:** un runner que enumere por nombre todas las migraciones, prohíba huecos, registre `schema_migrations`, capture snapshot antes/después y ensaye restore contra el head exacto.
- **Complejidad:** Alta.
- **Tiempo estimado:** 3–7 días.

### AX-AUD-003 — Suite frontend declarada como tests pero implementada como no-op

- **Prioridad:** 🔴 Crítica como gate QA de producción
- **Descripción:** `@axignal/web`, `@axignal/landing` y `@axignal/design-tokens` ejecutan `node -e "process.exit(0)"` en `test`.
- **Impacto:** `pnpm test` siempre pasa aunque existan regresiones de componentes, lógica de estado, validación, accesibilidad o utilidades.
- **Localización:** `apps/web/package.json`, `apps/landing/package.json`, `packages/design-tokens/package.json`.
- **Causa:** dependencia casi exclusiva de TypeScript, builds y E2E.
- **Riesgo:** cobertura insuficiente de ramas y errores difíciles de diagnosticar; falsa confianza en CI.
- **Solución propuesta:** Vitest + Testing Library para componentes y librerías, contratos de rutas/BFF, estados de error, autorización y accesibilidad; mantener Playwright para journeys.
- **Código sugerido:** sustituir `test` por `vitest run --coverage` y establecer umbrales iniciales por paquete, aumentando progresivamente.
- **Complejidad:** Alta.
- **Tiempo estimado:** 2–4 semanas para una base adecuada de áreas críticas.

### AX-AUD-004 — Cobertura insuficiente de workers y persistencia

- **Prioridad:** 🟠 Alta
- **Descripción:** cobertura Python total 59,62 %. `research_worker`, `retention_worker`, `proposal_publisher`, `scheduler_service`, `admission_runtime` y `proposal_worker` están al 0 %. Repositorios de identidad, TED, seats, entitlements, billing, organic y proposals se sitúan aproximadamente entre 17 % y 30 %.
- **Impacto:** las rutas felices de aceptación no cubren de forma fina retries, carreras, idempotencia, errores parciales, leases, duplicados y recuperación.
- **Localización:** `apps/api/src/axignal_api/*worker.py`, `*_repository.py`, `*_routes.py`.
- **Causa:** fuerte inversión en verificadores E2E y menor inversión en tests unitarios/de integración focalizados.
- **Riesgo:** fallos ocultos bajo carga, mensajes duplicados, estados imposibles, pérdida de leases o escrituras parciales.
- **Solución propuesta:** priorizar workers, repositorios y máquinas de estado; utilizar PostgreSQL/Valkey reales en tests de integración y fault injection controlada.
- **Código sugerido:** tests parametrizados de idempotencia, evento fuera de orden, redelivery, timeout, lock perdido, rollback y tenant mismatch; gate de cobertura por módulo crítico.
- **Complejidad:** Alta.
- **Tiempo estimado:** 2–4 semanas.

### AX-AUD-005 — Dependencias Python no bloqueadas de forma reproducible

- **Prioridad:** 🟠 Alta
- **Descripción:** `pyproject.toml` utiliza rangos amplios y no existe un lockfile Python de producción.
- **Impacto:** dos instalaciones en fechas distintas pueden resolver FastAPI, Starlette, Pydantic, Uvicorn, Redis u OpenTelemetry diferentes.
- **Localización:** `pyproject.toml`, workflows y Dockerfiles Python.
- **Causa:** especificación por rangos sin resolución inmutable.
- **Riesgo:** builds no reproducibles, vulnerabilidades o incompatibilidades introducidas sin cambio de código.
- **Solución propuesta:** generar lock con hashes por plataforma soportada, actualizarlo mediante Dependabot/Renovate y verificar SBOM.
- **Código sugerido:** `uv lock`/`pip-tools --generate-hashes`; CI con `uv sync --frozen` o `pip install --require-hashes`.
- **Complejidad:** Media.
- **Tiempo estimado:** 2–4 días.

### AX-AUD-006 — Autenticación legacy sin rate limiting visible

- **Prioridad:** 🟠 Alta
- **Descripción:** el fallback de email/contraseña valida scrypt y usa comparación temporalmente segura, pero la ruta no presenta rate limiting, backoff o bloqueo por identidad/IP.
- **Impacto:** una configuración que exponga el fallback permite fuerza bruta distribuida.
- **Localización:** `apps/web/app/api/auth/login/route.ts`, `apps/web/lib/server-auth.ts`.
- **Causa:** transición hacia passwordless manteniendo un modo heredado.
- **Riesgo:** credential stuffing, consumo de CPU por scrypt y denegación de servicio.
- **Solución propuesta:** retirar el fallback de producción o protegerlo con rate limit compartido, límites por identidad/IP, backoff, auditoría y respuesta uniforme.
- **Código sugerido:** token bucket en Valkey con claves HMAC de email/IP; fail closed si el backend de límites no está disponible.
- **Complejidad:** Media.
- **Tiempo estimado:** 2–5 días.

### AX-AUD-007 — Cobertura CSRF explícita no demostrada en todos los BFF mutantes

- **Prioridad:** 🟠 Alta
- **Descripción:** las cookies son `HttpOnly`, `Secure` en producción y `SameSite=Lax`, pero no se ha encontrado un control uniforme de `Origin`/`Host` o token CSRF en todas las rutas mutantes del BFF.
- **Impacto:** `SameSite=Lax` reduce riesgo, pero no sustituye una política verificable para todas las mutaciones y navegadores.
- **Localización:** rutas `apps/web/app/api/**/route.ts` de billing, seats, admin, auth y research.
- **Causa:** controles distribuidos y ausencia de middleware/utility común visible.
- **Riesgo:** acciones no deseadas si una ruta, método o contexto de cookie escapa a las garantías asumidas.
- **Solución propuesta:** helper obligatorio de same-origin para mutaciones, token CSRF cuando proceda y tests negativos globales.
- **Código sugerido:** `requireSameOrigin(request)` comparando `Origin`, `Host` y `X-Forwarded-Host` solo tras validar proxy confiable.
- **Complejidad:** Media.
- **Tiempo estimado:** 3–5 días.

### AX-AUD-008 — Documentación de instalación insuficiente

- **Prioridad:** 🟠 Alta
- **Descripción:** el README explica producto, estado y gobernanza, pero no ofrece un recorrido operativo completo desde clon limpio hasta sistema funcional.
- **Impacto:** onboarding dependiente de conocimiento implícito; alta probabilidad de configuraciones divergentes.
- **Localización:** `README.md`, `.env.example`, runbooks dispersos.
- **Causa:** documentación orientada al programa y contratos, no al operador/desarrollador nuevo.
- **Riesgo:** instalaciones incompletas, flags inseguros, ejecución de fixtures como si fueran producción y tiempos altos de recuperación.
- **Solución propuesta:** quickstart verificado, matriz de servicios, perfiles de entorno, comandos, seeds, health checks, troubleshooting, arquitectura y manual de release/rollback.
- **Código sugerido:** script `scripts/bootstrap-local.sh` idempotente y documentación generada/probada en CI.
- **Complejidad:** Media.
- **Tiempo estimado:** 1–2 días para base; 3–5 días para manuales completos.

### AX-AUD-009 — Deuda de formato masiva

- **Prioridad:** 🟡 Media
- **Descripción:** `prettier --check .` detecta 365 ficheros fuera de formato.
- **Impacto:** ruido en diffs, conflictos y imposibilidad práctica de activar el gate global sin una migración controlada.
- **Localización:** código TS/TSX/CSS, YAML, JSON y documentación.
- **Causa:** incorporación histórica sin enforcement uniforme.
- **Riesgo:** revisiones menos fiables y cambios funcionales ocultos en diffs de formato.
- **Solución propuesta:** PR exclusivo de formato, snapshot del árbol antes/después y exclusiones justificadas para artefactos que no deban formatearse.
- **Código sugerido:** `.prettierignore`, `prettier --write` en commit aislado y gate obligatorio posterior.
- **Complejidad:** Media por volumen, baja por lógica.
- **Tiempo estimado:** 1–2 días.

### AX-AUD-010 — `lint` frontend equivale a typecheck; no existe lint semántico

- **Prioridad:** 🟡 Media
- **Descripción:** web y landing ejecutan `tsc --noEmit` tanto para `lint` como para `typecheck`.
- **Impacto:** no se detectan hooks incorrectos, imports, promesas flotantes, accesibilidad JSX, mutaciones o patrones peligrosos.
- **Localización:** package manifests frontend.
- **Causa:** ausencia de ESLint/Biome u otra herramienta semántica.
- **Riesgo:** code smells y errores que compilan correctamente.
- **Solución propuesta:** ESLint flat config o Biome con reglas React, hooks, TypeScript, import y seguridad.
- **Código sugerido:** `eslint . --max-warnings=0` separado de `tsc --noEmit`.
- **Complejidad:** Media.
- **Tiempo estimado:** 2–4 días incluyendo baseline.

### AX-AUD-011 — Descargador de assets sin política explícita de red y tamaño

- **Prioridad:** 🟡 Media
- **Descripción:** el script de adquisición abre URLs del manifest y transmite el contenido sin allowlist de hosts, validación de redirects ni límite máximo de bytes.
- **Impacto:** una alteración del manifest puede convertir el proceso en SSRF o provocar consumo excesivo de disco.
- **Localización:** `scripts/acquire_globe_assets.py`, `docs/landing/assets-manifest.json`.
- **Causa:** confianza implícita en el manifest versionado.
- **Riesgo:** acceso a destinos no autorizados desde CI/operación y descarga de objetos inesperadamente grandes.
- **Solución propuesta:** HTTPS obligatorio, allowlist de dominios, validación del destino final, `Content-Length` y límite durante streaming, checksum esperado.
- **Código sugerido:** opener sin redirects automáticos o handler que revalide cada salto; contador de bytes y borrado atómico en fallo.
- **Complejidad:** Baja/Media.
- **Tiempo estimado:** 1–2 días con tests.

### AX-AUD-012 — Imágenes y acciones no completamente fijadas por digest/SHA

- **Prioridad:** 🟡 Media
- **Descripción:** existen tags de imágenes base y al menos acciones con tag mayor en workflows, aunque muchas acciones sí están fijadas por SHA.
- **Impacto:** la misma revisión puede ejecutar dependencias de supply chain diferentes.
- **Localización:** Dockerfiles, Compose y `.github/workflows/`.
- **Causa:** pinning parcial.
- **Riesgo:** comportamiento no reproducible o compromiso upstream.
- **Solución propuesta:** imágenes por digest, acciones por SHA con comentario de versión, revisión automatizada de pinning y SBOM firmado.
- **Código sugerido:** política CI que rechace `uses: owner/action@vN` y `FROM image:tag` sin digest, con excepciones documentadas.
- **Complejidad:** Media.
- **Tiempo estimado:** 2–4 días.

### AX-AUD-013 — Uso extensivo de `assert` en rutas y scripts

- **Prioridad:** 🟡 Media
- **Descripción:** Bandit detecta numerosos asserts; algunos aparecen en runtime como estrechamiento de tipos después de validar configuración.
- **Impacto:** Python optimizado elimina asserts, reduce claridad de invariantes y produce errores posteriores menos diagnosticables.
- **Localización:** `apps/api/src/axignal_api/` y verificadores.
- **Causa:** uso de `assert` como comprobación y type narrowing.
- **Riesgo:** invariantes no ejecutadas donde no exista una validación previa equivalente.
- **Solución propuesta:** sustituir asserts de runtime por errores explícitos y conservar asserts solo en tests/verificadores donde sean deliberados.
- **Código sugerido:** `if value is None: raise RuntimeError("validated invariant missing")`.
- **Complejidad:** Media por volumen.
- **Tiempo estimado:** 2–5 días.

### AX-AUD-014 — Módulos HTTP y repositorios demasiado grandes

- **Prioridad:** 🟡 Media
- **Descripción:** varias rutas y repositorios concentran estados, autorización, persistencia, proveedor y traducción HTTP.
- **Impacto:** alto coste de cambio y tests más difíciles.
- **Localización:** identidad, billing, seats, organic, proposal repository y repositorio general.
- **Causa:** crecimiento incremental por fase.
- **Riesgo:** acoplamiento, regresiones laterales y ownership ambiguo.
- **Solución propuesta:** separar command handlers, query services, policies, provider adapters y mappers; mantener routers finos.
- **Código sugerido:** patrón application service por caso de uso con puertos tipados y transacciones explícitas.
- **Complejidad:** Alta.
- **Tiempo estimado:** 2–6 semanas de refactor incremental.

### AX-AUD-015 — Rendimiento y capacidad no demostrados

- **Prioridad:** 🟠 Alta como gate, no como bug confirmado
- **Descripción:** no se ha encontrado evidencia suficiente de carga, soak, límites de concurrencia, planes de consulta, N+1 o presupuesto de memoria/CPU del sistema completo.
- **Impacto:** una build funcional puede degradarse o fallar bajo uso real.
- **Localización:** API, workers, PostgreSQL, Valkey, Next.js y observabilidad.
- **Causa:** validación centrada en corrección funcional y contratos.
- **Riesgo:** saturación de pools, latencia, backlog de colas, timeouts y costes impredecibles.
- **Solución propuesta:** perfiles de carga por journey, SLOs, límites y dashboards; `EXPLAIN ANALYZE` para consultas críticas; soak de workers con redelivery y backpressure.
- **Código sugerido:** k6/Locust con escenarios autenticados y métricas OTel; gate por p95/p99, errores, queue age y consumo.
- **Complejidad:** Alta.
- **Tiempo estimado:** 1–3 semanas para baseline y remediaciones iniciales.

## 4. Plan de remediación

1. **Consolidar una release candidate inmutable.** No seguir evaluando producción sobre una pila móvil de PRs.
2. **Construir el rehearsal completo de migraciones y restauración.** Bloquear cualquier despliegue hasta demostrarlo.
3. **Convertir los tests frontend no-op en pruebas reales** y añadir gates por paquete.
4. **Cubrir workers y repositorios críticos**, empezando por idempotencia, carreras, redelivery y estados terminales.
5. **Cerrar seguridad operativa:** rate limiting del fallback, política same-origin/CSRF, hardening del descargador, baseline de secretos y eliminación de asserts de runtime.
6. **Bloquear dependencias e infraestructura:** lock Python, SBOM, imágenes por digest y acciones por SHA.
7. **Añadir rendimiento, capacidad y observabilidad verificable.**
8. **Actualizar onboarding, runbooks y manuales.**
9. **Ejecutar la aceptación final sobre el mismo SHA** y solo entonces aceptar P27, fusionar y etiquetar.

## 5. Registro de cambios

| Cambio | Justificación | Commit/estado |
|---|---|---|
| Workflow aislado de auditoría E2E | Obtener evidencia reproducible sin modificar comportamiento de producto | Incluido en PR #87 |
| Corrección del proyecto tablet | El perfil iPad heredaba WebKit aunque el proyecto se llamaba Chromium y CI solo instalaba Chromium | Validado |
| Declaración de `jsonschema` como dependencia dev | Los verificadores lo importaban sin que el entorno dev lo declarase | Validado |
| Ejecución independiente de todos los gates JS | Evitar que un fallo de formato ocultase lint, typecheck, tests, build y auditoría | Validado |
| Exclusiones seguras del secret scan | Eliminar ruido de `.git`, caches y artefactos generados sin ocultar código | Validado |
| Upgrade de `pytest` a `>=9.0.3,<10` | Remediar vulnerabilidad detectada por `pip-audit` | Validado con pytest 9.1.1 |

No se realizó un formateo masivo ni un refactor amplio porque violaría la regla de cambios pequeños y produciría un diff de alto riesgo sin mejorar por sí mismo la corrección funcional.

## 6. Validación posterior a cada cambio

### Evidencia final sobre `15978f719351540ff63553f83025c7c29d27538d`

- `E2E Technical Audit` run `30667883080`: PASS.
- `Executable Spine` run `30667883164`: PASS.
- `F2 Runtime Closure` run `30667883130`: PASS.
- `P25-T01 Identity Passwordless and Trial Abuse E2E` run `30667883075`: PASS.
- P17, P18, P19 y P20: PASS.
- V1.5 Canonical Contract Validation: PASS.
- Contract Validation: PASS.

### Detalle reproducido

- 151 tests Python: PASS.
- Cobertura: 59,62 %.
- Ruff: PASS.
- `pip-audit`: 0 vulnerabilidades conocidas.
- `pnpm audit --prod`: 0 vulnerabilidades conocidas.
- TypeScript: PASS.
- Build web y landing: PASS.
- Playwright desktop + tablet Chromium: PASS.
- Docker Compose config/build/up/health/down: PASS.
- PostgreSQL y Valkey: PASS.
- Verificador global de contratos: PASS.
- Formato global: FAIL en 365 ficheros, registrado como deuda y no ocultado.

## 7. Riesgos residuales

- La evidencia verde pertenece a una rama candidata, no a `main` ni a una release aceptada.
- No se ha ejecutado Stripe sandbox real en esta auditoría; existen adapters y lifecycle determinista, pero la autoridad externa requiere pruebas separadas con cuenta y webhooks reales.
- Los flujos de producción con SMTP, bot verification, live sources, backups externos y edge real permanecen condicionados por configuración y autorización.
- No se ha demostrado capacidad bajo carga ni cumplimiento de SLOs.
- El secret scan no tiene todavía una baseline revisada; produce alto ruido y no debe interpretarse como certificación de ausencia de secretos.
- Los contratos JSON y los verificadores son valiosos, pero no sustituyen tests de implementación de los workers/repositories con cobertura baja.
- P26 sigue incompleta según el propio README: administración de customer/billing, risk/source y operaciones/DR/settings.

## 8. Checklist final

| Condición | Estado | Evidencia / impedimento |
|---|---|---|
| No existen errores críticos | **NO** | Persisten bloqueos críticos de release, migraciones y QA |
| Flujos principales funcionan E2E | **PARCIAL** | Investigación, autoridad, WebAuthn y browser base pasan; no todos los journeys productivos están aceptados sobre una release canónica |
| Instalación desde cero | **PASS para entorno auditado** | Python, pnpm y Docker pasan |
| Compila correctamente | **PASS** | Python, TypeScript y Next builds verdes |
| Dependencias no rotas | **PASS actual / NO reproducible a largo plazo** | Auditorías verdes, pero falta lock Python |
| Sin problemas de seguridad críticos conocidos | **PASS limitado** | 0 CVEs conocidos en auditorías; quedan hardenings y pruebas operativas |
| Arquitectura consistente | **PARCIAL** | Límites de autoridad sólidos; composición, módulos grandes y divergencia canónica requieren remediación |
| Documentación actualizada | **PARCIAL** | Contratos extensos; quickstart y manuales operativos insuficientes |
| Preparado para evolucionar | **PARCIAL** | Buen contrato de dominio, pero deuda de tests, migraciones, release y modularidad |
| Preparado para producción | **NO_GO** | No autorizar despliegue público |

## Decisión

**AXIGNAL no debe considerarse listo para producción pública en esta revisión.**

La implementación candidata demuestra una base de ingeniería considerable y varios flujos complejos reales. El siguiente gate no es añadir más contratos o funcionalidades: es convertir la pila candidata en una release reproducible, demostrar la cadena completa de datos y migraciones, elevar la cobertura de los runtimes críticos y ejecutar la aceptación final sobre un único SHA inmutable.
