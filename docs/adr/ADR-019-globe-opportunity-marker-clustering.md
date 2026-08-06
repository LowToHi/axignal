# ADR-019 — Fixed-size globe cards and zoom-aware opportunity clustering

## Status

Accepted

## Context

The investigation Globe presents opportunity markers over a cartographic surface. The selected marker card was rendered as a distance-scaled HTML object, which made the card grow with camera zoom and allowed it to overlap adjacent rails. Nearby opportunities also had no visual grouping model, making dense locations difficult to select.

## Decision

- Render the selected opportunity card as a fixed-size 2D overlay, independent of camera distance.
- Keep the card anchored to the selected marker and flip its horizontal attachment when the marker is near the right edge of the viewport.
- Disable autonomous camera rotation and orient the initial globe to the centre of the current opportunity set.
- Preserve a north-up frame while focusing so geographic north remains vertical and the globe never introduces an arbitrary roll.
- Bind OrbitControls to the transformed geographic-north axis, allowing unrestricted East-West longitude movement and bounded North-South latitude movement without a third roll axis.
- Keep the WebGL canvas opaque and mounted during selection changes; no fade-in animation is applied to the Globe surface.
- Cluster nearby opportunity markers at the current camera distance.
- Represent a collapsed cluster with a count badge.
- When the user zooms past the expansion threshold, spread clustered markers radially along the globe tangent plane so each opportunity can be selected independently.
- Keep the existing accessible opportunity table and right-rail selection as the deterministic equivalent of the visual marker layer.

## Alternatives considered

- Keep distance-scaled cards: rejected because the card becomes visually dominant and overlaps the evidence rail.
- Hide all but one nearby opportunity: rejected because it obscures available candidates.
- Use a third-party map clustering dependency: rejected for the current globe because the existing Three.js surface already owns projection, camera distance and marker lifecycle.

## Tradeoffs

- Clustering is client-side presentation logic and does not alter server-authoritative opportunity data.
- The current implementation uses a deterministic greedy spherical-distance grouping and tangent-plane radial expansion; a future high-density universe may require a spatial index.
- A cluster badge selects the highest-priority opportunity currently represented by that cluster unless the selected opportunity is already inside it.

## Consequences

The Globe remains readable at overview scale, dense regions become progressively explorable through zoom, and the selected card remains visually consistent with the rest of the interface. The accessible table remains the fallback for keyboard and assistive-technology workflows.
