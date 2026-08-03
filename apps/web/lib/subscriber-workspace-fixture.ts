import type {
  SubscriberWorkspaceAuditEvent,
  SubscriberWorkspaceEntitlement,
  SubscriberWorkspaceLocale,
  SubscriberWorkspaceOpportunity,
  SubscriberWorkspaceRecord,
  SubscriberWorkspaceRightsSnapshot,
  SubscriberWorkspaceRole,
  SubscriberWorkspaceTheme
} from "./subscriber-workspace-contract";

export const FIXTURE_DISCLOSURE = "ENGINEERING FIXTURE · NOT LIVE DATA" as const;

export type SubscriberWorkspaceActionReceipt = {
  digest: string;
  action_type: string;
  outcome: "persisted" | "rejected";
  tenant_revision: number;
  event: SubscriberWorkspaceAuditEvent;
  error?: {
    status: number;
    code: string;
    message: string;
    recoverable: boolean;
  };
};

export type SubscriberWorkspaceFixtureStore = {
  schema_version: "axignal.subscriber-workspace-store/v1";
  tenant: {
    id: string;
    name: string;
    revision: number;
  };
  entitlement: SubscriberWorkspaceEntitlement;
  preferences: {
    locale: SubscriberWorkspaceLocale;
    theme: SubscriberWorkspaceTheme;
  };
  opportunities: SubscriberWorkspaceOpportunity[];
  investigations: Array<{
    id: string;
    title: string;
    status: "active" | "paused" | "complete";
    updated_at: string;
    opportunity_ids: string[];
  }>;
  workspaces: SubscriberWorkspaceRecord[];
  rights_snapshot: SubscriberWorkspaceRightsSnapshot[];
  members: Array<{
    id: string;
    display_name: string;
    email: string;
    roles: SubscriberWorkspaceRole[];
  }>;
  events: SubscriberWorkspaceAuditEvent[];
  action_receipts: Record<string, SubscriberWorkspaceActionReceipt>;
};

const OBSERVED_AT = "2026-08-01T09:00:00.000Z";
const DEADLINE = "2026-09-18T12:00:00.000Z";

export function createSubscriberWorkspaceFixtureStore(
  tenantId = "axfx_tenant_northstar"
): SubscriberWorkspaceFixtureStore {
  const workspaceId = "axfx_ws_eu_cloud_001";
  const opportunities: SubscriberWorkspaceOpportunity[] = [
    {
      id: "axfx_opp_eu_cloud_001",
      version: "axfx_oppver_2026_08_01",
      title: "Sovereign cloud operations framework",
      buyer: "European Digital Infrastructure Agency",
      jurisdiction: "European Union",
      deadline: DEADLINE,
      status: "pursuing",
      fit: "high",
      confidence: 0.82,
      source_id: "axfx_source_ted_001",
      source_url: "https://ted.europa.eu/",
      observed_at: OBSERVED_AT,
      unknowns: ["Final security annex is not yet available"]
    },
    {
      id: "axfx_opp_city_data_002",
      version: "axfx_oppver_2026_07_30",
      title: "Urban data platform implementation and support",
      buyer: "Metropolitan Innovation Office",
      jurisdiction: "Portugal",
      deadline: "2026-10-06T15:00:00.000Z",
      status: "qualified",
      fit: "medium",
      confidence: 0.68,
      source_id: "axfx_source_portal_002",
      source_url: "https://base.gov.pt/",
      observed_at: "2026-07-30T14:30:00.000Z",
      unknowns: ["Consortium eligibility requires legal review"]
    }
  ];

  const workspaces: SubscriberWorkspaceRecord[] = [
    {
      id: workspaceId,
      opportunity_id: opportunities[0]!.id,
      title: "Sovereign cloud operations bid",
      state: "preparing",
      owner_id: "axfx_usr_bid_manager",
      deadline: DEADLINE,
      decision: "pursue",
      requirements: [
        {
          id: "axfx_req_iso_001",
          workspace_id: workspaceId,
          title: "ISO 27001 certification",
          category: "technical_eligibility",
          status: "met",
          blocking: true,
          owner_id: "axfx_usr_contributor",
          evidence_ids: ["axfx_evd_iso_001"],
          source_reference: "Notice §III.1.3",
          updated_at: OBSERVED_AT
        },
        {
          id: "axfx_req_residency_002",
          workspace_id: workspaceId,
          title: "EU data residency operating model",
          category: "delivery",
          status: "partial",
          blocking: true,
          owner_id: "axfx_usr_bid_manager",
          evidence_ids: [],
          source_reference: "Technical annex §4.2",
          updated_at: OBSERVED_AT
        },
        {
          id: "axfx_req_turnover_003",
          workspace_id: workspaceId,
          title: "Minimum annual turnover evidence",
          category: "financial_eligibility",
          status: "unknown",
          blocking: true,
          owner_id: null,
          evidence_ids: [],
          source_reference: "Notice §III.1.2",
          updated_at: OBSERVED_AT
        }
      ],
      evidence: [
        {
          id: "axfx_evd_iso_001",
          workspace_id: workspaceId,
          requirement_id: "axfx_req_iso_001",
          title: "ISO 27001 certificate — verified copy",
          evidence_type: "subscriber_document",
          status: "verified",
          source_reference: null,
          uploaded_by: "axfx_usr_contributor",
          updated_at: OBSERVED_AT
        }
      ],
      clarifications: [
        {
          id: "axfx_clar_security_001",
          workspace_id: workspaceId,
          question: "When will the final security annex be published?",
          rationale: "The annex changes the evidence needed for the blocking security requirement.",
          state: "internal_review",
          created_by: "axfx_usr_contributor",
          approved_by: null,
          handoff_opened_at: null,
          sent_confirmed_by: null,
          updated_at: OBSERVED_AT
        }
      ],
      tasks: [
        {
          id: "axfx_task_turnover_001",
          workspace_id: workspaceId,
          title: "Attach audited turnover evidence",
          owner_id: null,
          status: "open",
          due_at: "2026-08-12T16:00:00.000Z"
        }
      ],
      amendments: [
        {
          id: "axfx_amd_deadline_001",
          title: "Submission deadline extended by seven days",
          acknowledged: false,
          observed_at: "2026-08-01T08:30:00.000Z"
        }
      ],
      commercial: {
        currency: "EUR",
        candidate_value: 2400000,
        margin_percent: null,
        approved_by: null
      },
      submission: {
        package_status: "preparing",
        prepared_by: "axfx_usr_bid_manager",
        approved_by: null,
        preflight_status: "blocked",
        handoff_opened_at: null,
        externally_confirmed_by: null,
        externally_confirmed_at: null
      },
      outcome: {
        status: "unknown",
        observed_at: null,
        source_reference: null
      }
    }
  ];

  return {
    schema_version: "axignal.subscriber-workspace-store/v1",
    tenant: {
      id: tenantId,
      name: "Northstar Systems · Engineering",
      revision: 1
    },
    entitlement: {
      status: "active",
      plan_code: "engineering_fixture",
      seat_limit: 15,
      seats_used: 4,
      source: "engineering_fixture"
    },
    preferences: { locale: "es", theme: "dark" },
    opportunities,
    investigations: [
      {
        id: "axfx_inv_digital_infra_001",
        title: "European sovereign digital infrastructure",
        status: "active",
        updated_at: OBSERVED_AT,
        opportunity_ids: opportunities.map((item) => item.id)
      }
    ],
    workspaces,
    rights_snapshot: [
      {
        source_id: "axfx_source_ted_001",
        source_version: "axfx_rights_2026_08_01",
        rights_status: "admitted",
        attribution_required: true,
        redistribution_allowed: false,
        retrieved_at: OBSERVED_AT,
        expires_at: "2026-09-01T00:00:00.000Z"
      },
      {
        source_id: "axfx_source_portal_002",
        source_version: "axfx_rights_2026_07_30",
        rights_status: "review_required",
        attribution_required: true,
        redistribution_allowed: false,
        retrieved_at: "2026-07-30T14:30:00.000Z",
        expires_at: null
      }
    ],
    members: [
      {
        id: "axfx_usr_owner",
        display_name: "Elena Martín",
        email: "owner@fixture.invalid",
        roles: ["OWNER"]
      },
      {
        id: "axfx_usr_bid_manager",
        display_name: "Marco Silva",
        email: "bid-manager@fixture.invalid",
        roles: ["BID_MANAGER"]
      },
      {
        id: "axfx_usr_contributor",
        display_name: "Ari Rossi",
        email: "contributor@fixture.invalid",
        roles: ["CONTRIBUTOR"]
      },
      {
        id: "axfx_usr_reviewer",
        display_name: "Léa Bernard",
        email: "reviewer@fixture.invalid",
        roles: ["REVIEWER"]
      }
    ],
    events: [],
    action_receipts: {}
  };
}
