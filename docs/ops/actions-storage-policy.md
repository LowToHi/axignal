# AXIGNAL GitHub Actions storage policy

## Purpose

Keep GitHub Actions as an ephemeral execution transport, not as the canonical evidence repository.

## Canonical authority

Canonical AXIGNAL evidence must be represented in the repository by immutable metadata:

- exact commit SHA and tree SHA;
- workflow run and job identifiers;
- artifact identifier while retained;
- SHA-256 digest;
- schema/version marker;
- authority and gate status;
- retention or external object-store locator when applicable.

Binary browser traces, screenshots, videos, test reports and diagnostics are temporary debugging material. They are not canonical product authority and must not be retained indefinitely.

## Retention classes

| Class | Material | Retention |
|---|---|---:|
| Debug | failed-run traces, screenshots, videos, diagnostics | 3 days |
| Routine evidence | successful non-closure CI evidence | 7 days |
| Candidate exact-head | active PR and release-candidate evidence | 14 days |
| Contractual closure | attestation, manifest, provenance, SBOM, signatures and cited bundles | 30 days minimum, with immutable metadata retained in Git |

## Protected material

Automated cleanup must not delete:

- artifacts from the default branch;
- artifacts belonging to the current head SHA of an open pull request;
- named closure, attestation, manifest, provenance, restore, SBOM or signature evidence;
- explicitly protected artifact IDs cited by contractual attestations.

## Cleanup authority

`.github/workflows/actions-storage-governance.yml` is the repository authority for automated cleanup. It runs daily and supports an auditable emergency execution through an issue whose title starts with `OPS: actions storage cleanup`.

The workflow uses `actions: write`, deletes only eligible obsolete artifacts, writes its report to the job summary, comments the triggering issue and closes it when successful. It creates no cleanup artifact of its own.

## Non-goals

- GitHub Actions caches are not used as evidence storage.
- Generated binaries are not committed to Git.
- Evidence is never made canonical merely by remaining downloadable from a workflow run.
