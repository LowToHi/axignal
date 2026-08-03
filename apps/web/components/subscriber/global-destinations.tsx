"use client";

import {
  ArrowRight,
  BellPlus,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  FileDown,
  Filter,
  FolderOpen,
  GitCompareArrows,
  Plus,
  Search,
  ShieldCheck
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { BillingBridge } from "@/components/billing-bridge";
import { HumanReviewBridge } from "@/components/human-review-bridge";
import { SeatGovernanceBridge } from "@/components/seat-governance-bridge";
import type { SubscriberWorkspaceBootstrap, SubscriberWorkspaceRecord } from "@/lib/subscriber-workspace-contract";

import { PageState } from "./page-state";
import styles from "./workspace-content.module.css";

function PageHeader({ eyebrow, title, description, children }: { eyebrow: string; title: string; description: string; children?: React.ReactNode }) {
  return <header className={styles.pageHeader}><div><span className={styles.eyebrow}>{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{children && <div className={styles.headerActions}>{children}</div>}</header>;
}

function workspaceHref(workspace: SubscriberWorkspaceRecord | undefined, section = "overview") {
  return workspace ? `/workspaces/${workspace.id}/${section}` : "/workspaces";
}

function CommandCenter({ bootstrap }: { bootstrap: SubscriberWorkspaceBootstrap }) {
  const workspace = bootstrap.route_data.workspaces[0];
  const opportunity = bootstrap.route_data.opportunities.find((item) => item.id === workspace?.opportunity_id);
  const blockers = workspace?.requirements.filter((item) => item.blocking && !["met", "not_applicable"].includes(item.status)).length ?? 0;
  return <div className={styles.page} data-testid="command-center"><PageHeader eyebrow="Command Center" title="What requires your attention now" description="Prioritised from persisted deadlines, blockers, amendments and approvals. Priority is not evidence and never changes readiness by itself."><Link className={styles.primary} href="/opportunities"><Search size={15} /> Find opportunities</Link><Link className={styles.secondary} href="/workspaces"><FolderOpen size={15} /> Open workspaces</Link></PageHeader>
    <div className={styles.metricStrip}><article><span>ACTIVE WORKSPACES</span><strong>{bootstrap.route_data.summary.active_workspaces}</strong><small>{blockers} blockers</small></article><article><span>DEADLINES · 30 DAYS</span><strong>{bootstrap.route_data.summary.deadlines_next_30_days}</strong><small>Source timezones preserved</small></article><article><span>APPROVALS WAITING</span><strong>{workspace?.commercial.approved_by ? 1 : 2}</strong><small>Human authority required</small></article><article><span>AMENDMENTS</span><strong>{workspace?.amendments.filter((item) => !item.acknowledged).length ?? 0}</strong><small>Impact review pending</small></article><article><span>EVIDENCE GAPS</span><strong>{bootstrap.route_data.summary.blocking_requirements}</strong><small>Across current pursuits</small></article></div>
    <section className={styles.section}><div className={styles.sectionHeader}><h2>ATTENTION QUEUE</h2><span>Server-ranked · explainable</span></div><div className={styles.attentionList}>
      <Link className={styles.attentionRow} href={workspaceHref(workspace, "requirements")}><span className={styles.critical}>BLOCKER</span><strong>{workspace?.requirements.find((item) => item.blocking && item.status !== "met")?.title ?? "Blocking requirement needs evidence"}</strong><small>{workspace?.title ?? "Workspace unavailable"}</small><em className={styles.status} data-tone="critical">Review required</em><ChevronRight size={16} /></Link>
      <Link className={styles.attentionRow} href={workspaceHref(workspace, "changes")}><span className={styles.warning}>AMENDMENT</span><strong>{workspace?.amendments.find((item) => !item.acknowledged)?.title ?? "No unacknowledged amendment"}</strong><small>Impact remains versioned and subscriber-controlled</small><em className={styles.status} data-tone="warning">Review impact</em><ChevronRight size={16} /></Link>
      <Link className={styles.attentionRow} href={workspaceHref(workspace, "clarifications")}><span className={styles.signal}>APPROVAL</span><strong>Clarification is ready for subscriber review</strong><small>AXIGNAL can prepare the handoff; your organisation sends it</small><em className={styles.status} data-tone="signal">Human action</em><ChevronRight size={16} /></Link>
      <Link className={styles.attentionRow} href={workspaceHref(workspace, "commercial")}><span>COMMERCIAL</span><strong>Commercial assumptions require subscriber authority</strong><small>Candidate values do not contribute to readiness until approved</small><em className={styles.status}>Owner needed</em><ChevronRight size={16} /></Link>
    </div></section>
    <div className={styles.split}><section className={styles.section}><div className={styles.sectionHeader}><h2>WORKSPACES</h2><Link className={styles.quiet} href="/workspaces">View all <ArrowRight size={14} /></Link></div><div className={styles.rowList}>{bootstrap.route_data.workspaces.map((item) => <Link className={styles.dataRow} href={workspaceHref(item)} key={item.id}><span className={styles.signal}>{item.requirements.filter((requirement) => requirement.status === "met").length}/{item.requirements.length}</span><strong>{item.title}</strong><small>{item.state} · {item.requirements.filter((requirement) => requirement.blocking && requirement.status !== "met").length} blockers</small><em className={styles.status} data-tone="warning">{new Date(item.deadline).toLocaleDateString()}</em><ChevronRight size={16} /></Link>)}</div></section><section className={styles.section}><div className={styles.sectionHeader}><h2>SAFE NEXT ACTIONS</h2><span>Authority bounded</span></div><div className={styles.sideSummary}><article><span>AXIGNAL CAN DO NOW</span><strong>Map amendment impact</strong><p>Prepare a reversible requirement diff without invalidating human decisions automatically.</p></article><article><span>SUBSCRIBER AUTHORITY</span><strong>Approve external clarification handoff</strong><p>No message is sent and no buyer relationship is represented by AXIGNAL.</p></article></div></section></div>
  </div>;
}

function Opportunities({ bootstrap }: { bootstrap: SubscriberWorkspaceBootstrap }) {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("ALL");
  const [compared, setCompared] = useState<string[]>([]);
  const inventory = useMemo(() => bootstrap.route_data.opportunities.map((item) => ({ id: item.id, title: item.title, buyer: item.buyer, country: item.jurisdiction, deadline: new Date(item.deadline).toLocaleString(), fit: item.fit === "high" ? "Strong evidence" : item.fit === "medium" ? "Review required" : "Evidence unknown", contradiction: item.unknowns.length ? `${item.unknowns.length} unknown` : "None recorded" })), [bootstrap]);
  const countries = useMemo(() => Array.from(new Set(inventory.map((item) => item.country))), [inventory]);
  const rows = useMemo(() => inventory.filter((item) => (country === "ALL" || item.country === country) && `${item.title} ${item.buyer}`.toLowerCase().includes(query.toLowerCase())), [country, inventory, query]);
  return <div className={styles.page} data-testid="opportunities-page"><PageHeader eyebrow="Global Opportunity Intelligence" title="Opportunities" description="Search admitted and candidate procurement records without collapsing source facts, AXIGNAL inference, subscriber context or unknowns."><Link className={styles.primary} href="/investigations"><Plus size={15} /> New investigation</Link>{compared.length > 1 && <Link className={styles.secondary} href={`/opportunities?compare=${compared.join(",")}`}><GitCompareArrows size={15} /> Compare {compared.length}</Link>}</PageHeader>
    <div className={styles.filters}><label><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search title or buyer" aria-label="Search opportunities" /></label><label><Filter size={15} /><select value={country} onChange={(event) => setCountry(event.target.value)} aria-label="Country"><option value="ALL">All countries</option>{countries.map((value) => <option value={value} key={value}>{value}</option>)}</select></label></div>
    <section className={styles.section}><div className={styles.sectionHeader}><h2>OPPORTUNITY INVENTORY</h2><span>{rows.length} engineering fixture records · source versions pinned</span></div><div className={styles.tableWrap}><table className={styles.table}><thead><tr><th scope="col">Compare</th><th scope="col">Opportunity</th><th scope="col">Deadline</th><th scope="col">Fit state</th><th scope="col">Contradictions</th><th scope="col">Actions</th></tr></thead><tbody>{rows.map((item) => { const linkedWorkspace = bootstrap.route_data.workspaces.find((workspace) => workspace.opportunity_id === item.id); return <tr key={item.id}><td><input aria-label={`Compare ${item.title}`} type="checkbox" checked={compared.includes(item.id)} onChange={(event) => setCompared((current) => event.target.checked ? [...current, item.id] : current.filter((id) => id !== item.id))} /></td><td><strong>{item.title}</strong><small>{item.country} · {item.buyer}</small></td><td>{item.deadline}</td><td><span className={styles.status}>{item.fit}</span></td><td>{item.contradiction}</td><td><div className={styles.inlineActions}><Link href={`/investigations?opportunity=${item.id}`}>Investigate</Link><Link href={linkedWorkspace ? workspaceHref(linkedWorkspace, "qualification") : `/opportunities?selected=${item.id}`}>Qualify</Link></div></td></tr>; })}</tbody></table></div></section>
  </div>;
}

function Workspaces({ bootstrap }: { bootstrap: SubscriberWorkspaceBootstrap }) {
  return <div className={styles.page} data-testid="workspaces-page"><PageHeader eyebrow="Opportunity Operations" title="Tender Workspaces" description="Qualification, preparation, collaboration, review, official-channel handoff and learning remain versioned and subscriber-controlled."><Link className={styles.primary} href="/opportunities"><Plus size={15} /> Open from opportunity</Link></PageHeader><section className={styles.section}><div className={styles.sectionHeader}><h2>ACTIVE PURSUITS</h2><span>{bootstrap.route_data.workspaces.length} active · tenant scoped</span></div><div className={styles.tableWrap}><table className={styles.table}><thead><tr><th>Workspace</th><th>State</th><th>Readiness</th><th>Deadline</th><th>Next action</th></tr></thead><tbody>{bootstrap.route_data.workspaces.map((workspace) => { const met = workspace.requirements.filter((item) => item.status === "met").length; const blockers = workspace.requirements.filter((item) => item.blocking && !["met", "not_applicable"].includes(item.status)).length; const readiness = workspace.requirements.length ? Math.round((met / workspace.requirements.length) * 100) : 0; return <tr key={workspace.id}><td><strong>{workspace.title}</strong><small>{workspace.opportunity_id} · revision {bootstrap.tenant.revision}</small></td><td>{workspace.state}</td><td><span className={styles.status} data-tone={blockers ? "warning" : "positive"}>{readiness}% · {blockers} blockers</span></td><td>{new Date(workspace.deadline).toLocaleString()}</td><td><Link className={styles.secondary} href={workspaceHref(workspace)}>Open workspace <ArrowRight size={14} /></Link></td></tr>; })}</tbody></table></div></section></div>;
}

function GenericDestination({ kind, onThemeChange }: { kind: string; onThemeChange: (theme: "dark" | "light") => void }) {
  const content: Record<string, { eyebrow: string; title: string; description: string; rows: [string,string,string][] }> = {
    libraries: { eyebrow:"Governed knowledge", title:"Libraries", description:"Evidence, approved reusable content and documents retain source, rights, tenant, version and authority state.", rows:[["Evidence library","142 current records","7 freshness reviews"],["Approved response knowledge","38 approved items","4 expire this quarter"],["Document templates","12 governed templates","Organisation scoped"]]},
    alerts: { eyebrow:"Monitoring", title:"Alerts", description:"Saved searches and notice changes create research candidates; attention never proves an opportunity.", rows:[["EU mobility data platforms","Daily","3 new candidate notices"],["Urban digital twins · ES/PT","Weekly","1 material amendment"],["Rail predictive maintenance","Daily","No new admitted records"]]},
    reports: { eyebrow:"Evidence-preserving output", title:"Reports", description:"Exports preserve provenance, contradictions, rights and decision authority. Unauthorised fields remain excluded.", rows:[["Pursuit readiness dossier","European Mobility Data Platform","Generated 2 Aug 2026"],["Decision ledger","Q3 active pursuits","Current through revision 84"],["Evidence freshness report","Organisation library","7 items require review"]]},
    methodology: { eyebrow:"Trust architecture", title:"Methodology", description:"The vector discovers; the graph contextualises; the runtime admits. AI output is never authoritative by itself.", rows:[["Epistemic states","Observed, calculated, inferred, predicted, unknown","Never collapsed"],["Opportunity assembly","Supporting, contradictory and unknown claims","Versioned subgraph"],["External authority","Subscriber decides, approves, communicates and submits","Human controlled"]]},
    help: { eyebrow:"Support", title:"Help", description:"Contextual guidance, keyboard shortcuts, methodology and recovery ownership remain consistent across the product.", rows:[["Keyboard navigation","Press Tab to move; Command/Ctrl+K opens search","WCAG 2.2 AA target"],["Data and evidence","How AXIGNAL distinguishes facts and inference","5 minute guide"],["External handoff","What AXIGNAL can prepare and what your organisation must do","Authority guide"]]}
  };
  if (kind === "settings") return <div className={styles.page}><PageHeader eyebrow="Organisation controls" title="Settings" description="Locale, appearance, notifications, privacy and security are explicit and reversible."/><section className={styles.section}><div className={styles.sectionHeader}><h2>APPEARANCE</h2><span>First-class theme parity</span></div><div className={styles.dataRow}><span>THEME</span><strong>Workspace appearance</strong><small>Stored on this device and reconciled by the server across navigation</small><div className={styles.inlineActions}><button type="button" onClick={() => onThemeChange("dark")}>Dark</button><button type="button" onClick={() => onThemeChange("light")}>Light</button></div></div></section><section className={styles.section}><div className={styles.sectionHeader}><h2>PRIVACY & SECURITY</h2><span>Server authoritative</span></div><div className={styles.sideSummary}><article><span>PRIVATE KNOWLEDGE</span><strong>Explicit use only</strong><p>Private tenant context is never included in a ResearchRun without an explicit scoped choice.</p></article><article><span>SESSION</span><strong>Passkey-ready · bounded session</strong><p>Step-up is required for consequential organisation and external-handoff operations.</p></article></div></section></div>;
  const selected = content[kind] ?? content.help!;
  return <div className={styles.page}><PageHeader eyebrow={selected.eyebrow} title={selected.title} description={selected.description}>{kind === "reports" && <button className={styles.primary} type="button" onClick={() => window.print()}><FileDown size={15}/> Print current view</button>}{kind === "alerts" && <Link className={styles.primary} href="/opportunities?saveSearch=true"><BellPlus size={15}/> Create from search</Link>}</PageHeader><section className={styles.section}><div className={styles.sectionHeader}><h2>{selected.title.toUpperCase()}</h2><span>Tenant scoped</span></div><div className={styles.rowList}>{selected.rows.map(([title,detail,state]) => <div className={styles.dataRow} key={title}><span><CheckCircle2 size={15}/></span><strong>{title}</strong><small>{detail}</small><em className={styles.status}>{state}</em><ChevronRight size={16}/></div>)}</div></section></div>;
}

export function GlobalDestination({ pathname, onThemeChange, bootstrap }: { pathname: string; onThemeChange: (theme: "dark" | "light") => void; bootstrap: SubscriberWorkspaceBootstrap }) {
  if (pathname === "/" || pathname === "/command-center") return <CommandCenter bootstrap={bootstrap} />;
  if (pathname.startsWith("/opportunities")) return <Opportunities bootstrap={bootstrap} />;
  if (pathname === "/workspaces") return <Workspaces bootstrap={bootstrap} />;
  if (pathname === "/team") return <div className={styles.page}><PageHeader eyebrow="Organisation governance" title="Team" description="Members, invitations, roles, capacity and approvals are resolved by the server. Visible roles do not grant authority by themselves."/><SeatGovernanceBridge/><HumanReviewBridge/></div>;
  if (pathname === "/billing") return <div className={styles.page}><PageHeader eyebrow="Candidate commercial surface" title="Plan & Billing" description="Trial, entitlement, invoices and cancellation. Prices and activation remain candidate until the commercial gate passes."/><BillingBridge/></div>;
  if (["/libraries","/alerts","/reports","/settings","/methodology","/help"].includes(pathname)) return <GenericDestination kind={pathname.slice(1)} onThemeChange={onThemeChange}/>;
  return <PageState state="empty" title="Destination not implemented" detail="The route is declared but has no operational surface on this engineering revision."/>;
}
