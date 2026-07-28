#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/landing/assets-manifest.json"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AXIGNAL asset acquisition/1.0"},
    )
    with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire approved AXIGNAL Globe source assets")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    selected = set(args.asset)
    records = []
    args.output.mkdir(parents=True, exist_ok=True)
    for asset in manifest["external_assets"]:
        if selected and asset["id"] not in selected:
            continue
        destination = args.output / Path(asset["acquisition_url"]).name
        record = {
            "id": asset["id"],
            "source_page": asset["source_page"],
            "destination": str(destination),
        }
        if not args.dry_run:
            download(asset["acquisition_url"], destination)
            record.update(
                {
                    "bytes": destination.stat().st_size,
                    "sha256": digest(destination),
                }
            )
        records.append(record)

    print(
        json.dumps(
            {
                "status": "DRY_RUN" if args.dry_run else "ACQUIRED",
                "assets": records,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
