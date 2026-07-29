#!/usr/bin/env python3
"""Fail-closed validation for the AXIGNAL global procurement source catalogue."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/sources/global-public-procurement-catalogue.v0.2.json"
EXPECTED_HEADER = [
    "source_id",
    "region",
    "jurisdiction",
    "government_level",
    "system_name",
    "official_entry_point",
    "access_class",
    "priority_class",
    "state",
    "discovery_basis",
    "notes",
]
ALLOWED_PRIORITIES = {"P0", "P1", "P2", "P3", "P4"}
ALLOWED_STATES = {
    "DISCOVERED",
    "LEGAL_REVIEW",
    "TECHNICAL_PROBE",
    "SANDBOX",
    "INTERNAL_ONLY",
    "PRODUCT_ADMITTED",
    "RESTRICTED",
    "SUSPENDED",
    "REVOKED",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_inventory(paths: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for relative_path in paths:
        path = ROOT / relative_path
        require(path.is_file(), f"missing inventory file: {relative_path}")
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            require(reader.fieldnames == EXPECTED_HEADER, f"unexpected CSV header: {relative_path}")
            rows.extend(dict(row) for row in reader)
    return rows


def validate_url(row: dict[str, str]) -> None:
    url = row["official_entry_point"].strip()
    if not url:
        require(
            row["access_class"] == "OFFICIAL_IDENTITY_TO_VERIFY",
            f"blank official entry point outside identity-verification class: {row['source_id']}",
        )
        return
    parsed = urlparse(url)
    require(parsed.scheme == "https", f"non-HTTPS official entry point: {row['source_id']}")
    require(bool(parsed.netloc), f"invalid official entry point: {row['source_id']}")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(manifest["catalogue_id"] == "AX-GPP-SOURCE-CATALOGUE-001", "catalogue identity drift")
    require(manifest["version"] == "0.2.0", "catalogue version drift")
    require(manifest["goal_id"] == "AXIGNAL-GOAL-001", "goal identity drift")
    require(sum(manifest["priority_model"]["weights"].values()) == 100, "priority weights must sum to 100")

    rows = load_inventory(manifest["inventory_files"])
    require(len(rows) >= 140, "catalogue breadth regressed below 140 source families")

    source_ids = [row["source_id"] for row in rows]
    require(len(source_ids) == len(set(source_ids)), "duplicate source_id")
    require(all(source_ids), "blank source_id")

    for row in rows:
        require(row["priority_class"] in ALLOWED_PRIORITIES, f"invalid priority: {row['source_id']}")
        require(row["state"] in ALLOWED_STATES, f"invalid state: {row['source_id']}")
        require(bool(row["jurisdiction"].strip()), f"blank jurisdiction: {row['source_id']}")
        require(bool(row["system_name"].strip()), f"blank system name: {row['source_id']}")
        validate_url(row)

    priority_counts = Counter(row["priority_class"] for row in rows)
    region_counts = Counter(row["region"] for row in rows)
    jurisdiction_scope_count = len({(row["jurisdiction"], row["government_level"]) for row in rows})

    summary = manifest["inventory_summary"]
    require(summary["source_family_count"] == len(rows), "source family count mismatch")
    require(summary["jurisdiction_scope_count"] == jurisdiction_scope_count, "jurisdiction scope count mismatch")
    require(summary["priority_counts"] == dict(priority_counts), "priority counts mismatch")
    require(summary["region_counts"] == dict(region_counts), "region counts mismatch")

    p0 = [row["source_id"] for row in rows if row["priority_class"] == "P0"]
    require(p0 == ["EU_TED"], "TED must remain the sole P0 implementation wedge")
    require(not any(row["state"] == "PRODUCT_ADMITTED" for row in rows), "catalogue must not admit sources")

    queue = manifest["implementation_queue"]
    ranks = [item["rank"] for item in queue]
    queue_ids = [item["source_id"] for item in queue]
    require(ranks == list(range(1, len(queue) + 1)), "implementation ranks must be contiguous")
    require(len(queue_ids) == len(set(queue_ids)), "duplicate source in implementation queue")
    require(set(queue_ids).issubset(set(source_ids)), "implementation queue references unknown source")
    require(queue_ids[0] == "US_SAM_OPPORTUNITIES", "SAM.gov must be the first post-TED source priority")
    require("NG_NOCOPO_OCDS" not in queue_ids, "NOCOPO must remain in the worldwide backlog, not the top queue")

    boundary = manifest["authority_boundary"]
    require(boundary["ted_product_admitted"] is False, "TED product admission falsely enabled")
    require(boundary["new_sources_product_admitted"] == 0, "new source admission falsely enabled")
    require(boundary["global_coverage_marketing_authorised"] is False, "global marketing falsely enabled")
    require(boundary["billing_or_trial_activated"] is False, "billing or trial falsely enabled")

    evidence = {
        "catalogue_id": manifest["catalogue_id"],
        "version": manifest["version"],
        "source_family_count": len(rows),
        "jurisdiction_scope_count": jurisdiction_scope_count,
        "inventory_file_count": len(manifest["inventory_files"]),
        "implementation_queue_count": len(queue),
        "first_post_ted_priority": queue_ids[0],
        "no_product_admitted": True,
        "global_marketing_authorised": False,
    }
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
