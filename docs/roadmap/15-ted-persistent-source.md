# F8 TED persistent source — bounded product admission

Status: `IMPLEMENTED CANDIDATE / PRODUCT_ADMITTED PROFILE / FEATURE-FLAGGED / PUBLIC UNIVERSE NOT LAUNCHED`

Task `AX-F8-T14` converts the version-pinned parser, lifecycle and sandbox-admission evidence into a persistent authenticated ResearchRun path.

## Normative distinction

- Source profile `ted-eforms-non-personal@1.0.0`: product-admitted.
- Runtime: disabled by default and activated only by `AXIGNAL_TED_RESEARCH_ENABLED=true`.
- Public universe support and marketing: not authorised.
- Bulk or scheduled ingestion: not authorised.
- Buyer and winner identity persistence: not authorised.
- Raw XML persistence or redistribution: prohibited.

## Integration target

```text
identity → tenant → ResearchRun → retrieval outbox → isolated TED worker
→ transient XML → sanitised evidence → admission handoff
→ isolated TED admission runtime → canonical observed claims → dossier
→ InvestigationContext polling path
```

## Promotion ceiling

This gate may establish `EVIDENCE_READY` for the bounded source/runtime profile. It does not establish public launch, willingness to pay, billing, entitlements or broad country/subtype completeness.
