# 06 — Stack Freeze and Self-Hosted CI Tasks

Version: `0.1.0-candidate`
Goal ID: `AXIGNAL-GOAL-001`

These tasks extend the canonical catalogue and MUST be folded into `02-task-catalogue.md` at the next roadmap freeze.

## F0 — Stack governance

| Task | Outcome | Contracts | Skills |
|---|---|---|---|
| `AX-F0-T07` | Audit and freeze the candidate stack with versions, licences and replacement gates | 04, 19 | repository-architect, security-reviewer, gate-evaluator |
| `AX-F0-T08` | Record ADRs for pgvector-first storage, workflow orchestration and CI trust boundaries | 19 | data-architect, security-reviewer, contract-router |

## F1 — Design-system validation

| Task | Outcome | Contracts | Skills |
|---|---|---|---|
| `AX-F1-T13` | Apply candidate palette, typography and density modes to prototype v0.2 | 13, 20 | visualisation-designer, interaction-architect, accessibility-auditor |
| `AX-F1-T14` | Validate Globe–Graph semantic transformation and reduced-motion equivalent | 12, 13, 20 | globe-engineer, graph-engineer, performance-engineer |
| `AX-F1-T15` | Compare Sigma.js/Graphology against the remaining graph-renderer candidate using representative fixtures | 19 | graph-engineer, performance-engineer, gate-evaluator |
| `AX-F1-T16` | Validate six-language typography, wrapping and locale formatting | 16, 20 | multilingual-localiser, accessibility-auditor |

## F2 — Reproducible stack and CI

| Task | Outcome | Contracts | Skills |
|---|---|---|---|
| `AX-F2-T10` | Provision the VPS as a dedicated non-root AXIGNAL self-hosted runner | 06, 19 | repository-architect, security-reviewer |
| `AX-F2-T11` | Separate untrusted pull-request validation from trusted self-hosted workloads | 06, 08, 19 | security-reviewer, test-engineer, gate-evaluator |
| `AX-F2-T12` | Add disposable job containers, cleanup, resource telemetry and runner patching | 08, 10, 19 | observability-engineer, security-reviewer |
| `AX-F2-T13` | Scaffold pnpm/Turborepo, uv, Next.js, FastAPI and generated OpenAPI clients | 04, 19 | repository-architect, frontend-architect, backend-architect |
| `AX-F2-T14` | Scaffold AXIGNAL-owned shadcn registry and domain components | 19, 20 | frontend-architect, interaction-architect |
| `AX-F2-T15` | Add separate Remotion render package without loading it into the interactive shell | 19, 20 | frontend-architect, visualisation-designer, performance-engineer |

## Gate additions

F0 cannot freeze until `AX-F0-T07–T08` produce accepted ADRs.

F1 cannot pass until the candidate design system and motion model are validated against qualified users, reduced-motion operation and six-language fixtures.

F2 cannot pass until the VPS runner completes an isolated trusted workflow without root execution or production-secret access.
