import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ConfirmAlertClient } from "./confirm-alert-client";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Confirm tender alert — AXIGNAL",
  robots: {
    index: false,
    follow: false,
    noarchive: true
  }
};

export default async function ConfirmTenderAlertPage({
  searchParams
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;
  if (!token || !/^[A-Za-z0-9_-]{20,512}$/.test(token)) notFound();
  return <ConfirmAlertClient token={token} />;
}
