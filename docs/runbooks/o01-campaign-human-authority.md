# O01-B — Legal and Privacy/Data Rights campaign authority

## Objective

Authorise only the private and bounded `AX-LIB-O01` evidence campaign. This phase does not admit TED into the product and does not authorise public claims, redistribution, marketing, model training, bid submission or public launch.

## Frozen target

```text
target head
b754b5641e5f17c5a084434aace4f939a4be0e84

target tree
615efd6e8a7f3369292775dbcf3223f8cc006f29

manifest reference
sha256:0c722eb4b02c4446ac26154b6ade49e1efb7b5c7787f8ac4925a0af8dd3d7898

official baseline digest
sha256:8fc00d8f5f555bd4061fd7874161cfb8f5765c92c3f43b19e98030d8e9a6251a

official evidence expiry
2026-08-29T00:20:27.229612Z

latest permitted decision expiry
2026-08-28T00:20:27.229612Z
```

A different target head or manifest reference invalidates every decision. An approval must expire strictly before the official evidence.

## Human authorities

Both authorities are mandatory:

```text
LEGAL
PRIVACY_DATA_RIGHTS
```

Accepted decisions:

```text
APPROVE
APPROVE_WITH_CONDITIONS
REJECT
```

The campaign is authorised only when both current decisions are `APPROVE` or `APPROVE_WITH_CONDITIONS`.

## Required decision object

Each authority posts one complete fenced JSON object in its authority issue:

```json
{
  "authority": "LEGAL or PRIVACY_DATA_RIGHTS",
  "decision": "APPROVE, APPROVE_WITH_CONDITIONS or REJECT",
  "scope": "Exact scope reviewed by the human authority",
  "manifest_reference": "sha256:0c722eb4b02c4446ac26154b6ade49e1efb7b5c7787f8ac4925a0af8dd3d7898",
  "head_sha": "b754b5641e5f17c5a084434aace4f939a4be0e84",
  "reviewed_at": "ISO-8601 UTC",
  "expires_at": "ISO-8601 UTC no later than 2026-08-28T00:20:27.229612Z",
  "signature": "github-identity-v1:<login>:<authority>:sha256:<unsigned-payload-digest>",
  "conditions": [
    "Explicit conditions, prohibitions and retention limits"
  ]
}
```

Field names are exact. Additional or missing fields are rejected.

## Human signature procedure

The authority first writes the eight fields excluding `signature` to a local JSON file. The helper computes the deterministic signature over the canonical unsigned payload:

```bash
python scripts/sign_gate7_o01_campaign_decision.py \
  --input decision-unsigned.json \
  --github-login <human-github-login>
```

The returned object must be posted by that same human GitHub account. The extractor requires GitHub user type `User`, rejects bot identities, binds the signature login to the comment author and verifies the payload digest. The helper does not post, approve or generate authority.

## Decision surfaces

```text
LEGAL issue                 #124
PRIVACY_DATA_RIGHTS issue   #125
```

Historical comments bound to earlier heads or manifests are ignored. The extractor selects only a correctly signed object bound to the current target and manifest.

## Evidence validation

Before evaluating decisions, the workflow:

1. proves the target commit and tree;
2. verifies the frozen campaign-contract digest;
3. verifies artifact `8826022309` is unexpired and has its recorded GitHub digest;
4. downloads the retained O01-A artifact;
5. verifies the official baseline file digest, target head/tree, payload digest and evidence expiry;
6. confirms the online baseline is present and the official terms are available.

## Fail-closed transitions

```text
both decisions absent          O01_CAMPAIGN_AUTHORITY_BLOCKED
one decision absent            O01_CAMPAIGN_AUTHORITY_BLOCKED
wrong head                     O01_CAMPAIGN_AUTHORITY_BLOCKED
wrong manifest                 O01_CAMPAIGN_AUTHORITY_BLOCKED
bot or invalid signature       O01_CAMPAIGN_AUTHORITY_BLOCKED
future review time             O01_CAMPAIGN_AUTHORITY_BLOCKED
expired decision               O01_CAMPAIGN_AUTHORITY_BLOCKED
expiry beyond evidence         O01_CAMPAIGN_AUTHORITY_BLOCKED
any REJECT                      O01_CAMPAIGN_AUTHORITY_BLOCKED
both current authorisations    O01_CAMPAIGN_AUTHORISED
```

## Permanent authority boundary

Even when `O01_CAMPAIGN_AUTHORISED` is emitted:

```text
TED product admission             false
public claims                      false
public redistribution              false
contact marketing                  false
model training or fine-tuning      false
bid submission                     false
public launch                      NO_GO
```

The resulting envelope authorises only execution of the private bounded evidence campaign against the exact target head and manifest. It does not change the TED source state from `CANDIDATE`.
