#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = [
    "docs/research/P01-global-buyer-workflow-market-evidence-v0.1.md",
    "docs/research/P01-primary-research-protocol-v1.0.md",
    "data/research/p01-desk-evidence-register.v0.1.json",
    "data/research/p01-buyer-workflow-hypotheses.v0.1.json",
    "data/research/p01-primary-research-manifest.v0.1.json",
    "schemas/p01-research-session.schema.json",
    "docs/gates/AX-GE2E-P01-gate-v1.4.json",
]

for rel in REQUIRED:
    assert (ROOT / rel).is_file(), f"missing {rel}"

evidence = json.loads(
    (ROOT / "data/research/p01-desk-evidence-register.v0.1.json").read_text(
        encoding="utf-8"
    )
)
assert evidence["task_id"] == "AX-GE2E-P01-T01"
assert evidence["status"] == "SECONDARY_EVIDENCE_ONLY_PRIMARY_RESEARCH_MISSING"
assert len(evidence["sources"]) >= 24
assert len({item["source_id"] for item in evidence["sources"]}) == len(
    evidence["sources"]
)
libraries_with_evidence = {item["library_id"] for item in evidence["sources"]}
assert libraries_with_evidence == {f"AX-LIB-O{i:02d}" for i in range(1, 10)}
assert all(item["url"].startswith("https://") for item in evidence["sources"])
assert any(
    item["evidence_class"] == "OFFICIAL_STATISTICS"
    for item in evidence["sources"]
)
assert any(
    item["evidence_class"] == "OFFICIAL_VENDOR"
    for item in evidence["sources"]
)

hypotheses = json.loads(
    (ROOT / "data/research/p01-buyer-workflow-hypotheses.v0.1.json").read_text(
        encoding="utf-8"
    )
)
assert hypotheses["status"] == "HYPOTHESES_NOT_VALIDATED"
assert len(hypotheses["library_hypotheses"]) == 9
assert {
    item["library_id"] for item in hypotheses["library_hypotheses"]
} == {f"AX-LIB-O{i:02d}" for i in range(1, 10)}
for item in hypotheses["library_hypotheses"]:
    assert item["primary_operator_roles"]
    assert item["economic_buyers"]
    assert item["current_stack"]
    assert item["high_cost_failures"]
    assert item["workflow_required"]
    assert item["primary_research_needed"]
    assert item["budget_hypothesis_eur_month"]

schema = json.loads(
    (ROOT / "schemas/p01-research-session.schema.json").read_text(
        encoding="utf-8"
    )
)
Draft202012Validator.check_schema(schema)

manifest = json.loads(
    (ROOT / "data/research/p01-primary-research-manifest.v0.1.json").read_text(
        encoding="utf-8"
    )
)
assert manifest["status"] == "RECRUITMENT_NOT_STARTED"
assert manifest["primary_research_complete"] is False
assert manifest["unique_participants"] == 0
assert manifest["required_unique_participants"] == 45
assert len(manifest["library_quotas"]) == 9
assert all(
    item["complete"] == 0 and item["required"] == 5
    for item in manifest["library_quotas"].values()
)
assert manifest["sessions"] == []
assert manifest["public_launch_authorised"] is False

gate = json.loads(
    (ROOT / "docs/gates/AX-GE2E-P01-gate-v1.4.json").read_text(
        encoding="utf-8"
    )
)
assert gate["state"] == "IN_PROGRESS"
assert gate["decision"] == "NOT_READY_FOR_HUMAN_ACCEPTANCE"
assert gate["truth_boundary"]["desk_research_complete"] is True
assert gate["truth_boundary"]["primary_research_complete"] is False
assert gate["truth_boundary"]["buyer_personas_validated"] is False
assert gate["truth_boundary"]["pricing_validated"] is False
assert gate["truth_boundary"]["p02_authorised"] is False
assert gate["truth_boundary"]["public_launch_authorised"] is False

task_index = json.loads(
    (ROOT / "data/programmes/global-e2e-task-registry.v1.4.json").read_text(
        encoding="utf-8"
    )
)
tasks = []
for shard in task_index["shards"]:
    shard_data = json.loads((ROOT / shard["path"]).read_text(encoding="utf-8"))
    tasks.extend(shard_data["tasks"])

p01 = next(item for item in tasks if item["task_id"] == "AX-GE2E-P01-T01")
assert p01["state"] == "IN_PROGRESS"
assert "ux-researcher" in {item["skill_id"] for item in p01["skills"]}

routing = yaml.safe_load(
    (ROOT / "skills/global-e2e-routing.yaml").read_text(encoding="utf-8")
)
p01_route = next(item for item in routing["phase_routes"] if item["phase"] == "P01")
assert set(p01_route["required_skills"]) == {
    "ux-researcher",
    "hypothesis-curator",
    "product-analyst",
}

current = (
    ROOT / "docs/roadmap/06-current-execution-state.md"
).read_text(encoding="utf-8")
assert "P01 IN_PROGRESS" in current
assert "primary research remains missing" in current
assert '"public_launch_authorised": false' in current
assert "P02–P24" in current and "`BLOCKED`" in current

print(
    json.dumps(
        {
            "status": "PASS",
            "task": "AX-GE2E-P01-T01",
            "desk_sources": len(evidence["sources"]),
            "libraries_covered": len(libraries_with_evidence),
            "primary_sessions": manifest["unique_participants"],
            "primary_research_complete": False,
            "p02_authorised": False,
            "public_launch_authorised": False,
        },
        sort_keys=True,
    )
)
