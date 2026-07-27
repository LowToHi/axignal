import { NextResponse } from "next/server";

import { sessionCookieOptions } from "../../../../lib/server-auth";

export async function POST() {
  const response = NextResponse.json({ authenticated: false });
  response.cookies.set({ ...sessionCookieOptions(), value: "", maxAge: 0 });
  return response;
}
