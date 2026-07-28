# F1 Controlled Study Operations

## Roles

- **Study operator:** issues temporary access and records operational incidents.
- **Validation runtime:** creates sessions and immutable responses; no canonical authority.
- **Validation analyst:** exports pseudonymised outcomes through one execute-only function.
- **Gate reviewer:** reviews the final report and determines `PASSED`, `FAILED` or continued `GATE_REVIEW`.

No role may edit responses, reassign conditions or expose answer keys.

## Start gate

Run:

```bash
python scripts/verify_f1_controlled_study_protocol.py
bash scripts/verify_f1_controlled_study_migration_rehearsal.sh
python scripts/verify_f1_controlled_study_runtime.py
```

The first human session may begin only when all three pass on the same commit and the manifest status remains `FROZEN_PRE_RECRUITMENT`.

## Participant handling

Use temporary credentials. Do not store names or emails in AXIGNAL's evaluation schema. Keep any consent or scheduling record outside the analytical dataset with access limited to the study operator. Do not reveal condition assignment or expected superiority.

## Incident accounting

The export command requires explicit counts for privacy, cross-tenant, canonical-mutation, answer-key exposure and direct-PII incidents. Counts cannot be omitted or inferred as zero.

## Export

```bash
export AXIGNAL_VALIDATION_ANALYST_DATABASE_URL='postgresql://...'
python scripts/export_f1_controlled_study.py \
  --tenant-id 11111111-1111-4111-8111-111111111111 \
  --output runs/f1-controlled-study/dataset.json \
  --privacy-incidents 0 \
  --cross-tenant-incidents 0 \
  --canonical-mutations 0 \
  --answer-key-exposures 0 \
  --direct-participant-pii-records 0
```

The exported file remains sensitive despite pseudonymisation. Keep it outside public artifacts.

## Analysis

```bash
python scripts/analyse_f1_controlled_study.py \
  --input runs/f1-controlled-study/dataset.json \
  --output runs/f1-controlled-study/report.json
```

Record the dataset hash, report hash, repository commit and manifest hash. Do not modify the dataset after closure; corrections require a new versioned dataset with an audit note.

## Closure

At the stopping checkpoint, disable new study credentials, export once, hash the dataset, run analysis and record the human gate decision. Keep F1 in `GATE_REVIEW` when the recommendation is `NOT_READY` or `INCONCLUSIVE`.
