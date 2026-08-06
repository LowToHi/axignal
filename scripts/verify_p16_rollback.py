#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P16_ENGINEERING_HEAD = "daf3b4339051dfa3317e89f61e520e51ea36fbb7"
parent = Path(tempfile.mkdtemp(prefix="axignal-p16-rollback-"))
verification_dir = parent / "worktree"

try:
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "--detach",
            str(verification_dir),
            P16_ENGINEERING_HEAD,
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "python",
            str(verification_dir / "scripts/verify_p16_rollback.py"),
        ],
        cwd=verification_dir,
        check=True,
    )
finally:
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(verification_dir)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.rmtree(parent, ignore_errors=True)

print(
    json.dumps(
        {
            "status": "PASS",
            "task_id": "AX-GE2E-P16-T01",
            "verification_head": P16_ENGINEERING_HEAD,
            "isolated_forward_compatible_rehearsal": True,
        },
        sort_keys=True,
    )
)
