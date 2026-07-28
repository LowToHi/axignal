import { AuthGate } from "@/components/auth-gate";
import { ValidationHarness } from "@/components/validation-harness";
import { getAuthenticatedIdentity, isAuthenticationRequired } from "@/lib/server-auth";

export default async function ValidationPage() {
  if (process.env.AXIGNAL_VALIDATION_UI_ENABLED !== "true") {
    return null;
  }
  if (!isAuthenticationRequired()) return <ValidationHarness />;
  const identity = await getAuthenticatedIdentity();
  if (!identity) return <AuthGate />;
  return <ValidationHarness />;
}
