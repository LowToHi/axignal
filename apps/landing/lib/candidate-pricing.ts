import "server-only";

import { readFile } from "node:fs/promises";
import { resolve } from "node:path";

import {
  candidatePlansFromRuntime,
  type CommercialRuntime
} from "./candidate-pricing-contract";
import type { CandidatePlan } from "./landing-data";

export async function getCandidatePlans(): Promise<readonly CandidatePlan[]> {
  const runtimePath = resolve(
    process.cwd(),
    "../../data/commercial/commercial-runtime-pricing-stripe-runtime.v0.1.json"
  );
  const runtime = JSON.parse(await readFile(runtimePath, "utf8")) as CommercialRuntime;
  return candidatePlansFromRuntime(runtime);
}
