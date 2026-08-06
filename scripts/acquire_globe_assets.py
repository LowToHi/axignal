#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from asset_download_security import (
    AssetDownloadError,
    AssetDownloadPolicy,
    download_asset,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/landing/assets-manifest.json"


def _safe_filename(value: object) -> str:
    if not isinstance(value, str) or not value or Path(value).name != value:
        raise AssetDownloadError("Asset manifest filename must be a safe basename")
    return value


def _string_set(asset: dict[str, Any], key: str) -> frozenset[str]:
    value = asset.get(key)
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) for item in value
    ):
        raise AssetDownloadError(f"Asset manifest {key} must be a non-empty string list")
    return frozenset(value)


def _positive_int(asset: dict[str, Any], key: str) -> int:
    value = asset.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise AssetDownloadError(f"Asset manifest {key} must be a positive integer")
    return value


def _nonnegative_int(asset: dict[str, Any], key: str) -> int:
    value = asset.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise AssetDownloadError(f"Asset manifest {key} must be a non-negative integer")
    return value


def policy_from_asset(asset: dict[str, Any]) -> AssetDownloadPolicy:
    expected_sha256 = asset.get("expected_sha256")
    if not isinstance(expected_sha256, str):
        raise AssetDownloadError("Asset manifest requires a pinned expected_sha256")
    return AssetDownloadPolicy(
        allowed_hosts=_string_set(asset, "allowed_hosts"),
        allowed_content_types=_string_set(asset, "allowed_content_types"),
        max_bytes=_positive_int(asset, "max_bytes"),
        expected_sha256=expected_sha256,
        max_redirects=_nonnegative_int(asset, "max_redirects"),
    )


def _dry_run_record(asset: dict[str, Any], destination: Path) -> dict[str, object]:
    expected = asset.get("expected_sha256")
    return {
        "id": asset.get("id"),
        "source_page": asset.get("source_page"),
        "destination": str(destination),
        "allowed_hosts": sorted(_string_set(asset, "allowed_hosts")),
        "allowed_content_types": sorted(_string_set(asset, "allowed_content_types")),
        "max_bytes": _positive_int(asset, "max_bytes"),
        "max_redirects": _nonnegative_int(asset, "max_redirects"),
        "digest_pinned": isinstance(expected, str) and len(expected) == 64,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire approved AXIGNAL Globe source assets")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    selected = set(args.asset)
    records: list[dict[str, object]] = []
    args.output.mkdir(parents=True, exist_ok=True)
    try:
        for asset in manifest["external_assets"]:
            if selected and asset["id"] not in selected:
                continue
            filename = _safe_filename(asset.get("filename"))
            destination = args.output / filename
            if args.dry_run:
                records.append(_dry_run_record(asset, destination))
                continue
            result = download_asset(
                str(asset["acquisition_url"]),
                destination,
                policy_from_asset(asset),
            )
            records.append(
                {
                    "id": asset["id"],
                    "source_page": asset["source_page"],
                    "destination": str(destination),
                    "bytes": result.bytes_written,
                    "sha256": result.sha256,
                    "content_type": result.content_type,
                    "redirects": result.redirects,
                }
            )
    except (AssetDownloadError, KeyError, TypeError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "DENIED",
                    "error": str(exc),
                    "assets": records,
                },
                indent=2,
            )
        )
        return 2

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
