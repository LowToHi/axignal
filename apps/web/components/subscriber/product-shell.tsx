"use client";

import {
  Bell,
  ArrowLeft,
  BookOpen,
  BriefcaseBusiness,
  Building2,
  ChartNoAxesCombined,
  ChevronDown,
  CircleHelp,
  Command,
  CreditCard,
  FileChartColumn,
  FolderKanban,
  Globe2,
  LibraryBig,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  Settings,
  ShieldCheck,
  Users,
  X,
  Zap
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  type ComponentType,
  type PropsWithChildren,
  useEffect,
  useMemo,
  useRef,
  useState
} from "react";

import styles from "./product-shell.module.css";

export type ShellLocale = "en" | "es" | "fr" | "de" | "pt" | "it";

export type ShellIdentity = {
  name: string;
  email: string;
  organisation: string;
  roles: string[];
  entitlementLabel: string;
};

export type ShellWorkspaceContext = {
  id: string;
  title: string;
  sourceLabel: string;
  deadlineLabel: string;
  readiness: number;
  blockingRequirements: number;
};

type NavItem = {
  href: string;
  label: string;
  icon: ComponentType<{ size?: number; strokeWidth?: number }>;
  capability?: string;
};

const primary: NavItem[] = [
  { href: "/", label: "Command Center", icon: Zap },
  { href: "/opportunities", label: "Opportunities", icon: Globe2 },
  { href: "/investigations", label: "Investigations", icon: ChartNoAxesCombined },
  { href: "/workspaces", label: "Workspaces", icon: BriefcaseBusiness },
  { href: "/libraries", label: "Libraries", icon: LibraryBig },
  { href: "/alerts", label: "Alerts", icon: Bell },
  { href: "/reports", label: "Reports", icon: FileChartColumn },
  { href: "/team", label: "Team", icon: Users }
];

const secondary: NavItem[] = [
  { href: "/billing", label: "Plan & Billing", icon: CreditCard, capability: "billing:view" },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/methodology", label: "Methodology", icon: ShieldCheck },
  { href: "/help", label: "Help", icon: CircleHelp }
];

const workspaceSections = [
  ["overview", "Overview"],
  ["qualification", "Qualification"],
  ["requirements", "Requirements"],
  ["evidence", "Evidence"],
  ["documents", "Documents"],
  ["workplan", "Workplan"],
  ["clarifications", "Clarifications"],
  ["changes", "Changes"],
  ["commercial", "Commercial"],
  ["team", "Team & Approvals"],
  ["submission", "Submission"],
  ["outcome", "Outcome & Learning"],
  ["audit", "Audit"]
] as const;

const localeLabels: Record<ShellLocale, string> = {
  en: "English",
  es: "Español",
  fr: "Français",
  de: "Deutsch",
  pt: "Português",
  it: "Italiano"
};

function current(href: string, pathname: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

function GlobalNavigation({
  collapsed,
  capabilities,
  onNavigate
}: {
  collapsed: boolean;
  capabilities: ReadonlySet<string>;
  onNavigate: () => void;
}) {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(true);
  const visibleSecondary = secondary.filter((item) => !item.capability || capabilities.has(item.capability));
  return (
    <nav className={styles.globalNav} aria-label="Product navigation">
      <div className={styles.navGroup}>
        {primary.map((item) => (
          <Link
            className={styles.navLink}
            data-active={current(item.href, pathname)}
            href={item.href}
            key={item.href}
            onClick={onNavigate}
            aria-current={current(item.href, pathname) ? "page" : undefined}
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={18} strokeWidth={1.65} />
            {!collapsed && <span>{item.label}</span>}
          </Link>
        ))}
      </div>
      <div className={styles.navGroup}>
        <button
          type="button"
          className={styles.navLink}
          aria-expanded={moreOpen}
          onClick={() => setMoreOpen((value) => !value)}
          title={collapsed ? "More" : undefined}
        >
          <FolderKanban size={18} strokeWidth={1.65} />
          {!collapsed && <><span>More</span><ChevronDown className={styles.navChevron} size={14} /></>}
        </button>
        {(moreOpen || collapsed) && visibleSecondary.map((item) => (
          <Link
            className={`${styles.navLink} ${styles.secondaryLink}`}
            data-active={current(item.href, pathname)}
            href={item.href}
            key={item.href}
            onClick={onNavigate}
            aria-current={current(item.href, pathname) ? "page" : undefined}
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={17} strokeWidth={1.65} />
            {!collapsed && <span>{item.label}</span>}
          </Link>
        ))}
      </div>
    </nav>
  );
}

function WorkspaceNavigation({ workspace, compact }: { workspace: ShellWorkspaceContext; compact: boolean }) {
  const pathname = usePathname();
  return (
    <aside className={styles.workspaceNav} data-compact={compact} aria-label="Tender workspace navigation">
      <Link href="/workspaces" className={styles.backLink}><ArrowLeft size={15} /> <span>Back to Workspaces</span></Link>
      <div className={styles.workspaceIdentity}>
        <span>GOVERNED PROCUREMENT · TENANT SCOPED</span>
        <strong>{workspace.title}</strong>
        <small>{workspace.sourceLabel} · {workspace.deadlineLabel}</small>
      </div>
      <div className={styles.readiness} aria-label={`Readiness ${workspace.readiness} percent`}>
        <span><b>{workspace.readiness}%</b> readiness</span><i><em style={{ width: `${workspace.readiness}%` }} /></i><small>{workspace.blockingRequirements} blocking requirements</small>
      </div>
      <nav aria-label="Workspace sections">
        {workspaceSections.map(([slug, label]) => {
          const href = `/workspaces/${workspace.id}/${slug}`;
          return <Link key={slug} href={href} data-active={pathname === href} aria-current={pathname === href ? "page" : undefined}>{label}</Link>;
        })}
      </nav>
    </aside>
  );
}

export function ProductShell({
  children,
  identity,
  capabilities = [],
  fixtureMode = false,
  workspaceContext,
  locale,
  onLocaleChange
}: PropsWithChildren<{
  identity: ShellIdentity;
  capabilities?: string[];
  fixtureMode?: boolean;
  workspaceContext?: ShellWorkspaceContext | null;
  locale: ShellLocale;
  onLocaleChange: (locale: ShellLocale) => void;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const capabilitySet = useMemo(() => new Set(capabilities), [capabilities]);
  const workspaceMatch = pathname.match(/^\/workspaces\/([^/]+)(?:\/|$)/);

  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen(true);
      }
      if (event.key === "Escape") {
        setSearchOpen(false);
        setNotificationsOpen(false);
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", shortcut);
    return () => window.removeEventListener("keydown", shortcut);
  }, []);

  useEffect(() => {
    if (searchOpen) searchRef.current?.focus();
  }, [searchOpen]);

  function submitSearch() {
    const value = query.trim();
    if (!value) return;
    router.push(`/opportunities?q=${encodeURIComponent(value)}`);
    setSearchOpen(false);
  }

  return (
    <div className={styles.shell} data-sidebar-collapsed={collapsed} data-testid="product-shell">
      <a className={styles.skipLink} href="#subscriber-main">Skip to main content</a>
      {fixtureMode && <div className={styles.fixtureBanner} role="status">ENGINEERING FIXTURE · NOT LIVE DATA</div>}
      <aside className={styles.sidebar} data-open={mobileOpen}>
        <div className={styles.brandRow}>
          <Link href="/" className={styles.brand} aria-label="AXIGNAL Command Center">
            <img src="/brand/axignal-isotipo.svg" alt="" width="26" height="26" />
            {!collapsed && <strong>AXIGNAL</strong>}
          </Link>
          <button type="button" className={styles.iconButton} onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <GlobalNavigation collapsed={collapsed} capabilities={capabilitySet} onNavigate={() => setMobileOpen(false)} />
        <button className={styles.collapseButton} type="button" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}>
          {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          {!collapsed && <span>Collapse</span>}
        </button>
        <div className={styles.profile}>
          <span aria-hidden="true">{identity.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span>
          {!collapsed && <div><strong>{identity.name}</strong><small>{identity.roles.join(" · ")}</small></div>}
        </div>
      </aside>

      <header className={styles.header}>
        <button type="button" className={styles.mobileMenu} onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20} /></button>
        <button className={styles.organisation} type="button" aria-label="Current organisation">
          <Building2 size={16} /><span>{identity.organisation}</span><ChevronDown size={14} />
        </button>
        <button className={styles.searchTrigger} type="button" onClick={() => setSearchOpen(true)}>
          <Search size={16} /><span>Search opportunities, entities, sources…</span><kbd aria-label="Command K on Apple, Control K on Windows and Linux"><span aria-hidden="true">⌘ K&nbsp; / &nbsp;Ctrl K</span></kbd>
        </button>
        <span className={styles.entitlement}><span />{identity.entitlementLabel}</span>
        <label className={styles.localeSelect}>
          <span className={styles.srOnly}>Language</span>
          <select value={locale} onChange={(event) => onLocaleChange(event.target.value as ShellLocale)}>
            {(Object.keys(localeLabels) as ShellLocale[]).map((value) => <option key={value} value={value}>{value.toUpperCase()} · {localeLabels[value]}</option>)}
          </select>
        </label>
        <button type="button" className={styles.iconButton} onClick={() => setNotificationsOpen((value) => !value)} aria-expanded={notificationsOpen} aria-label="Notifications"><Bell size={18} /></button>
        <Link className={styles.iconButton} href="/help" aria-label="Help"><CircleHelp size={18} /></Link>
        <span className={styles.headerAvatar} aria-label={`${identity.name}, account menu`}>{identity.name.slice(0, 1)}</span>
        {notificationsOpen && <div className={styles.popover} role="region" aria-label="Notifications"><strong>2 items require attention</strong><Link href="/workspaces">Blocking evidence expires in 4 days</Link><Link href="/workspaces">Amendment review is waiting</Link></div>}
      </header>

      {workspaceMatch && workspaceContext && <WorkspaceNavigation workspace={workspaceContext} compact={collapsed} />}
      <main id="subscriber-main" className={styles.main} data-with-workspace={Boolean(workspaceMatch)} tabIndex={-1}>{children}</main>

      {searchOpen && (
        <div className={styles.dialogBackdrop} role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSearchOpen(false)}>
          <section className={styles.commandDialog} role="dialog" aria-modal="true" aria-labelledby="command-title">
            <div className={styles.commandInput}>
              <Command size={18} /><input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submitSearch()} placeholder="Search or enter a command" aria-label="Search or enter a command" /><button type="button" onClick={() => setSearchOpen(false)} aria-label="Close command palette"><X size={18} /></button>
            </div>
            <h2 id="command-title">Navigate</h2>
            <div className={styles.commandResults}>
              {[...primary, ...secondary].filter((item) => item.label.toLowerCase().includes(query.toLowerCase())).map((item) => <button type="button" key={item.href} onClick={() => { router.push(item.href); setSearchOpen(false); }}><item.icon size={17} /><span>{item.label}</span></button>)}
            </div>
            <footer><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></footer>
          </section>
        </div>
      )}
    </div>
  );
}
