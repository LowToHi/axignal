import type { Locale, PrototypeInvestigationPayload } from "./investigation-context";

export type NavigatorCommandRequest = {
  message: string;
  locale: Locale;
  payload: PrototypeInvestigationPayload;
};

export async function runNavigatorCommand(request: NavigatorCommandRequest): Promise<PrototypeInvestigationPayload> {
  const response = await fetch("/api/navigator/interpret", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(request)
  });

  if (!response.ok) {
    throw new Error(`Navigator request failed with status ${response.status}`);
  }

  return (await response.json()) as PrototypeInvestigationPayload;
}
