import { proxySeatRequest } from "../../../../../../../lib/seat-server";

export async function POST(
  request: Request,
  context: { params: Promise<{ membershipId: string }> }
) {
  const { membershipId } = await context.params;
  return proxySeatRequest(
    `/v1/organisation/seats/members/${encodeURIComponent(membershipId)}/role`,
    { method: "POST", body: await request.text() }
  );
}
