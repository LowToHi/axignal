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
  LogOut,
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

import { purgeAxentLocalHistory } from "@/lib/axent-local-history";

import {
  localeNames,
  shellCopy,
  shellLocales,
  type ShellLocale,
  type ShellNavKey,
  type WorkspaceSectionKey
} from "./subscriber-localization";
import styles from "./product-shell.module.css";

export type { ShellLocale } from "./subscriber-localization";

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
  key: ShellNavKey;
  icon?: ComponentType<{ size?: number; strokeWidth?: number }>;
  asset?: string;
  capability?: string;
};

const primary: NavItem[] = [
  { href: "/axent", key: "axent", asset: "/axent.svg" },
  { href: "/command-center", key: "commandCenter", icon: Zap },
  { href: "/opportunities", key: "opportunities", icon: Search },
  { href: "/investigations", key: "investigations", icon: Globe2 },
  { href: "/workspaces", key: "workspaces", icon: BriefcaseBusiness },
  { href: "/libraries", key: "libraries", icon: LibraryBig },
  { href: "/alerts", key: "alerts", icon: Bell },
  { href: "/reports", key: "reports", icon: FileChartColumn },
  { href: "/team", key: "team", icon: Users }
];

const secondary: NavItem[] = [
  { href: "/billing", key: "billing", icon: CreditCard, capability: "billing:view" },
  { href: "/settings", key: "settings", icon: Settings },
  { href: "/methodology", key: "methodology", icon: ShieldCheck },
  { href: "/help", key: "help", icon: CircleHelp }
];

const workspaceSections: readonly [WorkspaceSectionKey, WorkspaceSectionKey][] = [
  ["overview", "overview"],
  ["qualification", "qualification"],
  ["requirements", "requirements"],
  ["evidence", "evidence"],
  ["documents", "documents"],
  ["workplan", "workplan"],
  ["clarifications", "clarifications"],
  ["changes", "changes"],
  ["commercial", "commercial"],
  ["team", "team"],
  ["submission", "submission"],
  ["outcome", "outcome"],
  ["audit", "audit"]
];

type ActiveShellCopy = (typeof shellCopy)[ShellLocale];

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
  copy,
  onNavigate
}: {
  collapsed: boolean;
  capabilities: ReadonlySet<string>;
  workspace: ShellWorkspaceContext | null | undefined;
  copy: ActiveShellCopy;
  onNavigate: () => void;
}) {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(true);
  const visibleSecondary = secondary.filter((item) => !item.capability || capabilities.has(item.capability));
  return (
    <nav className={styles.globalNav} aria-label={copy.productNavigation}>
      <div className={styles.navGroup}>
        {primary.map((item) => {
          const label = copy.nav[item.key];
          return (
            <Link
              className={styles.navLink}
              data-active={current(item.href, pathname)}
              href={item.href}
              key={item.href}
              onClick={onNavigate}
              aria-current={current(item.href, pathname) ? "page" : undefined}
              title={collapsed ? label : undefined}
            >
              {item.asset ? <img className={styles.navAsset} src={item.asset} alt="" width={18} height={18} /> : item.icon ? <item.icon size={18} strokeWidth={1.65} /> : null}
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </div>
      {workspace ? (
        <div className={`${styles.navGroup} ${styles.mobileWorkspaceGroup}`} aria-label={copy.currentWorkspaceSections}>
          <strong>{workspace.title}</strong>
          {workspaceSections.map(([slug, key]) => {
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
                <span>{copy.sections[key]}</span>
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
          title={collapsed ? copy.more : undefined}
        >
          <FolderKanban size={18} strokeWidth={1.65} />
          {!collapsed && <><span>{copy.more}</span><ChevronDown className={styles.navChevron} size={14} /></>}
        </button>
        {(moreOpen || collapsed) && visibleSecondary.map((item) => {
          const label = copy.nav[item.key];
          return (
            <Link
              className={`${styles.navLink} ${styles.secondaryLink}`}
              data-active={current(item.href, pathname)}
              href={item.href}
              key={item.href}
              onClick={onNavigate}
              aria-current={current(item.href, pathname) ? "page" : undefined}
              title={collapsed ? label : undefined}
            >
              {item.asset ? <img className={styles.navAsset} src={item.asset} alt="" width={17} height={17} /> : item.icon ? <item.icon size={17} strokeWidth={1.65} /> : null}
              {!collapsed && <span>{label}</span>}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function WorkspaceNavigation({ workspace, compact, copy }: { workspace: ShellWorkspaceContext; compact: boolean; copy: ActiveShellCopy }) {
  const pathname = usePathname();
  return (
    <aside className={styles.workspaceNav} data-compact={compact} aria-label={copy.tenderWorkspaceNavigation}>
      <Link href="/workspaces" className={styles.backLink}><ArrowLeft size={15} /> <span>{copy.backToWorkspaces}</span></Link>
      <div className={styles.workspaceIdentity}>
        <span>{copy.governedProcurement}</span>
        <strong>{workspace.title}</strong>
        <small>{workspace.sourceLabel} · {workspace.deadlineLabel}</small>
      </div>
      <div className={styles.readiness} aria-label={copy.readiness(workspace.readiness)}>
        <span><b>{workspace.readiness}%</b> {copy.readinessLabel}</span><i><em style={{ width: `${workspace.readiness}%` }} /></i><small>{copy.blockingRequirements(workspace.blockingRequirements)}</small>
      </div>
      <nav aria-label={copy.workspaceSections}>
        {workspaceSections.map(([slug, key]) => {
          const href = `/workspaces/${workspace.id}/${slug}`;
          return <Link key={slug} href={href} data-active={pathname === href} aria-current={pathname === href ? "page" : undefined}>{copy.sections[key]}</Link>;
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
  const copy = shellCopy[locale];
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const [signOutError, setSignOutError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement>(null);
  const searchTriggerRef = useRef<HTMLButtonElement>(null);
  const commandDialogRef = useRef<HTMLElement>(null);
  const mobileMenuRef = useRef<HTMLButtonElement>(null);
  const sidebarRef = useRef<HTMLElement>(null);
  const mobileCloseRef = useRef<HTMLButtonElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);
  const notificationsButtonRef = useRef<HTMLButtonElement>(null);
  const accountRef = useRef<HTMLDivElement>(null);
  const accountButtonRef = useRef<HTMLButtonElement>(null);
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
        setAccountOpen(false);
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
    if (!notificationsOpen && !accountOpen) return;
    const closeOutside = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        notificationsOpen &&
        !notificationsRef.current?.contains(target) &&
        !notificationsButtonRef.current?.contains(target)
      ) {
        setNotificationsOpen(false);
      }
      if (
        accountOpen &&
        !accountRef.current?.contains(target) &&
        !accountButtonRef.current?.contains(target)
      ) {
        setAccountOpen(false);
      }
    };
    window.addEventListener("pointerdown", closeOutside);
    return () => window.removeEventListener("pointerdown", closeOutside);
  }, [accountOpen, notificationsOpen]);

  function submitSearch() {
    const value = query.trim();
    if (!value) return;
    router.push(`/opportunities?q=${encodeURIComponent(value)}`);
    setSearchOpen(false);
  }

  async function signOut() {
    if (signingOut) return;
    setSigningOut(true);
    setSignOutError(null);
    try {
      const response = await fetch("/api/auth/logout", { method: "POST" });
      if (!response.ok) throw new Error(copy.logoutFailed(response.status));
      purgeAxentLocalHistory(window.localStorage);
      window.location.assign("/");
    } catch (cause) {
      setSignOutError(cause instanceof Error ? cause.message : copy.logoutUnknown);
      setSigningOut(false);
    }
  }

  const commandItems = [...primary, ...secondary]
    .filter((item) => !item.capability || capabilitySet.has(item.capability))
    .map((item) => ({ ...item, label: copy.nav[item.key] }))
    .filter((item) => item.label.toLocaleLowerCase(locale).includes(query.toLocaleLowerCase(locale)));

  return (
    <div className={styles.shell} data-sidebar-collapsed={collapsed} data-testid="product-shell">
      <a className={styles.skipLink} href="#subscriber-main">{copy.skipToMain}</a>
      {fixtureMode && <div className={styles.fixtureBanner} role="status">{copy.fixtureNotice}</div>}
      {mobileOpen ? <button type="button" className={styles.mobileScrim} aria-label={copy.closeNavigationOverlay} onClick={() => setMobileOpen(false)} tabIndex={-1} /> : null}
      <aside
        ref={sidebarRef}
        className={styles.sidebar}
        data-open={mobileOpen}
        role={mobileOpen ? "dialog" : undefined}
        aria-modal={mobileOpen ? true : undefined}
        aria-label={mobileOpen ? copy.mobileProductNavigation : undefined}
        tabIndex={mobileOpen ? -1 : undefined}
      >
        <div className={styles.brandRow}>
          <Link href="/axent" className={styles.brand} aria-label="AXIGNAL AXENT" onClick={() => setMobileOpen(false)}>
            <img src="/brand/axignal-isotipo.svg" alt="" width="26" height="26" />
            {!collapsed && <strong>AXIGNAL</strong>}
          </Link>
          <button ref={mobileCloseRef} type="button" className={styles.iconButton} onClick={() => setMobileOpen(false)} aria-label={copy.closeNavigation}><X size={18} /></button>
        </div>
        <GlobalNavigation collapsed={collapsed} capabilities={capabilitySet} workspace={workspaceContext} copy={copy} onNavigate={() => setMobileOpen(false)} />
        <button className={styles.collapseButton} type="button" onClick={() => setCollapsed((value) => !value)} aria-label={collapsed ? copy.expandNavigation : copy.collapseNavigation}>
          {collapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
          {!collapsed && <span>{copy.collapse}</span>}
        </button>
        <div className={styles.profile}>
          <span aria-hidden="true">{identity.name.split(" ").map((part) => part[0]).join("").slice(0, 2)}</span>
          {!collapsed && <div><strong>{identity.name}</strong><small>{identity.roles.join(" · ")}</small></div>}
        </div>
      </aside>

      <header className={styles.header}>
        <button ref={mobileMenuRef} type="button" className={styles.mobileMenu} onClick={() => setMobileOpen(true)} aria-label={copy.openNavigation} aria-expanded={mobileOpen}><Menu size={20} /></button>
        <div className={styles.organisation} aria-label={copy.currentOrganisation(identity.organisation)}>
          <Building2 size={16} /><span>{identity.organisation}</span>
        </div>
        <button ref={searchTriggerRef} className={styles.searchTrigger} type="button" onClick={() => setSearchOpen(true)} aria-haspopup="dialog">
          <Search size={16} /><span>{copy.searchTrigger}</span><kbd aria-label={copy.shortcutDescription}><span aria-hidden="true">⌘ K&nbsp; / &nbsp;Ctrl K</span></kbd>
        </button>
        <span className={styles.entitlement}><span />{identity.entitlementLabel}</span>
        <label className={styles.localeSelect}>
          <span className={styles.srOnly}>{copy.language}</span>
          <select aria-label={copy.language} value={locale} onChange={(event) => onLocaleChange(event.target.value as ShellLocale)}>
            {shellLocales.map((value) => <option key={value} value={value}>{value.toUpperCase()} · {localeNames[value]}</option>)}
          </select>
        </label>
        <button ref={notificationsButtonRef} type="button" className={styles.iconButton} onClick={() => { setNotificationsOpen((value) => !value); setAccountOpen(false); }} aria-expanded={notificationsOpen} aria-controls="subscriber-notifications" aria-haspopup="dialog" aria-label={copy.notifications}><Bell size={18} /></button>
        <Link className={styles.iconButton} href="/help" aria-label={copy.help}><CircleHelp size={18} /></Link>
        <button
          ref={accountButtonRef}
          type="button"
          className={styles.headerAvatar}
          aria-label={copy.accountMenuFor(identity.name)}
          aria-expanded={accountOpen}
          aria-controls="subscriber-account-menu"
          aria-haspopup="menu"
          onClick={() => { setAccountOpen((value) => !value); setNotificationsOpen(false); }}
        >
          {identity.name.slice(0, 1)}
        </button>
        {notificationsOpen && <div ref={notificationsRef} id="subscriber-notifications" className={styles.popover} role="dialog" aria-modal="false" aria-label={copy.notificationsDialog}><strong>{copy.notificationsAttention}</strong><Link href="/workspaces" onClick={() => setNotificationsOpen(false)}>{copy.evidenceExpiry}</Link><Link href="/workspaces" onClick={() => setNotificationsOpen(false)}>{copy.amendmentWaiting}</Link></div>}
        {accountOpen && <div ref={accountRef} id="subscriber-account-menu" className={styles.popover} role="menu" aria-label={copy.accountMenu} style={{ right: 12 }}>
          <strong>{identity.name}</strong>
          <small>{identity.email}</small>
          <Link className={styles.navLink} href="/settings" role="menuitem" onClick={() => setAccountOpen(false)}><Settings size={16} /><span>{copy.accountSettings}</span></Link>
          <button className={styles.navLink} type="button" role="menuitem" disabled={signingOut} onClick={() => void signOut()}><LogOut size={16} /><span>{signingOut ? copy.signingOut : copy.signOut}</span></button>
          {signOutError ? <small role="alert">{signOutError}</small> : null}
        </div>}
      </header>

      {workspaceMatch && workspaceContext && <WorkspaceNavigation workspace={workspaceContext} compact={collapsed} copy={copy} />}
      <main id="subscriber-main" className={styles.main} data-with-workspace={Boolean(workspaceMatch)} tabIndex={-1}>{children}</main>

      {searchOpen && (
        <div className={styles.dialogBackdrop} role="presentation" onMouseDown={(event) => event.target === event.currentTarget && setSearchOpen(false)}>
          <section ref={commandDialogRef} className={styles.commandDialog} role="dialog" aria-modal="true" aria-labelledby="command-title" tabIndex={-1}>
            <div className={styles.commandInput}>
              <Command size={18} /><input ref={searchRef} value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === "Enter" && submitSearch()} placeholder={copy.searchCommand} aria-label={copy.searchCommand} /><button type="button" onClick={() => setSearchOpen(false)} aria-label={copy.closeCommandPalette}><X size={18} /></button>
            </div>
            <h2 id="command-title">{copy.navigate}</h2>
            <div className={styles.commandResults}>
              {commandItems.map((item) => <button type="button" key={item.href} onClick={() => { router.push(item.href); setSearchOpen(false); }}>{item.asset ? <img className={styles.navAsset} src={item.asset} alt="" width={17} height={17} /> : item.icon ? <item.icon size={17} /> : null}<span>{item.label}</span></button>)}
            </div>
            <footer><span><kbd>Enter</kbd> {copy.enterOpen}</span><span><kbd>Esc</kbd> {copy.escapeClose}</span></footer>
          </section>
        </div>
      )}
    </div>
  );
}
