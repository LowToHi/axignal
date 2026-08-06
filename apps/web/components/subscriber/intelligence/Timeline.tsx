"use client";

import type { TimelinePoint } from "./types";
import styles from "./intelligence-workspace.module.css";

type TimelineProps = {
  points: readonly TimelinePoint[];
  selectedId: string | null;
  onSelect?: (pointId: string) => void;
};

export function Timeline({ points, selectedId, onSelect }: TimelineProps) {
  const current = points.find((point) => point.id === selectedId) ?? points.find((point) => point.status === "current") ?? points[0];
  return (
    <section className={styles.timeline} aria-label="Investigation timeline">
      <button type="button" className={styles.playButton} aria-label="Play timeline" disabled={points.length === 0}>Play</button>
      <span className={styles.horizon}>12M</span>
      <div className={styles.timelineTrack} aria-hidden="true">
        {points.map((point) => <i key={point.id} data-selected={point.id === current?.id} data-status={point.status} />)}
      </div>
      <span className={styles.today}>{current?.label ?? "No timeline data"}</span>
      <ol className={styles.srOnly}>
        {points.map((point) => (
          <li key={point.id}>
            <button type="button" aria-current={point.id === current?.id ? "date" : undefined} onClick={() => onSelect?.(point.id)}>{point.date}: {point.label} ({point.status})</button>
          </li>
        ))}
      </ol>
    </section>
  );
}
