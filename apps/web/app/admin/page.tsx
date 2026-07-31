import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";

import {
  fetchFounderAdminData,
  isFounderIdentity
} from "@/lib/organic-server";
import { getAuthenticatedIdentity } from "@/lib/server-auth";

import { FounderAdminDashboard } from "./founder-admin-dashboard";
import { FounderBootstrap } from "./founder-bootstrap";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Founder Control Plane — AXIGNAL",
  description: "Private founder administration for AXIGNAL.",
  robots: {
    index: false,
    follow: false,
    noarchive: true,
    noimageindex: true
  }
};

function boolEnv(name: string): boolean {
  return ["1", "true", "yes", "on"].includes(
    (process.env[name] ?? "").trim().toLowerCase()
  );
}

export default async function FounderAdminPage() {
  const identity = await getAuthenticatedIdentity();
  if (!identity) redirect("/");
  if (!isFounderIdentity(identity)) notFound();
  try {
    const data = await fetchFounderAdminData(identity);
    return <FounderAdminDashboard data={data} founderEmail={identity.email} />;
  } catch {
    if (
      process.env.AXIGNAL_ENVIRONMENT === "test" &&
      boolEnv("AXIGNAL_TEST_RUNTIME_ENABLED")
    ) {
      return <FounderBootstrap />;
    }
    notFound();
  }
}
