"use client";

import { useState } from "react";

import styles from "./demo-guide.module.css";

const STORAGE_KEY = "axignal:investigation-shell:v2";

const steps = [
  {
    eyebrow: "01 · QUESTION",
    title: "Start from a bounded investigation",
    body: "Use the Navigator to ask about Moscow real-estate opportunities. The shell preserves geography, horizon, universe and selected lens."
  },
  {
    eyebrow: "02 · MODEL PROPOSAL",
    title: "Inspect what the model proposed",
    body: "A proposal is never presented as canonical evidence. Open a claim and inspect the authority label before reading its confidence."
  },
  {
    eyebrow: "03 · EVIDENCE",
    title: "Follow the evidence binding",
    body: "Select a claim, then open the Evidence rail. Support, contradiction and unknown relationships remain explicit and traceable."
  },
  {
    eyebrow: "04 · DETERMINISTIC DECISION",
    title: "Separate policy from generation",
    body: "The admission runtime, not the model, decides whether a proposal is admitted, contested, rejected or sent to human review."
  },
  {
    eyebrow: "05 · HUMAN REVIEW",
    title: "Use human judgment without rewriting truth",
    body: "Human review may accept context, request evidence or confirm a contested state, but cannot create a canonical claim directly."
  },
  {
    eyebrow: "06 · UNKNOWN",
    title: "End with what remains unknown",
    body: "The dossier preserves coverage gaps and unresolved questions instead of silently converting absence of evidence into certainty."
  }
] as const;

export function DemoGuide() {
  const [index, setIndex] = useState(0);
  const step = steps[index] ?? steps[0];

  function resetDemo() {
    window.localStorage.removeItem(STORAGE_KEY);
    window.location.reload();
  }

  return (
    <aside className={styles.guide} aria-label="Guion de demostración de AXIGNAL">
      <div className={styles.header}>
        <div>
          <span className={styles.kicker}>PILOT DEMO · SYNTHETIC FIXTURE</span>
          <h1>From proposal to defensible knowledge.</h1>
        </div>
        <button className={styles.reset} type="button" onClick={resetDemo}>
          Reset demo
        </button>
      </div>

      <div className={styles.progress} aria-label={`Paso ${index + 1} de ${steps.length}`}>
        {steps.map((item, itemIndex) => (
          <button
            aria-label={`Abrir ${item.eyebrow}`}
            aria-current={itemIndex === index ? "step" : undefined}
            className={itemIndex === index ? styles.activeDot : styles.dot}
            key={item.eyebrow}
            onClick={() => setIndex(itemIndex)}
            type="button"
          />
        ))}
      </div>

      <section className={styles.step} aria-live="polite">
        <span>{step.eyebrow}</span>
        <h2>{step.title}</h2>
        <p>{step.body}</p>
      </section>

      <div className={styles.legend}>
        <span><i data-kind="proposal" />Model proposal</span>
        <span><i data-kind="decision" />Deterministic decision</span>
        <span><i data-kind="human" />Human review</span>
        <span><i data-kind="canonical" />Canonical claim</span>
      </div>

      <div className={styles.actions}>
        <button type="button" disabled={index === 0} onClick={() => setIndex((current) => current - 1)}>
          Previous
        </button>
        <strong>{index + 1} / {steps.length}</strong>
        <button
          type="button"
          disabled={index === steps.length - 1}
          onClick={() => setIndex((current) => current + 1)}
        >
          Next
        </button>
      </div>
    </aside>
  );
}
