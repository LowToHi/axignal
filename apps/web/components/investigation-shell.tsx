"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  claimsForSelectedOpportunity,
  createInitialInvestigation,
  evidenceForClaim,
  findSelectedOpportunity,
  initialMessages,
  nextHistoryEvent,
  normaliseInvestigationPayload,
  selectedResearchDossier,
  selectedResearchRun,
  updateContext,
  type Claim,
  type ClaimKind,
  type Lens,
  type Locale,
  type Message,
  type PersistedShellState,
  type PrototypeInvestigationPayload,
  type Theme
} from "../lib/investigation-context";
import { runNavigatorCommand, runResearch } from "../lib/navigator-client";

const STORAGE_KEY = "axignal:investigation-shell:v2";
const lensOptions: Lens[] = ["AUTO", "GLOBE", "GRAPH", "DUAL"];
const localeOptions: { value: Locale; label: string }[] = [
  { value: "en", label: "EN" },
  { value: "es", label: "ES" },
  { value: "fr", label: "FR" },
  { value: "de", label: "DE" },
  { value: "pt-BR", label: "PT" },
  { value: "zh-Hans", label: "中文" }
];

type ClaimFilter = "TODOS" | ClaimKind;
type RequestState = "idle" | "processing" | "error";

function Confidence({ value }: { value: number }) {
  const score = Math.max(0, Math.min(5, Math.round(value * 5)));
  return (
    <span className="confidence" aria-label={`Confianza ${score} de 5`}>
      {Array.from({ length: 5 }, (_, index) => (
        <i key={index} data-on={index < score} />
      ))}
    </span>
  );
}

function GlobeSurface({ payload }: { payload: PrototypeInvestigationPayload }) {
  const selected = findSelectedOpportunity(payload);
  return (
    <div className="globe-stage" aria-label="Globe centrado en Moscú">
      <div className="star-field" />
      <div className="globe">
        <div className="globe-grid" />
        <span className="signal signal-moscow" />
        <span className="signal signal-europe" />
        <span className="signal signal-me" />
        <span className="signal signal-asia" />
        <div className="moscow-card">
          <strong>Moscú, Rusia</strong>
          <span>Selección <b>{selected.name}</b></span>
          <span>Potencial <b>{selected.level}</b></span>
          <span>Retorno prototipo <b>{selected.expected_return_label}</b></span>
        </div>
      </div>
      <div className="potential-legend">
        <span>POTENCIAL · FIXTURE SINTÉTICA</span>
        <div className="legend-gradient" />
        <div className="legend-labels"><small>Muy bajo</small><small>Medio</small><small>Muy alto</small><small>Sin datos</small></div>
      </div>
    </div>
  );
}

function GraphSurface({ payload }: { payload: PrototypeInvestigationPayload }) {
  const selected = findSelectedOpportunity(payload);
  const nodes = [
    { id: "moscow", x: 50, y: 48, label: "Moscú" },
    { id: "opportunity", x: 25, y: 26, label: selected.name.replace("Distrito de ", "") },
    { id: "transport", x: 72, y: 24, label: "Transporte" },
    { id: "demand", x: 78, y: 66, label: "Demanda" },
    { id: "rates", x: 28, y: 74, label: "Tipos" }
  ];

  return (
    <div className="graph-stage" aria-label="Grafo de relaciones de la oportunidad">
      <svg viewBox="0 0 100 100" role="img" aria-label={`Relaciones causales de ${selected.name}`}>
        <line x1="50" y1="48" x2="25" y2="26" className="edge support" />
        <line x1="50" y1="48" x2="72" y2="24" className="edge inferred" />
        <line x1="50" y1="48" x2="78" y2="66" className="edge support" />
        <line x1="50" y1="48" x2="28" y2="74" className="edge contradiction" />
        <line x1="72" y1="24" x2="78" y2="66" className="edge inferred" />
        {nodes.map((node) => (
          <g key={node.id} className={node.id === "opportunity" ? "node selected" : "node"}>
            <circle cx={node.x} cy={node.y} r={node.id === "opportunity" ? 8 : 6} />
            <text x={node.x} y={node.y + 1}>{node.label}</text>
          </g>
        ))}
      </svg>
      <div className="graph-caption">
        <strong>Transmission graph</strong>
        <span>{selected.name} · relaciones tipadas · contexto preservado</span>
      </div>
    </div>
  );
}

function PrimaryCanvas({ payload }: { payload: PrototypeInvestigationPayload }) {
  const effectiveLens = payload.context.lens === "AUTO" ? "GLOBE" : payload.context.lens;
  if (effectiveLens === "GRAPH") return <GraphSurface payload={payload} />;
  if (effectiveLens === "DUAL") {
    return (
      <div className="dual-stage">
        <GlobeSurface payload={payload} />
        <GraphSurface payload={payload} />
      </div>
    );
  }
  return <GlobeSurface payload={payload} />;
}

function isPersistedState(value: unknown): value is PersistedShellState {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<PersistedShellState>;
  return candidate.schemaVersion === 2 && candidate.payload?.context?.context_id === "ctx_moscow_real_estate_v01" && Array.isArray(candidate.messages);
}

function messageNow(actor: Message["actor"], text: string): Message {
  return { id: `msg_${Date.now()}_${actor}`, actor, text, occurredAt: new Date().toISOString() };
}

function isResearchRequest(text: string): boolean {
  const lower = text.toLocaleLowerCase("es");
  return ["investiga", "investigar", "research", "regulator", "socioecon", "evidencia adversa", "dossier", "contexto político", "contexto cultural"].some((token) => lower.includes(token));
}

export function InvestigationShell() {
  const [payload, setPayload] = useState<PrototypeInvestigationPayload>(() => createInitialInvestigation("es"));
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [theme, setTheme] = useState<Theme>("dark");
  const [locale, setLocale] = useState<Locale>("es");
  const [draft, setDraft] = useState("");
  const [requestState, setRequestState] = useState<RequestState>("idle");
  const [claimFilter, setClaimFilter] = useState<ClaimFilter>("TODOS");
  const [showInterpretation, setShowInterpretation] = useState(true);
  const [includePrivateKnowledge, setIncludePrivateKnowledge] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        const parsed: unknown = JSON.parse(raw);
        if (isPersistedState(parsed)) {
          setPayload(normaliseInvestigationPayload(parsed.payload));
          setMessages(parsed.messages);
          setTheme(parsed.theme);
          setIncludePrivateKnowledge(parsed.includePrivateKnowledge);
          setLocale(parsed.payload.context.locale);
          document.documentElement.dataset.theme = parsed.theme;
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    const persisted: PersistedShellState = {
      schemaVersion: 2,
      payload,
      messages,
      theme,
      includePrivateKnowledge
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
  }, [hydrated, includePrivateKnowledge, messages, payload, theme]);

  const selected = useMemo(() => findSelectedOpportunity(payload), [payload]);
  const selectedClaims = useMemo(() => claimsForSelectedOpportunity(payload), [payload]);
  const visibleClaims = useMemo(
    () => claimFilter === "TODOS" ? selectedClaims : selectedClaims.filter((claim) => claim.kind === claimFilter),
    [claimFilter, selectedClaims]
  );
  const selectedClaimId = payload.context.selection.claim_ids[0] ?? null;
  const selectedEvidenceId = payload.context.selection.evidence_ids[0] ?? null;
  const selectedClaim = payload.claims.find((claim) => claim.claim_id === selectedClaimId) ?? null;
  const selectedEvidence = payload.evidence.find((item) => item.evidence_id === selectedEvidenceId) ?? null;
  const effectiveLens = payload.context.lens === "AUTO" ? "GLOBE" : payload.context.lens;
  const researchRun = selectedResearchRun(payload);
  const researchDossier = selectedResearchDossier(payload);
  const researchClaims = researchRun
    ? payload.candidate_claims.filter((claim) => researchRun.candidate_claim_ids.includes(claim.candidate_claim_id))
    : [];
  const researchUnknowns = researchRun
    ? payload.unknowns.filter((unknown) => researchRun.unknown_ids.includes(unknown.unknown_id))
    : [];

  function toggleTheme() {
    const nextTheme: Theme = theme === "dark" ? "light" : "dark";
    setTheme(nextTheme);
    document.documentElement.dataset.theme = nextTheme;
  }

  function chooseLens(lens: Lens) {
    setPayload((current) => updateContext(
      current,
      (context) => {
        context.lens = lens;
        context.lens_reason = lens === "AUTO" ? "La intención geográfica mantiene Globe como lente efectiva." : "Selección explícita del usuario.";
        context.history.push(nextHistoryEvent(context, "LENS_CHANGED"));
        return context;
      },
      `Lente ${lens} activada con el contexto preservado.`
    ));
  }

  function chooseOpportunity(opportunityId: string) {
    const opportunity = payload.opportunities.find((item) => item.opportunity_id === opportunityId);
    if (!opportunity) return;
    setClaimFilter("TODOS");
    setPayload((current) => {
      const next = updateContext(
        current,
        (context) => {
          context.selection.opportunity_ids = [opportunityId];
          context.selection.claim_ids = [];
          context.selection.evidence_ids = [];
          context.selection.graph_node_ids = ["entity_moscow", opportunityId];
          context.rail_mode = "OPPORTUNITY";
          context.history.push(nextHistoryEvent(context, "OPPORTUNITY_SELECTED"));
          return context;
        },
        `${opportunity.name} seleccionado y sincronizado en todas las superficies.`
      );
      return { ...next, focus: { opportunity_id: opportunityId, claim_id: null, evidence_id: null } };
    });
  }

  function chooseClaim(claim: Claim) {
    const evidence = evidenceForClaim(payload, claim)[0] ?? null;
    setPayload((current) => {
      const next = updateContext(
        current,
        (context) => {
          context.selection.claim_ids = [claim.claim_id];
          context.selection.evidence_ids = evidence ? [evidence.evidence_id] : [];
          context.rail_mode = evidence ? "EVIDENCE" : "CLAIM";
          context.history.push(nextHistoryEvent(context, "CLAIM_SELECTED"));
          return context;
        },
        `Claim ${claim.claim_id} seleccionado con su procedencia.`
      );
      return {
        ...next,
        focus: {
          opportunity_id: current.context.selection.opportunity_ids[0] ?? null,
          claim_id: claim.claim_id,
          evidence_id: evidence?.evidence_id ?? null
        }
      };
    });
  }

  function changeHorizon(horizon: "12M" | "24M" | "36M") {
    setPayload((current) => updateContext(
      current,
      (context) => {
        context.time.horizon_label = horizon;
        context.filters.horizon = horizon === "12M" ? "12 meses" : horizon === "24M" ? "12–24 meses" : "36 meses";
        context.history.push(nextHistoryEvent(context, "TIME_HORIZON_CHANGED"));
        return context;
      },
      `Horizonte cambiado a ${horizon} sin perder la selección.`
    ));
  }

  function saveTrail() {
    setPayload((current) => updateContext(
      current,
      (context) => {
        context.saved_trail_id = context.saved_trail_id ?? "trail_moscow_real_estate_v01";
        context.history.push(nextHistoryEvent(context, "TRAIL_SAVED"));
        return context;
      },
      "Investigation Trail guardado localmente como fixture de prototipo."
    ));
  }

  function changeLocale(nextLocale: Locale) {
    setLocale(nextLocale);
    setPayload((current) => updateContext(
      current,
      (context) => {
        context.locale = nextLocale;
        context.history.push(nextHistoryEvent(context, "LOCALE_CHANGED"));
        return context;
      },
      `Locale cambiado a ${nextLocale}; el texto fuente conserva su idioma original.`
    ));
  }

  async function executeMessage(text: string) {
    setMessages((current) => [...current, messageNow("user", text)]);
    setRequestState("processing");
    try {
      const result = isResearchRequest(text)
        ? await runResearch({ question: text, locale, includePrivateKnowledge, payload })
        : await runNavigatorCommand({ message: text, locale, payload });
      setPayload(normaliseInvestigationPayload(result));
      setMessages((current) => [...current, messageNow("axignal", result.explanation)]);
      setRequestState("idle");
    } catch {
      setMessages((current) => [...current, messageNow("axignal", "No he modificado el contexto porque la orden no pudo ejecutarse. Puedes reintentarlo sin perder el estado actual.")]);
      setRequestState("error");
    }
  }

  async function submitMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || requestState === "processing") return;
    setDraft("");
    await executeMessage(text);
  }

  return (
    <main className="shell" data-current-theme={theme} data-context-version={payload.context.version}>
      <header className="topbar">
        <a className="brand" href="#" aria-label="AXIGNAL home">AXIGNAL</a>
        <div className="context-path">
          <span>Moscú, Rusia</span><b>/</b><span>Real Estate</span><b>/</b><span>{payload.context.time.horizon_label}</span><b>/</b><span>v{payload.context.version}</span>
        </div>
        <nav className="lens-switch" aria-label="Seleccionar lente">
          {lensOptions.map((item) => (
            <button key={item} type="button" aria-pressed={payload.context.lens === item} onClick={() => chooseLens(item)}>{item}</button>
          ))}
        </nav>
        <label className="search"><span>⌕</span><input aria-label="Buscar" placeholder="Buscar entidades, temas, fuentes…" /></label>
        <select aria-label="Idioma" value={locale} onChange={(event) => changeLocale(event.target.value as Locale)}>
          {localeOptions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        <button className="icon-button" type="button" onClick={toggleTheme} aria-label="Cambiar tema">{theme === "dark" ? "☾" : "☀"}</button>
      </header>

      <aside className="rail-nav" aria-label="Navegación primaria">
        <button aria-label="Inicio">⌂</button><button className="active" aria-label="Globe">◎</button><button aria-label="Graph">⌘</button><button aria-label="Oportunidades">◇</button><button aria-label="Claims">▱</button><button aria-label="Trails">↺</button>
        <span className="avatar">AN</span>
      </aside>

      <section className="navigator panel" aria-label="AXIGNAL Navigator">
        <div className="panel-title">
          <strong>AXIGNAL NAVIGATOR</strong>
          <span className={requestState === "processing" ? "online processing" : "online"}>● {requestState === "processing" ? "RESEARCHING" : requestState === "error" ? "RETRY" : "ONLINE"}</span>
        </div>
        <div className="messages" aria-live="polite">
          {messages.map((message) => (
            <article key={message.id} className={`message ${message.actor}`}>
              <div><strong>{message.actor === "user" ? "TÚ" : "AXIGNAL"}</strong><time suppressHydrationWarning>{new Date(message.occurredAt).toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" })}</time></div>
              <p>{message.text}</p>
              {message.actor === "axignal" && <button type="button" onClick={() => setShowInterpretation((value) => !value)}>Ver interpretación</button>}
            </article>
          ))}
        </div>
        {showInterpretation && (
          <div className="interpretation context-inspector">
            <span>INTERPRETACIÓN ACTIVA</span>
            <b>{payload.context.lens} → {effectiveLens}</b>
            <small>{payload.context.lens_reason}</small>
            <small>Coverage: {payload.context.coverage.status} · History: {payload.context.history.length}</small>
            <label className="private-memory-toggle">
              <input
                type="checkbox"
                checked={includePrivateKnowledge}
                onChange={(event) => setIncludePrivateKnowledge(event.target.checked)}
              />
              Memoria privada sintética para ResearchRun
            </label>
          </div>
        )}
        <button
          className="research-shortcut"
          type="button"
          disabled={requestState === "processing"}
          onClick={() => executeMessage("Investiga el contexto regulatorio y socioeconómico de esta oportunidad")}
        >
          Investigar oportunidad
        </button>
        <form className="composer" onSubmit={submitMessage}>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Orden, pregunta o investigación…" aria-label="Mensaje para AXIGNAL" disabled={requestState === "processing"} />
          <button type="submit" aria-label="Enviar" disabled={requestState === "processing"}>➤</button>
        </form>
      </section>

      <section className="workspace panel">
        <div className="canvas-toolbar">
          <strong>{payload.context.lens === "AUTO" ? "AUTO · GLOBE" : payload.context.lens} VIEW</strong>
          <span>{selected.name} · contexto sincronizado</span>
          <span className="synthetic-badge">SYNTHETIC</span>
          <button type="button" onClick={saveTrail}>{payload.context.saved_trail_id ? "Trail guardado" : "Guardar Trail"}</button>
        </div>
        <PrimaryCanvas payload={payload} />
        <div className="timeline" aria-label="Timeline de investigación">
          <button type="button" aria-label="Reproducir">▶</button>
          <select aria-label="Horizonte" value={payload.context.time.horizon_label} onChange={(event) => changeHorizon(event.target.value as "12M" | "24M" | "36M")}>
            <option value="12M">12M</option><option value="24M">24M</option><option value="36M">36M</option>
          </select>
          <div className="timeline-track"><i /><i /><i className="selected" /><i /><i /></div><span>HOY</span>
        </div>
        <div className="metrics">
          <article><span>OPORTUNIDADES EN FIXTURE</span><strong>{payload.opportunities.length}</strong><small>Contexto versionado</small></article>
          <article><span>POTENCIAL SELECCIONADO</span><strong>{selected.expected_return_label}</strong><small>Estimación prototipo</small></article>
          <article><span>CONFIANZA</span><strong>{Math.round(selected.confidence * 100)}%</strong><small>No es recomendación</small></article>
          <article><span>CANDIDATE CLAIMS</span><strong>{researchRun?.candidate_claim_ids.length ?? 0}</strong><small>No admitidos</small></article>
          <article><span>HISTORIAL</span><strong>{payload.context.history.length}</strong><small>Eventos persistentes</small></article>
        </div>
      </section>

      <aside className="right-column" data-has-research={Boolean(researchRun)}>
        <section className="opportunities panel">
          <div className="panel-title"><strong>OPORTUNIDADES ({payload.opportunities.length})</strong><span>Ordenar: Potencial</span></div>
          {payload.opportunities.map((opportunity) => (
            <button className="opportunity" data-selected={opportunity.opportunity_id === selected.opportunity_id} key={opportunity.opportunity_id} type="button" onClick={() => chooseOpportunity(opportunity.opportunity_id)}>
              <span><strong>{opportunity.name}</strong><em>{opportunity.level}</em></span>
              <span>Retorno prototipo <b>{opportunity.expected_return_label}</b></span>
              <span>Confianza <Confidence value={opportunity.confidence} /></span>
            </button>
          ))}
        </section>

        <section className="research-panel panel" aria-label="ResearchRun">
          <div className="panel-title">
            <strong>RESEARCH RUN</strong>
            <span>{researchRun?.state ?? "NO INICIADO"}</span>
          </div>
          {!researchRun && <p className="empty-state">Solicita una investigación para crear un plan visible, recuperar fuentes autorizadas y generar propuestas trazables.</p>}
          {researchRun && (
            <div className="research-content">
              <div className="research-status">
                <span className="proposal-badge">PROPUESTA · NO ADMITIDA</span>
                <strong>{researchRun.question}</strong>
                <small>{researchRun.research_run_id} · presupuesto máx. {(researchRun.budgets.max_cost_minor_units / 100).toLocaleString("es-ES", { style: "currency", currency: "EUR" })}</small>
              </div>
              <div className="research-sources">
                {researchRun.source_plan.map((source) => (
                  <article key={source.source_result_id} data-domain={source.domain} data-status={source.status}>
                    <strong>{source.source_class}</strong><span>{source.label}</span><small>{source.status} · {source.note}</small>
                  </article>
                ))}
              </div>
              <div className="research-progress" aria-label="Progreso de ResearchRun">
                {researchRun.progress.map((step) => <span key={step.step} data-status={step.status}>{step.status === "COMPLETED" ? "✓" : "○"} {step.step}</span>)}
              </div>
              <div className="candidate-claims">
                {researchClaims.map((claim) => (
                  <article key={claim.candidate_claim_id} data-kind={claim.kind}>
                    <span>{claim.kind}</span><p>{claim.text}</p><small>{claim.state} · canonical_claim_id: null</small>
                  </article>
                ))}
              </div>
              {researchUnknowns.map((unknown) => <div className="research-unknown" key={unknown.unknown_id}><strong>UNKNOWN</strong><p>{unknown.text}</p><small>{unknown.reason}</small></div>)}
              {researchDossier && (
                <div className="research-dossier">
                  <strong>{researchDossier.title}</strong>
                  <p>{researchDossier.summary}</p>
                  <small>{researchDossier.status} · {researchDossier.sections.length} secciones · memoria privada {researchDossier.private_context_used ? "usada" : "no usada"}</small>
                </div>
              )}
            </div>
          )}
        </section>

        <section className="claims panel">
          <div className="panel-title"><strong>CLAIM &amp; EVIDENCE RAIL</strong><span>{selected.name}</span></div>
          <div className="claim-tabs">
            {(["TODOS", "HECHO", "INFERENCIA", "PREDICCIÓN", "CONTRADICCIÓN", "DESCONOCIDO"] as ClaimFilter[]).map((item) => (
              <button key={item} className={claimFilter === item ? "active" : undefined} type="button" onClick={() => setClaimFilter(item)}>{item === "TODOS" ? "Todos" : item}</button>
            ))}
          </div>
          <div className="coverage-strip" data-status={payload.context.coverage.status}>
            <strong>{payload.context.coverage.status}</strong><span>{payload.context.coverage.summary}</span>
          </div>
          {visibleClaims.map((claim) => (
            <article className="claim" data-kind={claim.kind} data-selected={claim.claim_id === selectedClaimId} key={claim.claim_id}>
              <span className="claim-kind">{claim.kind}</span>
              <p>{claim.text}</p>
              <small>{claim.confidence === null ? "Confianza no calculable" : `Confianza ${Math.round(claim.confidence * 100)}%`} · {claim.evidence_ids.length} evidencia(s)</small>
              <button type="button" onClick={() => chooseClaim(claim)}>VER</button>
              {claim.claim_id === selectedClaimId && selectedEvidence && (
                <div className="evidence-detail" data-relationship={selectedEvidence.relationship}>
                  <strong>{selectedEvidence.title}</strong>
                  <span>{selectedEvidence.source} · {selectedEvidence.as_of}</span>
                  <small>{selectedEvidence.relationship} · evidencia sintética de prototipo</small>
                </div>
              )}
            </article>
          ))}
          {visibleClaims.length === 0 && <p className="empty-state">No hay claims de este tipo para la oportunidad seleccionada.</p>}
          {selectedClaim && <button className="view-all" type="button" onClick={() => chooseClaim(selectedClaim)}>Evidencia seleccionada: {selectedClaim.claim_id} →</button>}
        </section>
      </aside>
    </main>
  );
}
