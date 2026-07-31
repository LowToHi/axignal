"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import styles from "./seat-governance-bridge.module.css";

type RoleId =
  | "ORG_OWNER"
  | "ORG_ADMIN"
  | "B2G_MANAGER"
  | "RESEARCH_OPERATOR"
  | "BID_REVIEWER"
  | "VIEWER"
  | "BILLING_ADMIN"
  | "AUDITOR";

type SeatEntitlement = {
  seat_entitlement_id: string;
  plan_code: string;
  billing_model: "FLAT_TIER";
  seat_capacity: number;
  state: "ACTIVE" | "READ_ONLY" | "SUSPENDED" | "CANCELLED";
  policy_version: string;
  valid_from: string;
  valid_until: string | null;
};

type Member = {
  membership_id: string;
  principal_id: string;
  email_normalized: string;
  status: "ACTIVE" | "SUSPENDED" | "REVOKED" | "EXPIRED";
  roles: RoleId[];
  joined_at: string;
  revoked_at: string | null;
};

type Invitation = {
  invitation_id: string;
  operation_id: string;
  email_normalized: string;
  requested_role_id: RoleId;
  status: "PENDING" | "ACCEPTED" | "EXPIRED" | "REVOKED" | "DELIVERY_FAILED";
  delivery_provider: "TEST" | "SMTP";
  invited_at: string;
  expires_at: string;
  accepted_at: string | null;
  revoked_at: string | null;
};

type SeatSummary = {
  seat_entitlement: SeatEntitlement;
  active_seats: number;
  reserved_seats: number;
  occupied_seats: number;
  available_seats: number;
  members: Member[];
  invitations: Invitation[];
};

type ApiError = {
  error?: string;
  detail?: string | Array<{ msg?: string }>;
};

const roles: Array<{ id: Exclude<RoleId, "ORG_OWNER">; label: string }> = [
  { id: "ORG_ADMIN", label: "Organisation admin" },
  { id: "B2G_MANAGER", label: "B2G manager" },
  { id: "RESEARCH_OPERATOR", label: "Research operator" },
  { id: "BID_REVIEWER", label: "Bid reviewer" },
  { id: "VIEWER", label: "Viewer" },
  { id: "BILLING_ADMIN", label: "Billing admin" },
  { id: "AUDITOR", label: "Auditor" }
];

function operationId(): string {
  return `op_seat_${crypto.randomUUID().replaceAll("-", "")}`;
}

function errorMessage(value: ApiError, fallback: string): string {
  if (typeof value.detail === "string") return value.detail;
  if (Array.isArray(value.detail)) {
    return value.detail.map((item) => item.msg).filter(Boolean).join(" · ") || fallback;
  }
  return value.error ?? fallback;
}

function planLabel(plan: string): string {
  if (plan === "PROFESSIONAL_MONTHLY") return "Professional";
  if (plan === "TEAM_MONTHLY") return "Team";
  if (plan === "TRIAL_7D") return "7-day trial";
  return plan;
}

export function SeatGovernanceBridge() {
  const [open, setOpen] = useState(false);
  const [summary, setSummary] = useState<SeatSummary | null>(null);
  const [needsBootstrap, setNeedsBootstrap] = useState(false);
  const [email, setEmail] = useState("");
  const [roleId, setRoleId] = useState<Exclude<RoleId, "ORG_OWNER">>("BID_REVIEWER");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testToken, setTestToken] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/organisation/seats", { cache: "no-store" });
      const body = (await response.json()) as SeatSummary | ApiError;
      if (!response.ok) {
        const message = errorMessage(body as ApiError, "Seat governance unavailable.");
        if (
          response.status === 403 &&
          ["seat_membership_required", "An active trial or paid package is required"].includes(message)
        ) {
          setNeedsBootstrap(message === "seat_membership_required");
          setSummary(null);
          setError(
            message === "seat_membership_required"
              ? null
              : "Activate a trial or paid package before allocating seats."
          );
          return;
        }
        throw new Error(message);
      }
      setSummary(body as SeatSummary);
      setNeedsBootstrap(false);
      setError(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Seat governance unavailable.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pendingInvitations = useMemo(
    () => summary?.invitations.filter((item) => item.status === "PENDING") ?? [],
    [summary?.invitations]
  );
  const activeMembers = useMemo(
    () => summary?.members.filter((item) => item.status === "ACTIVE") ?? [],
    [summary?.members]
  );

  async function post(path: string, body: object): Promise<Record<string, unknown>> {
    setBusy(true);
    setError(null);
    try {
      const response = await fetch(path, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(body)
      });
      const payload = (await response.json()) as Record<string, unknown> & ApiError;
      if (!response.ok) {
        throw new Error(errorMessage(payload, "Seat operation failed."));
      }
      await load();
      return payload;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Seat operation failed.");
      throw cause;
    } finally {
      setBusy(false);
    }
  }

  async function bootstrap() {
    await post("/api/organisation/seats/bootstrap-owner", {
      confirm_owner_bootstrap: true
    });
  }

  async function invite() {
    const payload = await post("/api/organisation/seats/invitations", {
      operation_id: operationId(),
      email,
      role_id: roleId
    });
    setEmail("");
    const candidate = payload.test_acceptance_token;
    setTestToken(typeof candidate === "string" ? candidate : null);
  }

  async function revokeInvitation(invitationId: string) {
    await post(`/api/organisation/seats/invitations/${invitationId}/revoke`, {
      confirm: true
    });
  }

  async function revokeMember(membershipId: string) {
    await post(`/api/organisation/seats/members/${membershipId}/revoke`, {
      confirm: true
    });
  }

  async function changeRole(membershipId: string, nextRole: RoleId) {
    await post(`/api/organisation/seats/members/${membershipId}/role`, {
      role_id: nextRole,
      confirm_role_change: true
    });
  }

  const launcherLabel = summary
    ? `SEATS · ${summary.occupied_seats}/${summary.seat_entitlement.seat_capacity}`
    : needsBootstrap
      ? "SEATS · SETUP"
      : "SEATS";

  return (
    <>
      <button
        type="button"
        className={styles.launcher}
        aria-expanded={open}
        aria-controls="axignal-seat-governance-panel"
        onClick={() => setOpen((value) => !value)}
      >
        {launcherLabel}
      </button>

      {open && (
        <aside
          id="axignal-seat-governance-panel"
          className={styles.panel}
          aria-label="Organisation seats and members"
        >
          <header className={styles.header}>
            <div>
              <h2>SEATS & MEMBERS</h2>
              <p>Tenant-scoped allocations, roles and invitation state.</p>
            </div>
            <button type="button" className={styles.secondary} onClick={() => setOpen(false)}>
              Close
            </button>
          </header>

          {needsBootstrap && (
            <section className={styles.card}>
              <h3>Initial owner allocation</h3>
              <p>
                The approved organisation owner must consume the first seat before other
                members can be invited.
              </p>
              <button type="button" className={styles.primary} disabled={busy} onClick={() => void bootstrap()}>
                Initialise owner seat
              </button>
            </section>
          )}

          {summary && (
            <>
              <section className={styles.capacity} aria-label="Seat capacity">
                <div>
                  <strong>{planLabel(summary.seat_entitlement.plan_code)}</strong>
                  <span>{summary.seat_entitlement.billing_model}</span>
                </div>
                <div className={styles.capacityNumber}>
                  {summary.occupied_seats}/{summary.seat_entitlement.seat_capacity}
                </div>
                <dl>
                  <div><dt>Active</dt><dd>{summary.active_seats}</dd></div>
                  <div><dt>Reserved</dt><dd>{summary.reserved_seats}</dd></div>
                  <div><dt>Available</dt><dd>{summary.available_seats}</dd></div>
                </dl>
                <p>
                  Seat state: {summary.seat_entitlement.state}. Pending invitations reserve
                  capacity until accepted, revoked or expired.
                </p>
              </section>

              <section className={styles.card}>
                <h3>Invite a member</h3>
                <label>
                  Work email
                  <input
                    type="email"
                    value={email}
                    placeholder="member@company.com"
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </label>
                <label>
                  Initial role
                  <select
                    value={roleId}
                    onChange={(event) => setRoleId(event.target.value as Exclude<RoleId, "ORG_OWNER">)}
                  >
                    {roles.map((role) => (
                      <option key={role.id} value={role.id}>{role.label}</option>
                    ))}
                  </select>
                </label>
                <button
                  type="button"
                  className={styles.primary}
                  disabled={busy || !email || summary.available_seats < 1 || summary.seat_entitlement.state !== "ACTIVE"}
                  onClick={() => void invite()}
                >
                  Reserve seat and send invitation
                </button>
                {summary.available_seats < 1 && (
                  <p className={styles.warning}>
                    Seat capacity exhausted. Upgrade the package or release a seat.
                  </p>
                )}
                {testToken && (
                  <p className={styles.testToken}>
                    TEST ONLY acceptance token: <code>{testToken}</code>
                  </p>
                )}
              </section>

              <section className={styles.card}>
                <h3>Active members</h3>
                <div className={styles.list}>
                  {activeMembers.map((member) => {
                    const currentRole = member.roles[0] ?? "VIEWER";
                    return (
                      <article key={member.membership_id} className={styles.row}>
                        <div>
                          <strong>{member.email_normalized}</strong>
                          <small>{member.principal_id}</small>
                        </div>
                        <select
                          aria-label={`Role for ${member.email_normalized}`}
                          value={currentRole}
                          disabled={busy}
                          onChange={(event) => void changeRole(
                            member.membership_id,
                            event.target.value as RoleId
                          )}
                        >
                          <option value="ORG_OWNER">Organisation owner</option>
                          {roles.map((role) => (
                            <option key={role.id} value={role.id}>{role.label}</option>
                          ))}
                        </select>
                        <button
                          type="button"
                          className={styles.danger}
                          disabled={busy}
                          onClick={() => void revokeMember(member.membership_id)}
                        >
                          Revoke
                        </button>
                      </article>
                    );
                  })}
                </div>
              </section>

              <section className={styles.card}>
                <h3>Pending invitations</h3>
                {pendingInvitations.length === 0 && <p>No pending invitations.</p>}
                <div className={styles.list}>
                  {pendingInvitations.map((invitation) => (
                    <article key={invitation.invitation_id} className={styles.row}>
                      <div>
                        <strong>{invitation.email_normalized}</strong>
                        <small>
                          {invitation.requested_role_id} · expires{" "}
                          {new Date(invitation.expires_at).toLocaleString()}
                        </small>
                      </div>
                      <button
                        type="button"
                        className={styles.danger}
                        disabled={busy}
                        onClick={() => void revokeInvitation(invitation.invitation_id)}
                      >
                        Revoke invitation
                      </button>
                    </article>
                  ))}
                </div>
              </section>
            </>
          )}

          <footer className={styles.footer}>
            <button type="button" className={styles.secondary} disabled={busy} onClick={() => void load()}>
              Refresh
            </button>
            <span>Stripe bills one package unit; AXIGNAL governs seat capacity.</span>
          </footer>
          {error && <p className={styles.error} role="alert">{error}</p>}
        </aside>
      )}
    </>
  );
}
