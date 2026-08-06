"use client";

import { useMemo, useState } from "react";

import type { FounderAdminData, SeoPageCandidate } from "@/lib/organic-server";

import styles from "./founder-admin.module.css";

type ModuleId =
  | "overview"
  | "seo"
  | "pages"
  | "citations"
  | "alerts"
  | "crm"
  | "customers"
  | "billing"
  | "risk"
  | "sources"
  | "operations"
  | "settings"
  | "audit";

const navigation: Array<{
  id: ModuleId;
  label: string;
  icon: string;
  group: "Growth" | "Commercial" | "Platform";
}> = [
  { id: "overview", label: "Overview", icon: "◫", group: "Growth" },
  { id: "seo", label: "Organic SEO", icon: "⌁", group: "Growth" },
  { id: "pages", label: "Pages & Sitemaps", icon: "▤", group: "Growth" },
  { id: "citations", label: "AI Citations", icon: "✦", group: "Growth" },
  { id: "alerts", label: "Tender Alerts", icon: "◉", group: "Growth" },
  { id: "crm", label: "CRM", icon: "◎", group: "Commercial" },
  { id: "customers", label: "Customers & Trials", icon: "♙", group: "Commercial" },
  { id: "billing", label: "Billing", icon: "€", group: "Commercial" },
  { id: "risk", label: "Risk & Abuse", icon: "◇", group: "Platform" },
  { id: "sources", label: "Sources & Coverage", icon: "⊙", group: "Platform" },
  { id: "operations", label: "Operations", icon: "⚙", group: "Platform" },
  { id: "settings", label: "Settings", icon: "≡", group: "Platform" },
  { id: "audit", label: "Audit", icon: "✓", group: "Platform" }
];

function number(value: unknown): number {
  return typeof value === "number" ? value : Number(value ?? 0) || 0;
}

function Metric({ label, value, note }: { label: string; value: number | string; note: string }) {
  return (
    <article className={styles.metric}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  );
}

function StateBadge({ state }: { state: string }) {
  return <span className={styles.state} data-state={state}>{state}</span>;
}

function GovernancePanel({ data }: { data: FounderAdminData }) {
  return (
    <section className={styles.governance}>
      <div>
        <span className={styles.eyebrow}>AUTHORITY CHAIN</span>
        <h2>Generated does not mean indexable.</h2>
        <p>Every public URL must pass demand, inventory, freshness, uniqueness, source coverage and content-depth gates before a founder can publish a versioned snapshot.</p>
      </div>
      <div className={styles.boundaries}>
        {data.overview.truth_boundaries.map((boundary) => (
          <span key={boundary}>{boundary}</span>
        ))}
      </div>
    </section>
  );
}

function Overview({ data }: { data: FounderAdminData }) {
  const seo = data.overview.seo;
  const crm = data.overview.crm;
  const alerts = data.overview.alerts;
  const citations = data.overview.citations;
  return (
    <>
      <div className={styles.metricGrid}>
        <Metric label="Published pages" value={number(seo.published)} note="Current admitted snapshots" />
        <Metric label="Indexable queue" value={number(seo.indexable)} note="Awaiting founder publication" />
        <Metric label="Noindex" value={number(seo.noindex)} note="Rejected by policy" />
        <Metric label="CRM contacts" value={number(crm.contacts)} note={`${number(crm.mql)} marketing-qualified`} />
        <Metric label="Active alerts" value={number(alerts.active)} note={`${number(alerts.pending)} awaiting confirmation`} />
        <Metric label="AI citations" value={number(citations.total)} note={`${number(citations.last_30_days)} in 30 days`} />
      </div>
      <GovernancePanel data={data} />
      <section className={styles.twoColumn}>
        <article className={styles.panel}>
          <header><div><span>ACQUISITION SYSTEM</span><h3>Organic discovery funnel</h3></div><StateBadge state="CONTROLLED" /></header>
          <div className={styles.funnel}>
            {["Source ingestion", "IndexabilityGate", "Published intelligence", "Tender alert", "Passwordless signup", "Trial activation", "Paid package"].map((item, index) => (
              <div key={item}><b>{String(index + 1).padStart(2, "0")}</b><span>{item}</span></div>
            ))}
          </div>
        </article>
        <article className={styles.panel}>
          <header><div><span>FOUNDER CONTROL</span><h3>Activation boundaries</h3></div><StateBadge state="FAIL-CLOSED" /></header>
          <ul className={styles.checkList}>
            <li><b>Public indexing</b><span>Environment gate + published snapshot</span></li>
            <li><b>Tender alerts</b><span>Bot verification + double opt-in</span></li>
            <li><b>Founder mutations</b><span>Recent AAL2 + server allowlist + DB principal</span></li>
            <li><b>Trial creation</b><span>Never triggered by SEO or alert capture</span></li>
            <li><b>AI citations</b><span>Observed evidence, never inferred endorsement</span></li>
          </ul>
        </article>
      </section>
    </>
  );
}

function score(page: SeoPageCandidate): number {
  return Math.round(
    ([page.demand_score, page.data_quality_score, page.uniqueness_score, page.source_coverage_score, page.content_depth_score]
      .map(number)
      .reduce((total, item) => total + item, 0) / 5) * 100
  );
}

function SeoPages({ data, mode }: { data: FounderAdminData; mode: "seo" | "pages" }) {
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const pages = useMemo(
    () => [...data.pages].sort((left, right) => score(right) - score(left)),
    [data.pages]
  );

  async function mutate(action: "evaluate" | "publish", page: SeoPageCandidate) {
    setBusy(`${action}:${page.page_id}`);
    setMessage(null);
    const response = await fetch("/api/admin/organic", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ action, pageId: page.page_id, snapshot: page })
    });
    const body = (await response.json().catch(() => ({}))) as Record<string, unknown>;
    setBusy(null);
    if (!response.ok) {
      setMessage(typeof body.error === "string" ? body.error : "Operation denied.");
      return;
    }
    setMessage(action === "evaluate" ? "Indexability decision persisted." : "Versioned snapshot published.");
    window.setTimeout(() => window.location.reload(), 450);
  }

  return (
    <section className={styles.panel}>
      <header>
        <div>
          <span>{mode === "seo" ? "INDEXABILITY QUEUE" : "PUBLIC URL INVENTORY"}</span>
          <h3>{mode === "seo" ? "Programmatic SEO governance" : "Pages, snapshots and sitemaps"}</h3>
        </div>
        <div className={styles.headerMeta}>{pages.length} candidates · policy 1.0.0</div>
      </header>
      {message && <div className={styles.notice}>{message}</div>}
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead><tr><th>Page</th><th>Kind</th><th>Inventory</th><th>Buyers</th><th>Gate score</th><th>State</th><th>Authority</th></tr></thead>
          <tbody>
            {pages.map((page) => (
              <tr key={page.page_id} data-page-state={page.state}>
                <td><strong>{page.title}</strong><small>{page.canonical_path}</small></td>
                <td>{page.page_kind.replaceAll("_", " ")}</td>
                <td>{page.active_opportunity_count}</td>
                <td>{page.unique_buyer_count}</td>
                <td><div className={styles.score}><i style={{ width: `${score(page)}%` }} /><span>{score(page)}</span></div></td>
                <td><StateBadge state={page.state} /></td>
                <td><div className={styles.actions}>
                  <button disabled={busy !== null} onClick={() => mutate("evaluate", page)}>Evaluate</button>
                  <button disabled={busy !== null || page.state !== "INDEXABLE"} onClick={() => mutate("publish", page)}>Publish</button>
                </div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function CRM({ data }: { data: FounderAdminData }) {
  return (
    <section className={styles.panel}>
      <header><div><span>COMMERCIAL PIPELINE</span><h3>CRM contacts</h3></div><div className={styles.headerMeta}>Alerts and trials remain separate</div></header>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead><tr><th>Contact</th><th>Stage</th><th>Source</th><th>Score</th><th>Consent</th><th>Last touch</th></tr></thead>
          <tbody>
            {data.contacts.length === 0 ? <tr><td colSpan={6} className={styles.empty}>No CRM contacts have been admitted.</td></tr> : data.contacts.map((contact, index) => (
              <tr key={String(contact.contact_id ?? index)}>
                <td><strong>{String(contact.email_normalized ?? "—")}</strong><small>{String(contact.company_name ?? "Company not resolved")}</small></td>
                <td><StateBadge state={String(contact.lifecycle_stage ?? "LEAD")} /></td>
                <td>{String(contact.source ?? "—")}</td>
                <td>{String(contact.lead_score ?? 0)}</td>
                <td>{String(contact.consent_status ?? "PENDING")}</td>
                <td>{String(contact.last_touch_path ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Alerts({ data }: { data: FounderAdminData }) {
  return (
    <section className={styles.panel}>
      <header><div><span>LEAD CAPTURE</span><h3>Tender alerts</h3></div><div className={styles.headerMeta}>Double opt-in · no implicit tenant</div></header>
      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead><tr><th>Email</th><th>Market</th><th>Cadence</th><th>State</th><th>Source path</th></tr></thead>
          <tbody>
            {data.alerts.length === 0 ? <tr><td colSpan={5} className={styles.empty}>No alert subscriptions have been captured.</td></tr> : data.alerts.map((alert, index) => (
              <tr key={String(alert.subscription_id ?? index)}>
                <td>{String(alert.email_normalized ?? "—")}</td>
                <td>{String(alert.country_code ?? "—")} · {String(alert.sector_slug ?? "—")}</td>
                <td>{String(alert.cadence ?? "—")}</td>
                <td><StateBadge state={String(alert.state ?? "PENDING_CONFIRMATION")} /></td>
                <td>{String(alert.source_path ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

const moduleContracts: Record<Exclude<ModuleId, "overview" | "seo" | "pages" | "crm" | "alerts">, { title: string; status: string; description: string; controls: string[] }> = {
  citations: { title: "AI citation governance", status: "CONNECTED", description: "Measure observed citations across ChatGPT, Copilot, Google AI, Perplexity and other answer engines without converting mentions into unsupported endorsements.", controls: ["Provider and surface attribution", "HMAC-protected grounding query", "Cited URL and observation time", "Bing AI Performance import boundary", "ChatGPT referral UTM measurement"] },
  customers: { title: "Customers & controlled trials", status: "READ-ONLY", description: "Operational view across prepared, active, expired and converted trials. Trial authority remains in P25 and cannot be mutated from SEO modules.", controls: ["Trial state and expiry", "Seat occupancy", "Token and cost budget", "Conversion state", "Abuse decision history"] },
  billing: { title: "Billing and commercial packages", status: "BLOCKED", description: "Professional and Team packages remain candidate-only. The founder dashboard can observe lifecycle state but cannot enable live Stripe or alter signed price-book authority.", controls: ["MRR and package mix", "Stripe reconciliation", "Failed payment queue", "Downgrade conflicts", "Live activation gate"] },
  risk: { title: "Risk & abuse", status: "CONNECTED", description: "Identity, trial abuse and seat signals remain separate from CRM scoring. Risk decisions require evidence and never become marketing labels.", controls: ["Duplicate strong claims", "Weak-signal step-up", "Session revocations", "Credential compromise events", "Manual review overrides"] },
  sources: { title: "Sources & coverage", status: "CONTROLLED", description: "Manage procurement libraries as versioned sources rather than product identity. Coverage, freshness, rights and failure state feed the IndexabilityGate.", controls: ["Library health", "Jurisdiction coverage", "Freshness SLA", "Rights and attribution", "Schema drift"] },
  operations: { title: "Platform operations", status: "CONNECTED", description: "Observe queues, workers, database migrations, outbox lag and failed gates without giving the browser direct infrastructure authority.", controls: ["Worker and queue health", "ResearchRun throughput", "Outbox lag", "Migration state", "Evidence artifact retention"] },
  settings: { title: "Governed settings", status: "FAIL-CLOSED", description: "Policy versions and activation gates are visible here. Production credentials and irreversible switches remain outside browser authority.", controls: ["Indexability thresholds", "Locale rollout gates", "Crawler policy", "Sitemap partitions", "Provider connection status"] },
  audit: { title: "Founder audit", status: "APPEND-ONLY", description: "All SEO publication, citation import, CRM mutation and activation decisions are recorded with actor, target, version and timestamp.", controls: ["Publication events", "Indexability decisions", "Citation imports", "CRM lifecycle changes", "Configuration changes"] }
};

function ContractModule({ id }: { id: keyof typeof moduleContracts }) {
  const module = moduleContracts[id];
  return (
    <section className={styles.contractModule}>
      <div><span className={styles.eyebrow}>MODULE CONTRACT</span><h2>{module.title}</h2><p>{module.description}</p><StateBadge state={module.status} /></div>
      <ul>{module.controls.map((control) => <li key={control}><span>✓</span>{control}</li>)}</ul>
    </section>
  );
}

export function FounderAdminDashboard({ data, founderEmail }: { data: FounderAdminData; founderEmail: string }) {
  const [active, setActive] = useState<ModuleId>("overview");
  const groups = ["Growth", "Commercial", "Platform"] as const;
  return (
    <main className={styles.shell} data-testid="founder-admin-dashboard">
      <aside className={styles.sidebar}>
        <div className={styles.brand}><span>AXIGNAL</span><small>FOUNDER OS</small></div>
        <nav aria-label="Founder administration">
          {groups.map((group) => (
            <div className={styles.navGroup} key={group}>
              <p>{group}</p>
              {navigation.filter((item) => item.group === group).map((item) => (
                <button key={item.id} type="button" data-active={active === item.id} onClick={() => setActive(item.id)}>
                  <i>{item.icon}</i><span>{item.label}</span>
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className={styles.founder}><div>RL</div><span><b>Founder</b><small>{founderEmail}</small></span></div>
      </aside>
      <section className={styles.content}>
        <header className={styles.topbar}>
          <div><span>AXIGNAL CONTROL PLANE</span><h1>{navigation.find((item) => item.id === active)?.label}</h1></div>
          <div className={styles.topActions}><a href="/">Open product</a><span>Updated {new Date(data.generatedAt).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}</span></div>
        </header>
        <div className={styles.viewport}>
          {active === "overview" && <Overview data={data} />}
          {active === "seo" && <SeoPages data={data} mode="seo" />}
          {active === "pages" && <SeoPages data={data} mode="pages" />}
          {active === "crm" && <CRM data={data} />}
          {active === "alerts" && <Alerts data={data} />}
          {active !== "overview" && active !== "seo" && active !== "pages" && active !== "crm" && active !== "alerts" && <ContractModule id={active} />}
        </div>
      </section>
    </main>
  );
}
