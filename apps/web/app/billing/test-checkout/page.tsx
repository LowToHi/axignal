import { notFound } from "next/navigation";

import { DeterministicTestCheckoutClient } from "./test-checkout-client";

export const dynamic = "force-dynamic";

function testRuntimeEnabled(): boolean {
  return (
    process.env.AXIGNAL_ENVIRONMENT === "test" &&
    process.env.AXIGNAL_TEST_RUNTIME_ENABLED === "true"
  );
}

export default function DeterministicTestCheckoutPage() {
  if (!testRuntimeEnabled()) notFound();
  return <DeterministicTestCheckoutClient />;
}
