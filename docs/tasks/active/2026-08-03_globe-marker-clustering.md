# Goal Lock: AXIGNAL-GOAL-001

## Objective

Keep the Globe opportunity card at a stable UI size and make nearby opportunity markers discoverable and individually selectable through zoom-aware clustering.

## Affected systems

- `apps/web/components/subscriber/intelligence/SemanticGlobe.tsx`
- `apps/web/components/subscriber/intelligence/intelligence-workspace.module.css`
- Globe E2E coverage

## Implementation

- Remove distance-scaled HTML rendering from the selected marker card.
- Add fixed-size card layout with viewport-aware left/right attachment.
- Add camera-distance clustering and tangent-plane expansion for dense marker groups.
- Add a count badge for collapsed clusters.

## Validation checklist

- [x] TypeScript passes for `apps/web`.
- [x] Globe E2E suite passes.
- [x] Production build passes.
- [x] Accessible geographic opportunity table remains available.
- [ ] Validate dense same-region fixture with product data before enabling a larger spatial index.

## Risks and rollback

The presentation layer can be rolled back by removing the `clusterMarkerLayouts` path and restoring per-opportunity layouts. No API, database or canonical evidence data changes are involved.
