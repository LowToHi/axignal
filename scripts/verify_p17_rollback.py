#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P17_ENGINEERING_HEAD = "4f2d52bcff78bba020ede336f34e494b442fa898"
parent = Path(tempfile.mkdtemp(prefix="axignal-p17-rollback-"))
verification_dir = parent / "worktree"

try:
    subprocess.run(
        [
            "git",
            "worktree",
            "add",
            "--detach",
            str(verification_dir),
            P17_ENGINEERING_HEAD,
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [
            "python",
            str(verification_dir / "scripts/verify_p17_rollback.py"),
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
            "task_id": "AX-GE2E-P17-T01",
            "verification_head": P17_ENGINEERING_HEAD,
            "isolated_forward_compatible_rehearsal": True,
        },
        sort_keys=True,
    )
)
