import { proxyAxentJson } from "@/lib/axent-server";

export async function POST(request: Request) {
  return proxyAxentJson("/v1/axent/conversations", {
    method: "POST",
    body: await request.text()
  });
}
