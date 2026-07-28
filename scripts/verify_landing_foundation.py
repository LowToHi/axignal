#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

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


def main() -> int:
    for skill in SKILLS:
        path = ROOT / "skills" / skill / "SKILL.md"
        assert path.is_file(), f"missing skill {skill}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert re.search(rf"^name:\s*{re.escape(skill)}$", text, re.MULTILINE)
        assert re.search(r"^description:\s*.+$", text, re.MULTILINE)

    assets = load_json("docs/landing/assets-manifest.json")
    assert assets["version"] == "1.0.0"
    assert len(assets["external_assets"]) >= 5
    for asset in assets["external_assets"]:
        assert asset["source_page"].startswith("https://")
        assert asset["acquisition_url"].startswith("https://")
        assert asset["hotlink"] is False
        assert asset["rights_basis"]

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
