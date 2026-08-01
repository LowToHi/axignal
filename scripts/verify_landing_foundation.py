#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILLS = [
    "globe-engineer",
    "interaction-architect",
    "visualisation-designer",
    "frontend-architect",
    "performance-engineer",
    "accessibility-auditor",
    "hypothesis-curator",
    "analytics-engineer",
    "source-admission",
]
CITY_COORDS = {
    "Madrid": (40.4168, -3.7038),
    "London": (51.5074, -0.1278),
    "Paris": (48.8566, 2.3522),
    "Berlin": (52.52, 13.405),
}


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _version(value: object) -> tuple[int, int, int]:
    assert isinstance(value, str)
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", value)
    assert match is not None
    return tuple(int(part) for part in match.groups())


def main() -> int:
    for skill in SKILLS:
        path = ROOT / "skills" / skill / "SKILL.md"
        assert path.is_file(), f"missing skill {skill}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert re.search(rf"^name:\s*{re.escape(skill)}$", text, re.MULTILINE)
        assert re.search(r"^description:\s*.+$", text, re.MULTILINE)

    assets = load_json("docs/landing/assets-manifest.json")
    assert (1, 1, 0) <= _version(assets["version"]) < (2, 0, 0)
    assert assets["status"] in {
        "SOURCES_APPROVED_DIGESTS_NOT_PINNED",
        "SOURCES_APPROVED_DIGESTS_PINNED",
    }
    assert len(assets["external_assets"]) >= 5
    unpinned = 0
    for asset in assets["external_assets"]:
        assert asset["source_page"].startswith("https://")
        assert asset["acquisition_url"].startswith("https://")
        parsed = urlsplit(asset["acquisition_url"])
        assert parsed.hostname
        assert parsed.username is None and parsed.password is None
        assert parsed.port in {None, 443}
        assert Path(asset["filename"]).name == asset["filename"]
        assert parsed.hostname.casefold() in {
            host.casefold() for host in asset["allowed_hosts"]
        }
        assert asset["allowed_content_types"]
        assert 0 < asset["max_bytes"] <= 512 * 1024 * 1024
        assert 0 <= asset["max_redirects"] <= 5
        digest = asset["expected_sha256"]
        if digest is None:
            unpinned += 1
        else:
            assert re.fullmatch(r"[0-9a-f]{64}", digest)
        assert asset["hotlink"] is False
        assert asset["rights_basis"]
    if unpinned:
        assert assets["status"] == "SOURCES_APPROVED_DIGESTS_NOT_PINNED"
        assert "denied" in assets["production_rule"].casefold()
        assert "sha-256" in assets["production_rule"].casefold()

    demo = load_json("docs/landing/european-opportunity-risk-radar.json")
    assert demo["synthetic"] is True
    assert demo["dataset_id"] == "AXIGNAL-LANDING-EUROPE-001"
    assert {city["name"] for city in demo["cities"]} == set(CITY_COORDS)
    for city in demo["cities"]:
        lat, lon = CITY_COORDS[city["name"]]
        assert city["lat"] == lat and city["lon"] == lon
        assert 0 <= city["demo_score"] <= 100
        assert 0 <= city["confidence"] <= 100

    brand = load_json("docs/landing/brand-direction.json")
    assert brand["brand"] == "AXIGNAL"
    assert brand["globe"]["cities"] == ["Madrid", "London", "Paris", "Berlin"]
    assert brand["conversion"]["primary_cta"] == "Request access"

    print(
        json.dumps(
            {
                "status": "PASS",
                "skills": len(SKILLS),
                "external_asset_sources": len(assets["external_assets"]),
                "unpinned_asset_digests": unpinned,
                "remote_acquisition_fail_closed": unpinned > 0,
                "synthetic_demo_cities": len(demo["cities"]),
                "madrid_london_paris_berlin": True,
                "moscow_or_russian_fixture_in_landing": False,
                "production_globe_implemented": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
