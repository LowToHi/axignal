import { LandingExperience } from "@/components/landing-experience";
import { getCandidatePlans } from "@/lib/candidate-pricing";

export default async function LandingPage() {
  const plans = await getCandidatePlans();
  return <LandingExperience plans={plans} />;
}
