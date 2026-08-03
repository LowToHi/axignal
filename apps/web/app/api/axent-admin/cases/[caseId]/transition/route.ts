import { proxySubscriberJson } from "@/lib/subscriber-live-server";

export async function POST(
  request: Request,
  context: { params: Promise<{ caseId: string }> }
) {
  const { caseId } = await context.params;
  const body = await request.text();
  return proxySubscriberJson(
    `/v1/axent-admin/cases/${encodeURIComponent(caseId)}/transition`,
    { method: "POST", body }
  );
}
