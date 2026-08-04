"use client";

import {
  Bell,
  ArrowLeft,
  BookOpen,
  BriefcaseBusiness,
  Building2,
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
  icon?: ComponentType<{ size?: number; strokeWidth?: number }>;
  asset?: string;
  capability?: string;
};

const primary: NavItem[] = [
  { href: "/axent", label: "AXENT", asset: "/axent.svg" },
  { href: "/command-center", label: "Command Center", icon: Zap },
  { href: "/opportunities", label: "Opportunities", icon: Search },
  { href: "/investigations", label: "Investigations", icon: Globe2 },
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

function focusable(container: HTMLElement | null): HTMLElement[] {
  if (!container) return [];
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'
    )
  ).filter((element) => !element.hasAttribute("hidden") && element.getAttribute("aria-hidden") !== "true");
}

function trapFocus(event: KeyboardEvent, container: HTMLElement | null) {
  if (event.key !== "Tab") return;
  const items = focusable(container);
  if (items.length === 0) {
    event.preventDefault();
    container?.focus();
    return;
  }
  const first = items[0]!;
  const last = items[items.length - 1]!;
  const active = document.activeElement;
  if (event.shiftKey && (active === first || !container?.contains(active))) {
    event.preventDefault();
    last.focus();
  } else if (!event.shiftKey && active === last) {
    event.preventDefault();
    first.focus();
  }
}

function GlobalNavigation({
  collapsed,
  capabilities,
  workspace,
  onNavigate
}: {
  collapsed: boolean;
  capabilities: ReadonlySet<string>;
  workspace: ShellWorkspaceContext | null | undefined;
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
            {item.asset ? <img className={styles.navAsset} src={item.asset} alt="" width={18} height={18} /> : item.icon ? <item.icon size={18} strokeWidth={1.65} /> : null}
            {!collapsed && <span>{item.label}</span>}
          </Link>
        ))}
      </div>
      {workspace ? (
        <div className={`${styles.navGroup} ${styles.mobileWorkspaceGroup}`} aria-label="Current workspace sections">
          <strong>{workspace.title}</strong>
          {workspaceSections.map(([slug, label]) => {
            const href = `/workspaces/${workspace.id}/${slug}`;
            return (
              <Link
                className={`${styles.navLink} ${styles.secondaryLink}`}
                data-active={pathname === href}
                href={href}
                key={slug}
                onClick={onNavigate}
                aria-current={pathname === href ? "page" : undefined}
              >
                <span>{label}</span>
              </Link>
            );
          })}
        </div>
      ) : null}
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
            {item.asset ? <img className={styles.navAsset} src={item.asset} alt="" width={17} height={17} /> : item.icon ? <item.icon size={17} strokeWidth={1.65} /> : null}
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
  const searchTriggerRef = useRef<HTMLButtonElement>(null);
  const commandDialogRef = useRef<HTMLElement>(null);
  const mobileMenuRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const mobileCloseRef = useRef<HTMLButtonElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const notificationsButtonRef = useRef<HTMLButtonElement>(null);
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
    if (!searchOpen) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : searchTriggerRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event: KeyboardEvent) => trapFocus(event, commandDialogRef.current);
    window.addEventListener("keydown", handleKeyDown);
    queueMicrotask(() => searchRef.current?.focus());
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previous?.focus();
    };
  }, [searchOpen]);

  useEffect(() => {
    if (!mobileOpen) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : mobileMenuRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const handleKeyDown = (event: KeyboardEvent) => trapFocus(event, sidebarRef.current);
    window.addEventListener("keydown", handleKeyDown);
    queueMicrotask(() => mobileCloseRef.current?.focus());
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      previous?.focus();
    };
  }, [mobileOpen]);

  useEffect(() => {
    if (!notificationsOpen) return;
    const closeOutside = (event: PointerEvent) => {
      const target = event.target as Node;
      if (!notificationsRef.current?.contains(target) && !notificationsButtonRef.current?.contains(target)) {
        setNotificationsOpen(false);
      }
    };
    window.addEventListener("pointerdown", closeOutside);
    return () => window.removeEventListener("pointerdown", closeOutside);
  }, [notificationsOpen]);

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
      {mobileOpen ? <button type="button" className={styles.mobileScrim} aria-label="Close navigation overlay" onClick={() => setMobileOpen(false)} tabIndex={-1} /> : null}
      <aside
        ref={sidebarRef}
        className={styles.sidebar}
        data-open={mobileOpen}
        role={mobileOpen ? "dialog" : undefined}
        aria-modal={mobileOpen ? true : undefined}
        aria-label={mobileOpen ? "Mobile product navigation" : undefined}
        tabIndex={mobileOpen ? -1 : undefined}
      >
        <div className={styles.brandRow}>
          <Link href="/axent" className={styles.brand} aria-label="AXIGNAL AXENT" onClick={() => setMobileOpen(false)}>
            <img src="/brand/axignal-isotipo.svg" alt="" width="26" height="26" />
            {!collapsed && <strong>AXIGNAL</strong>}
          </Link>
          <button ref={mobileCloseRef} type="button" className={styles.iconButton} onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18} /></button>
        </div>
        <GlobalNavigation collapsed={collapsed} capabilities={capabilitySet} workspace={workspaceContext} onNavigate={() => setMobileOpen(false)} />
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
        <button ref={mobileMenuRef} type="button" className={styles.mobileMenu} onClick={() => setMobileOpen(true)} aria-label="Open navigation" aria-expanded={mobileOpen}><Menu size={20} /></button>
        <div className={styles.organisation} aria-label={`Current organisation: ${identity.organisation}`}>
          <Building2 size={16} /><span>{identity.organisation}</span>
        </div>
        <button ref={searchTriggerRef} className={styles.searchTrigger} type="button" onClick={() => setSearchOpen(true)} aria-haspopup="dialog">
          <Search size={16} /><span>Search opportunities, entities, sources…</span><kbd aria-label="Command K on Apple, Control K on Windows and Linux"><span aria-hidden="true">⌘ K&nbsp; / &nbsp;Ctrl K</span></kbd>
        </button>
        <span className={styles.entitlement}><span />{identity.entitlementLabel}</span>
        <label className={styles.localeSelect}>
          <span className={styles.srOnly}>Language</span>
          <select value={locale} onChange={(event) => onLocaleChange(event.target.value as ShellLocale)}>
            {(Object.keys(localeLabels) as ShellLocale[]).map((value) => <option key={value} value={value}>{value.toUpperCase()} · {localeLabels[value]}</option>)}
          </select>
        </label>
        <button ref={notificationsButtonRef} type="button" className={styles.iconButton} onClick={() => setNotificationsOpen((value) => !value)} aria-expanded={notificationsOpen} aria-controls="subscriber-notifications" aria-haspopup="dialog" aria-label="Notifications"><Bell size={18} /></button>
        <Link className={styles.iconButton} href="/help" aria-label="Help"><CircleHelp size={18} /></Link>
        <span className={styles.headerAvatar} aria-label={`Signed in as ${identity.name}`}>{identity.name.slice(0, 1)}</span>
        {notificationsOpen && <div ref={notificationsRef} id="subscriber-notifications" className={styles.popover} role="dialog" aria-modal="false" aria-label="Notifications"><strong>2 items require attention</strong><Link href="/workspaces" onClick={() => setNotificationsOpen(false)}>Blocking evidence expires in 4 days</Link><Link href="/workspaces" onClick={() => setNotificationsOpen(false)}>Amendment review is waiting</Link></div>}
      </header>

      {workspaceMatch && workspaceContext && <WorkspaceNavigation workspace={workspaceContext} compact={collapsed} />}
      <main id="subscriber-main" className={styles.main} data-with-workspace={Boolean(workspaceMatch)} tabIndex={-1}>{children}</main>

      {searchOpen && (
        <div className={styles.dialogBackdrop} role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSearchOpen(false)}>
          <section ref={commandDialogRef} className={styles.commandDialog} role="dialog" aria-modal="true" aria-labelledby="command-title" tabIndex={-1}>
            <div className={styles.commandInput}>
              <Command size={18} /><input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submitSearch()} placeholder="Search or enter a command" aria-label="Search or enter a command" /><button type="button" onClick={() => setSearchOpen(false)} aria-label="Close command palette"><X size={18} /></button>
            </div>
            <h2 id="command-title">Navigate</h2>
            <div className={styles.commandResults}>
              {[...primary, ...secondary].filter((item) => (!item.capability || capabilitySet.has(item.capability)) && item.label.toLowerCase().includes(query.toLowerCase())).map((item) => <button type="button" key={item.href} onClick={() => { router.push(item.href); setSearchOpen(false); }}>{item.asset ? <img className={styles.navAsset} src={item.asset} alt="" width={17} height={17} /> : item.icon ? <item.icon size={17} /> : null}<span>{item.label}</span></button>)}
            </div>
            <footer><span><kbd>Enter</kbd> open</span><span><kbd>Esc</kbd> close</span></footer>
          </section>
        </div>
      )}
    </div>
  );
}
