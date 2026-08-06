"use client";

import type { ComponentProps } from "react";
import { useEffect, useId, useState } from "react";

import { SemanticGlobe as AnimatedSemanticGlobe } from "./SemanticGlobe";
import styles from "./intelligence-workspace.module.css";

type SemanticGlobeProps = ComponentProps<typeof AnimatedSemanticGlobe>;

function useReducedMotion() {
  const [reducedMotion, setReducedMotion] = useState<boolean | null>(null);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const sync = () => setReducedMotion(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  return reducedMotion;
}

function StaticSemanticGlobe({
  opportunities,
  selectedOpportunityId,
  label,
  onSelect,
}: SemanticGlobeProps) {
  const descriptionId = useId();
  const selected =
    opportunities.find((item) => item.id === selectedOpportunityId) ??
    opportunities[0];

  return (
    <section
      className={styles.globeSurface}
      aria-label={label}
      aria-describedby={descriptionId}
      data-reduced-motion="true"
    >
      <p id={descriptionId} className={styles.srOnly}>
        Static cartographic equivalent for the current investigation. Motion is
        disabled because the operating system requests reduced motion. The
        opportunity table remains fully available.
      </p>
      <div
        className={styles.globeFallback}
        role="status"
        data-testid="semantic-globe-static"
      >
        <img src="/globe/globe-poster.webp" alt="" />
        <span>
          Motion reduced. A static cartographic equivalent is shown; the
          accessible opportunity list remains available below.
        </span>
      </div>
      {selected ? (
        <div className={styles.globeCallout}>
          <strong>{label}</strong>
          <span>{opportunities.length} opportunities detected</span>
          <span>
            Selected <b>{selected.name}</b>
          </span>
          <span>
            Evidence fit <b>{selected.expectedReturn ?? "Unknown"}</b>
          </span>
          <span>
            Confidence{" "}
            <b>
              {selected.confidence === null
                ? "Unknown"
                : `${Math.round(selected.confidence * 100)}%`}
            </b>
          </span>
        </div>
      ) : null}
      <div className={styles.legend} aria-hidden="true">
        <span>OPPORTUNITY POTENTIAL</span>
        <i />
        <div>
          <small>Very low</small>
          <small>Medium</small>
          <small>Very high</small>
          <small>No data</small>
        </div>
      </div>
      <small
        className={styles.globeAttribution}
        aria-label="Earth imagery: NASA Earth Observatory. Country boundaries: Natural Earth."
      >
        NASA Earth Observatory · Natural Earth
      </small>
      <table className={styles.srOnly}>
        <caption>{label}: accessible geographic opportunity list</caption>
        <thead>
          <tr>
            <th>Opportunity</th>
            <th>Latitude</th>
            <th>Longitude</th>
            <th>Evidence fit</th>
            <th>Confidence</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {opportunities.map((opportunity) => (
            <tr key={opportunity.id}>
              <th scope="row">{opportunity.name}</th>
              <td>{opportunity.latitude}</td>
              <td>{opportunity.longitude}</td>
              <td>{opportunity.expectedReturn ?? "Unknown"}</td>
              <td>{opportunity.confidence ?? "Unknown"}</td>
              <td>
                <button type="button" onClick={() => onSelect(opportunity.id)}>
                  Select {opportunity.name}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function SemanticGlobe(props: SemanticGlobeProps) {
  const reducedMotion = useReducedMotion();

  if (reducedMotion !== false) {
    return <StaticSemanticGlobe {...props} />;
  }

  return <AnimatedSemanticGlobe {...props} />;
}
