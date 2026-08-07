import type { Metadata } from "next";

import { WorkspaceActions } from "@/components/opportunities/workspace-actions";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Workspaces — AXIGNAL",
  description: "Private opportunity workspaces.",
  robots: { index: false, follow: false }
};

type Workspace = {
  workspace_id: string;
  pursuit_ref: string;
  opportunity_ref: string;
  state: string;
  assessment_version: string;
  created_at: string;
};

async function fetchWorkspaces(): Promise<Workspace[]> {
  try {
    const response = await fetch(
      `${process.env.AXIGNAL_PUBLIC_ORIGIN ?? "http://localhost:18080"}/api/opportunities/workspaces`,
      { cache: "no-store", signal: AbortSignal.timeout(8_000) }
    );
    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export default async function WorkspacesPage() {
  const workspaces = await fetchWorkspaces();
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Workspaces</h1>
      <p>Tenant-scoped opportunity workspaces sobre la API real.</p>
      {workspaces.length === 0 ? (
        <p>No hay workspaces todavía.</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Workspace</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Pursuit</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>State</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {workspaces.map((workspace) => (
              <tr key={workspace.workspace_id}>
                <td style={{ padding: "0.5rem" }}>{workspace.workspace_id}</td>
                <td style={{ padding: "0.5rem" }}>{workspace.pursuit_ref}</td>
                <td style={{ padding: "0.5rem" }}>{workspace.state}</td>
                <td style={{ padding: "0.5rem" }}>
                  <WorkspaceActions
                    pursuitRef={workspace.pursuit_ref}
                    opportunityRef={workspace.opportunity_ref}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
