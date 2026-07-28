"use client";

import { useEffect, useMemo, useState } from "react";

import styles from "./validation-harness.module.css";

type TaskSummary = {
  task_id: string;
  title: string;
  language: string;
  content_hash: string;
};

type Evidence = {
  id: string;
  title: string;
  excerpt: string;
  source_state: string;
};

type Unknown = { id: string; label: string };

type SessionBundle = {
  session: {
    validation_session_id: string;
    condition: "AXIGNAL" | "CONTROL";
    state: "STARTED" | "COMPLETED";
    outcome?: Record<string, boolean | number>;
  };
  task: {
    task_id: string;
    title: string;
    content_hash: string;
    payload: {
      prompt: string;
      statement: string;
      evidence: Evidence[];
      unknowns: Unknown[];
    };
  };
  response?: {
    authority_layer_correct: boolean;
    evidence_traceability: boolean;
    unknowns_identified: boolean;
    critical_error: boolean;
    task_completed: boolean;
  } | null;
};

const authorityOptions = [
  "CANONICAL_CLAIM",
  "MODEL_PROPOSAL",
  "DETERMINISTIC_DECISION",
  "HUMAN_REVIEW_CONTEXT",
  "CONTESTED",
  "REJECTED_PROPOSAL",
  "DERIVED_COMPARISON",
  "CANONICAL_CAUSAL_CLAIM"
];

async function postJson(path: string, payload: unknown) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error ?? body.detail ?? "Validation request failed");
  return body;
}

export function ValidationHarness() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [taskId, setTaskId] = useState("");
  const [profile, setProfile] = useState("DOMAIN_EXPERT");
  const [bundle, setBundle] = useState<SessionBundle | null>(null);
  const [authority, setAuthority] = useState("");
  const [evidenceIds, setEvidenceIds] = useState<string[]>([]);
  const [unknownIds, setUnknownIds] = useState<string[]>([]);
  const [confidence, setConfidence] = useState(70);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    fetch("/api/validation/tasks?language=en", { cache: "no-store" })
      .then((response) => response.json())
      .then((body) => {
        const next = (body.tasks ?? []) as TaskSummary[];
        setTasks(next);
        if (next[0]) setTaskId(next[0].task_id);
      })
      .catch(() => setError("Unable to load frozen validation tasks."));
  }, []);

  const conditionLabel = useMemo(() => {
    if (!bundle) return "UNASSIGNED";
    return bundle.session.condition;
  }, [bundle]);

  async function startSession() {
    setBusy(true);
    setError("");
    try {
      const next = (await postJson("/api/validation/sessions", {
        task_id: taskId,
        participant_profile: profile
      })) as SessionBundle;
      setBundle(next);
      await postJson(
        `/api/validation/sessions/${next.session.validation_session_id}/events`,
        {
          event_type: "TASK_OPENED",
          idempotency_key: "ui-task-opened",
          payload: { condition: next.session.condition }
        }
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to start validation.");
    } finally {
      setBusy(false);
    }
  }

  async function toggleEvidence(id: string) {
    const selected = evidenceIds.includes(id);
    setEvidenceIds(selected ? evidenceIds.filter((item) => item !== id) : [...evidenceIds, id]);
    if (!selected && bundle) {
      await postJson(
        `/api/validation/sessions/${bundle.session.validation_session_id}/events`,
        {
          event_type: "EVIDENCE_INSPECTED",
          idempotency_key: `evidence-${id}`,
          payload: { evidence_id: id }
        }
      ).catch(() => undefined);
    }
  }

  async function completeSession() {
    if (!bundle) return;
    setBusy(true);
    setError("");
    try {
      const next = (await postJson(
        `/api/validation/sessions/${bundle.session.validation_session_id}/complete`,
        {
          authority_layer: authority,
          evidence_ids: evidenceIds,
          unknown_ids: unknownIds,
          confidence,
          answer
        }
      )) as SessionBundle;
      setBundle(next);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to submit response.");
    } finally {
      setBusy(false);
    }
  }

  if (!bundle) {
    return (
      <main className={styles.shell} data-testid="validation-launcher">
        <header>
          <p className={styles.eyebrow}>F1 QUALIFIED-USER VALIDATION</p>
          <h1>Controlled evaluation session</h1>
          <p>
            The condition is assigned deterministically after session start. Direct personal
            identifiers are not stored in the evaluation schema.
          </p>
        </header>
        <section className={styles.launchCard}>
          <label>
            Frozen task
            <select value={taskId} onChange={(event) => setTaskId(event.target.value)}>
              {tasks.map((task) => (
                <option key={task.task_id} value={task.task_id}>
                  {task.task_id} — {task.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            Qualified-user profile
            <select value={profile} onChange={(event) => setProfile(event.target.value)}>
              <option value="DOMAIN_EXPERT">Domain expert</option>
              <option value="ANALYST">Analyst</option>
              <option value="DECISION_MAKER">Decision maker</option>
              <option value="OTHER_QUALIFIED">Other qualified user</option>
            </select>
          </label>
          <button disabled={!taskId || busy} onClick={startSession}>
            Start controlled session
          </button>
        </section>
        {error ? <p className={styles.error}>{error}</p> : null}
      </main>
    );
  }

  const payload = bundle.task.payload;
  const completed = bundle.session.state === "COMPLETED";
  return (
    <main className={styles.shell} data-testid="validation-session">
      <header className={styles.sessionHeader}>
        <div>
          <p className={styles.eyebrow}>FROZEN TASK · {bundle.task.task_id}</p>
          <h1>{bundle.task.title}</h1>
        </div>
        <span className={styles.condition} data-testid="validation-condition">
          {conditionLabel}
        </span>
      </header>

      <section className={styles.prompt}>
        <strong>{payload.prompt}</strong>
        <blockquote>{payload.statement}</blockquote>
      </section>

      <div
        className={bundle.session.condition === "AXIGNAL" ? styles.axignalGrid : styles.controlStack}
        data-testid={bundle.session.condition === "AXIGNAL" ? "axignal-condition" : "control-condition"}
      >
        <section className={styles.panel}>
          <h2>{bundle.session.condition === "AXIGNAL" ? "AUTHORITY" : "Classification"}</h2>
          <label>
            Authority state
            <select value={authority} onChange={(event) => setAuthority(event.target.value)}>
              <option value="">Select one</option>
              {authorityOptions.map((option) => (
                <option key={option}>{option}</option>
              ))}
            </select>
          </label>
        </section>

        <section className={styles.panel}>
          <h2>{bundle.session.condition === "AXIGNAL" ? "EVIDENCE" : "Source material"}</h2>
          {payload.evidence.map((item) => (
            <label className={styles.evidence} key={item.id}>
              <input
                type="checkbox"
                checked={evidenceIds.includes(item.id)}
                onChange={() => toggleEvidence(item.id)}
              />
              <span>
                <strong>{item.title}</strong>
                <small>{item.source_state}</small>
                <p>{item.excerpt}</p>
              </span>
            </label>
          ))}
        </section>

        <section className={styles.panel}>
          <h2>{bundle.session.condition === "AXIGNAL" ? "UNKNOWNS" : "Limitations"}</h2>
          {payload.unknowns.length ? (
            payload.unknowns.map((item) => (
              <label className={styles.evidence} key={item.id}>
                <input
                  type="checkbox"
                  checked={unknownIds.includes(item.id)}
                  onChange={() =>
                    setUnknownIds(
                      unknownIds.includes(item.id)
                        ? unknownIds.filter((value) => value !== item.id)
                        : [...unknownIds, item.id]
                    )
                  }
                />
                <span>{item.label}</span>
              </label>
            ))
          ) : (
            <p>No declared unknowns for this task.</p>
          )}
        </section>
      </div>

      <section className={styles.responseCard}>
        <label>
          Confidence: {confidence}%
          <input
            type="range"
            min="0"
            max="100"
            value={confidence}
            onChange={(event) => setConfidence(Number(event.target.value))}
          />
        </label>
        <label>
          Explanation
          <textarea value={answer} onChange={(event) => setAnswer(event.target.value)} />
        </label>
        <button disabled={!authority || busy || completed} onClick={completeSession}>
          Submit immutable response
        </button>
      </section>

      {completed ? (
        <section className={styles.outcome} data-testid="validation-outcome">
          <h2>Session recorded</h2>
          <pre>{JSON.stringify(bundle.session.outcome, null, 2)}</pre>
          <p>The response is append-only and cannot alter evidence or canonical claims.</p>
        </section>
      ) : null}
      {error ? <p className={styles.error}>{error}</p> : null}
    </main>
  );
}
