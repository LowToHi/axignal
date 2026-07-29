from __future__ import annotations

import re
from pathlib import Path

DEPLOY_PATH = Path("infra/landing/deploy.sh")
EXPECTED_LINE = (
    'for name in re.findall(r"--certificatesresolvers\\.([A-Za-z0-9_-]+)\\.", '
    'args, re.I):'
)
PATTERN = r"--certificatesresolvers\.([A-Za-z0-9_-]+)\."

source = DEPLOY_PATH.read_text(encoding="utf-8")
assert EXPECTED_LINE in source
assert "[A-Za-z0-9_.-]+" not in source.split("--certificatesresolvers", 1)[1].split(
    "args, re.I", 1
)[0]

real_args = """
--entrypoints.web.address=:80
--entrypoints.websecure.address=:443
--certificatesresolvers.letsencrypt.acme.email=ops@example.com
--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json
--certificatesresolvers.letsencrypt.acme.httpchallenge=true
--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web
"""
assert sorted(set(re.findall(PATTERN, real_args, re.I))) == ["letsencrypt"]

multiple_roots = real_args + "\n--certificatesresolvers.backup.acme.storage=/backup.json\n"
assert sorted(set(re.findall(PATTERN, multiple_roots, re.I))) == [
    "backup",
    "letsencrypt",
]

print("traefik resolver parser contract: PASS")
