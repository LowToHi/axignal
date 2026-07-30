#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
plan=json.loads((ROOT/"data/sovereign-macro/p13-rollback-plan.v0.1.json").read_text())
baseline=plan["baseline_sha"]
run=lambda *a:subprocess.run(a,cwd=ROOT,check=True,capture_output=True,text=True).stdout
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=sorted(x for x in run("git","diff","--name-only",f"{baseline}...HEAD").splitlines() if x)
assert changed==sorted(plan["expected_changed_paths"]),{"changed":changed}
before={p:digest(ROOT/p) for p in plan["preserved_p12_authority_files"]}
for rel in plan["p13_only_artifacts"]:
    path=ROOT/rel
    assert path.is_file(),rel
    path.unlink()
for rel in plan["restored_baseline_files"]:
    content=subprocess.run(["git","show",f"{baseline}:{rel}"],cwd=ROOT,check=True,capture_output=True).stdout
    (ROOT/rel).write_bytes(content)
after={p:digest(ROOT/p) for p in plan["preserved_p12_authority_files"]}
assert before==after
assert subprocess.run(["git","diff","--quiet",baseline,"--","."],cwd=ROOT).returncode==0
print(json.dumps({"status":"PASS","task_id":"AX-GE2E-P13-T01","baseline_sha":baseline,"changed_paths":len(changed),"restored_baseline_files":len(plan["restored_baseline_files"]),"residual_paths":0,"rolled_back_tree_equals_baseline":True},sort_keys=True))
