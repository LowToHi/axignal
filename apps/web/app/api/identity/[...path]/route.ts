import { proxyIdentityRequest } from "../../../../lib/identity-server";

type Context = { params: Promise<{ path: string[] }> };

async function proxy(request: Request, context: Context) {
  const { path } = await context.params;
  return proxyIdentityRequest(request, path.join("/"));
}

export async function GET(request: Request, context: Context) {
  return proxy(request, context);
}

export async function POST(request: Request, context: Context) {
  return proxy(request, context);
}
