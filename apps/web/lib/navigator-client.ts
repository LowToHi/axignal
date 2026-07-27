import type { Locale, PrototypeInvestigationPayload } from "./investigation-context";

export type NavigatorCommandRequest = {
  message: string;
  locale: Locale;
  payload: PrototypeInvestigationPayload;
};

export type ResearchRequest = {
  question: string;
  locale: Locale;
  includePrivateKnowledge: boolean;
  payload: PrototypeInvestigationPayload;
};

async function readPayload(response: Response, operation: string): Promise<PrototypeInvestigationPayload> {
  if (!response.ok) {
    throw new Error(`${operation} failed with status ${response.status}`);
  }
  return (await response.json()) as PrototypeInvestigationPayload;
}

export async function runNavigatorCommand(request: NavigatorCommandRequest): Promise<PrototypeInvestigationPayload> {
  const response = await fetch("/api/navigator/interpret", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request)
  });
  return readPayload(response, "Navigator request");
}

export async function runResearch(request: ResearchRequest): Promise<PrototypeInvestigationPayload> {
  const response = await fetch("/api/research/runs", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request)
  });
  return readPayload(response, "ResearchRun");
}
