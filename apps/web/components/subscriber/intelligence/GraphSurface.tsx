"use client";

import { useEffect, useRef } from "react";

import type { GraphEntity, GraphRelationship } from "./types";
import styles from "./intelligence-workspace.module.css";

type GraphSurfaceProps = {
  entities: readonly GraphEntity[];
  relationships: readonly GraphRelationship[];
  selectedOpportunityId: string | null;
};

export function GraphSurface({ entities, relationships, selectedOpportunityId }: GraphSurfaceProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;
    const ratio = Math.min(window.devicePixelRatio || 1, 1.6);
    const width = Math.max(1, Math.floor(canvas.clientWidth * ratio));
    const height = Math.max(1, Math.floor(canvas.clientHeight * ratio));
    canvas.width = width;
    canvas.height = height;
    context.scale(ratio, ratio);
    const cssWidth = width / ratio;
    const cssHeight = height / ratio;
    const css = getComputedStyle(canvas);
    context.fillStyle = css.getPropertyValue("--ax-bg-canvas").trim() || "#070a0e";
    context.fillRect(0, 0, cssWidth, cssHeight);
    const points = new Map<string, { x: number; y: number }>();
    const radius = Math.min(cssWidth, cssHeight) * 0.31;
    entities.forEach((entity, index) => {
      const angle = (Math.PI * 2 * index) / Math.max(entities.length, 1) - Math.PI / 2;
      points.set(entity.id, index === 0
        ? { x: cssWidth / 2, y: cssHeight / 2 }
        : { x: cssWidth / 2 + Math.cos(angle) * radius, y: cssHeight / 2 + Math.sin(angle) * radius });
    });
    const colors: Record<GraphRelationship["epistemicStatus"], string> = {
      support: css.getPropertyValue("--ax-support").trim() || "#67d39f",
      inferred: css.getPropertyValue("--ax-inferred").trim() || "#b99cff",
      contradiction: css.getPropertyValue("--ax-critical").trim() || "#ff7182",
      unknown: css.getPropertyValue("--ax-unknown").trim() || "#81909e"
    };
    relationships.forEach((relationship) => {
      const from = points.get(relationship.from);
      const to = points.get(relationship.to);
      if (!from || !to) return;
      context.beginPath();
      context.moveTo(from.x, from.y);
      context.lineTo(to.x, to.y);
      context.strokeStyle = colors[relationship.epistemicStatus];
      context.globalAlpha = .72;
      context.lineWidth = 1.25;
      if (relationship.epistemicStatus === "inferred") context.setLineDash([5, 5]);
      context.stroke();
      context.setLineDash([]);
    });
    context.globalAlpha = 1;
    entities.forEach((entity) => {
      const point = points.get(entity.id);
      if (!point) return;
      const selected = entity.id === selectedOpportunityId;
      context.beginPath();
      context.arc(point.x, point.y, selected ? 27 : 21, 0, Math.PI * 2);
      context.fillStyle = selected ? "rgba(67, 200, 200, .24)" : css.getPropertyValue("--ax-bg-raised").trim() || "#131d27";
      context.fill();
      context.strokeStyle = selected ? css.getPropertyValue("--ax-brand-signal").trim() || "#43c8c8" : css.getPropertyValue("--ax-border-strong").trim() || "#3a5265";
      context.stroke();
      context.fillStyle = css.getPropertyValue("--ax-fg-primary").trim() || "#f3f7fa";
      context.font = "11px system-ui";
      context.textAlign = "center";
      context.textBaseline = "middle";
      context.fillText(entity.label.slice(0, 17), point.x, point.y);
    });
  }, [entities, relationships, selectedOpportunityId]);

  return (
    <section className={styles.graphSurface} aria-label="Relationship graph">
      <canvas className={styles.graphCanvas} ref={canvasRef} aria-hidden="true" />
      <div className={styles.graphCaption}><strong>Transmission graph</strong><span>Typed relationships · context preserved</span></div>
      <table className={styles.srOnly}>
        <caption>Accessible graph relationships</caption>
        <thead><tr><th>From</th><th>Relationship</th><th>To</th><th>Epistemic status</th></tr></thead>
        <tbody>{relationships.map((relationship) => (
          <tr key={relationship.id}><td>{entities.find((item) => item.id === relationship.from)?.label ?? relationship.from}</td><td>{relationship.label}</td><td>{entities.find((item) => item.id === relationship.to)?.label ?? relationship.to}</td><td>{relationship.epistemicStatus}</td></tr>
        ))}</tbody>
      </table>
    </section>
  );
}
