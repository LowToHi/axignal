import { proxySeatRequest } from "../../../../lib/seat-server";

export async function GET() {
  return proxySeatRequest("/v1/organisation/seats");
}
