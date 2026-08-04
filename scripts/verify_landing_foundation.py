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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


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
        latitude, longitude = CITY_COORDS[city["name"]]
        assert city["lat"] == latitude and city["lon"] == longitude
        assert 0 <= city["demo_score"] <= 100
        assert 0 <= city["confidence"] <= 100

    brand = load_json("docs/landing/brand-direction.json")
    assert brand["brand"] == "AXIGNAL"
    assert brand["globe"]["cities"] == ["Madrid", "London", "Paris", "Berlin"]

    globe = read("apps/landing/components/semantic-globe.tsx")
    experience = read("apps/landing/components/landing-experience.tsx")
    assert "<Canvas" in globe
    assert experience.count("<SemanticGlobe") == 1

    evidence = {
        "status": "PASS",
        "scope": "LANDING_VISUAL_FOUNDATION_ONLY",
        "skills": len(SKILLS),
        "external_asset_sources": len(assets["external_assets"]),
        "synthetic_demo_cities": len(demo["cities"]),
        "madrid_london_paris_berlin_fixture_retained": True,
        "production_globe_implemented": True,
        "single_semantic_globe": True,
        "foundation_copy_is_commercial_authority": False,
        "canonical_commercial_authority": (
            "apps/landing/lib/canonical-commercial-contract.ts"
        ),
    }
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
