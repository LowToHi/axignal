# F01-B — Legal and Privacy/Data Rights human authority

## Purpose

This runbook governs the only admissible transition from the retained F01 technical baseline to a private, bounded evidence campaign.

It does **not** admit the source, activate F01, authorise public redistribution, permit public claims or change public launch from `NO_GO`.

## Frozen technical baseline

```text
head SHA         db7758a2e250a80ba992b2ff28b0574b01393c82
tree SHA         f631a3efdc0199a1468bd96e3a2947ec7e32c3ec
workflow run     30777549236
artifact ID      8842563273
artifact digest  sha256:16a21241a43a0f6d4e7994179723110d7b227d719264d1dd8cdbb02608389e74
baseline digest  sha256:67e4e7c4d18261fbd087427b4a1a6f179ed5b32a29956a2c8637f566fff744b9
payload digest   sha256:190d3a1c61b14b6b4600d99ad45519a68a86c79c77aa22ef088efc2655b3f6a4
evidence expiry  2026-08-31T23:59:59Z
```

The authority manifest is:

```text
data/acceptance/approvals/AX-LIB-F01-rights-authority-manifest.v0.1.json
sha256:1cb8612a47d6ff8a20728ed996ca2d83cc454fedde361ceae473b3a083287f86
```

Any change to the manifest, target SHA, target tree, required assertions or evidence digest invalidates prior decisions.

## Human surfaces

```text
Legal                 issue #160
Privacy/Data Rights   issue #161
```

Only comments authored by a GitHub account whose API type is `User` are eligible. Bot identities and unsigned comments are ignored.

## Decision preparation

Create an unsigned JSON file containing every required field except `signature`. Use the exact assertion map published in the corresponding issue.

Generate the signed object:

```bash
python scripts/sign_gate7_f01_rights_decision.py \
  --input /path/to/unsigned-decision.json \
  --github-login YOUR_GITHUB_LOGIN
```

Post the resulting object inside one `json` fenced code block in the authority issue from the same GitHub login.

## Admitted decisions

```text
APPROVE
APPROVE_WITH_CONDITIONS
REJECT
```

`APPROVE` and `APPROVE_WITH_CONDITIONS` authorise only the private campaign when:

- both authorities are present;
- both signatures match the human comment authors;
- both decisions target the exact manifest and technical SHA;
- both assertion maps exactly equal the safe contract;
- both reviews are current;
- both expiries are no later than `2026-08-30T23:59:59Z` and strictly precede evidence expiry;
- neither authority rejects.

`REJECT` always blocks the campaign.

## Evaluation

Run the workflow on the F01-B branch:

```text
F01 Rights Human Authority
```

The workflow independently:

1. freezes the evaluator SHA;
2. proves the technical target is an ancestor with the expected Git tree;
3. retrieves the retained Actions artifact by immutable ID;
4. verifies artifact, baseline, payload and result digests;
5. revalidates all entry/concept counts and authority boundaries;
6. reads current comments from issues `#160` and `#161`;
7. accepts only the latest valid signed decision for each authority;
8. emits an authority envelope only when both authorities pass.

## Permanent boundary

Even when the private campaign becomes authorised:

```text
source state                         CANDIDATE
product admitted                     false
active source                        false
public claims authorised             false
public redistribution authorised     false
ISO standard text ingestion          false
ISO publication redistribution       false
model training                       false
profiling or marketing               false
F01                                  BLOCKED
claim decision                       DENIED
Gate 7                               IN_PROGRESS
public launch                        NO_GO
```

Further F01 acceptance phases must provide their own exact evidence and authority.