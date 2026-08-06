import { proxySeatRequest } from "../../../../../lib/seat-server";

export async function POST(request: Request) {
  return proxySeatRequest("/v1/organisation/seats/bootstrap-owner", {
    method: "POST",
    body: await request.text()
  });
}
