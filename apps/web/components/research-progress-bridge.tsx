"use client";

import { useEffect, useState } from "react";

import {
  RESEARCH_PROGRESS_EVENT,
  type ResearchProgressEvent
} from "../lib/navigator-client";

const stateLabels: Record<string, string> = {
  QUEUED: "En cola",
  RETRIEVING: "Recuperando fuente",
  PROPOSING: "Construyendo propuesta",
  ADMISSION_PENDING: "Evaluando admisión",
  COMPLETED: "Completada",
  FAILED: "Fallida"
};

export function ResearchProgressBridge() {
  const [progress, setProgress] = useState<ResearchProgressEvent | null>(null);

  useEffect(() => {
    function receive(event: Event) {
      setProgress((event as CustomEvent<ResearchProgressEvent>).detail);
    }
    window.addEventListener(RESEARCH_PROGRESS_EVENT, receive);
    return () => window.removeEventListener(RESEARCH_PROGRESS_EVENT, receive);
  }, []);

  if (!progress) return null;

  return (
    <aside
      className="research-progress-bridge"
      data-state={progress.state}
      data-terminal={progress.terminal}
      aria-live="polite"
      aria-label="Progreso de la investigación persistente"
    >
      <div>
        <span>RESEARCH RUN</span>
        <strong>{stateLabels[progress.state] ?? progress.state}</strong>
      </div>
      <p>{progress.question}</p>
      <small>{progress.researchRunId}</small>
      <small>{progress.explanation}</small>
      {progress.terminal && (
        <button type="button" onClick={() => setProgress(null)}>Cerrar</button>
      )}
    </aside>
  );
}
