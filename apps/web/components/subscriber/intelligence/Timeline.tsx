"use client";

import { useEffect, useState } from "react";

import type { TimelinePoint } from "./types";
import styles from "./intelligence-workspace.module.css";

type TimelineProps = {
  points: readonly TimelinePoint[];
  selectedId: string | null;
  onSelect?: (pointId: string) => void;
};

export function Timeline({ points, selectedId, onSelect }: TimelineProps) {
  const current = points.find((point) => point.id === selectedId) ?? points.find((point) => point.status === "current") ?? points[0];
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    if (!isPlaying || points.length < 2) return;
    const timer = window.setTimeout(() => {
      const currentIndex = points.findIndex((point) => point.id === current?.id);
      const nextIndex = currentIndex + 1;
      if (nextIndex >= points.length) {
        setIsPlaying(false);
        return;
      }
      onSelect?.(points[nextIndex]!.id);
    }, 950);
    return () => window.clearTimeout(timer);
  }, [current?.id, isPlaying, onSelect, points]);

  function togglePlayback() {
    if (points.length < 2) return;
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    const currentIndex = points.findIndex((point) => point.id === current?.id);
    if (currentIndex >= points.length - 1) onSelect?.(points[0]!.id);
    setIsPlaying(true);
  }

  return (
    <section className={styles.timeline} aria-label="Investigation timeline">
      <button type="button" className={styles.playButton} aria-label={isPlaying ? "Pause timeline" : "Play timeline"} onClick={togglePlayback} disabled={points.length < 2}>{isPlaying ? "Pause" : "Play"}</button>
      <span className={styles.horizon}>12M</span>
      <div className={styles.timelineTrack} aria-label="Timeline points">
        {points.map((point) => <button key={point.id} type="button" className={styles.timelinePoint} aria-label={`${point.date}: ${point.label}`} aria-current={point.id === current?.id ? "date" : undefined} data-selected={point.id === current?.id} data-status={point.status} onClick={() => { setIsPlaying(false); onSelect?.(point.id); }} />)}
      </div>
      <span className={styles.today}>{current?.label ?? "No timeline data"}</span>
    </section>
  );
}
