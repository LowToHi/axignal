import type { Metadata } from "next";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Notices — AXIGNAL",
  description: "Versioned O01 notices.",
  robots: { index: false, follow: false }
};

type Notice = {
  publication_number: string;
  source_id: string;
  current_version: number;
  current_content_hash: string;
  first_retrieved_at: string;
  last_retrieved_at: string;
  notice_title: Record<string, string> | null;
  buyer_name: Record<string, string> | null;
  notice_type: string | null;
  state: string;
};

async function fetchNotices(): Promise<Notice[]> {
  try {
    const response = await fetch(
      `${process.env.AXIGNAL_PUBLIC_ORIGIN ?? "http://localhost:18080"}/api/opportunities/notices`,
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

export default async function NoticesPage() {
  const notices = await fetchNotices();
  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1>Notices</h1>
      <p>Notices O01 persistidos y versionados por la cadena de ingestión.</p>
      {notices.length === 0 ? (
        <p>No hay notices todavía.</p>
      ) : (
        <table style={{ borderCollapse: "collapse", width: "100%" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Publication</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Title</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Version</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>State</th>
              <th style={{ textAlign: "left", padding: "0.5rem" }}>Retrieved</th>
            </tr>
          </thead>
          <tbody>
            {notices.map((notice) => (
              <tr key={notice.publication_number}>
                <td style={{ padding: "0.5rem" }}>{notice.publication_number}</td>
                <td style={{ padding: "0.5rem" }}>
                  {notice.notice_title?.eng ?? notice.publication_number}
                </td>
                <td style={{ padding: "0.5rem" }}>{notice.current_version}</td>
                <td style={{ padding: "0.5rem" }}>{notice.state}</td>
                <td style={{ padding: "0.5rem" }}>
                  {new Date(notice.last_retrieved_at).toISOString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
