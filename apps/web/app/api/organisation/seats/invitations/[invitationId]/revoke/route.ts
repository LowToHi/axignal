import { proxySeatRequest } from "../../../../../../../lib/seat-server";

export async function POST(
  request: Request,
  context: { params: Promise<{ invitationId: string }> }
) {
  const { invitationId } = await context.params;
  return proxySeatRequest(
    `/v1/organisation/seats/invitations/${encodeURIComponent(invitationId)}/revoke`,
    { method: "POST", body: await request.text() }
  );
}
