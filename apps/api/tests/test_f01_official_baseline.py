from __future__ import annotations

import csv
import io
import json

import pytest
from scripts.build_gate7_f01_official_baseline import (
    BaselineError,
    apply_notations_csv,
    derived_bucket,
    finalise_concepts,
    parse_classification_csv,
    parse_full_list_json,
)

SCHEMES = {f"{value:04d}" for value in range(1, 11)}
BASE = "http://publications.europa.eu/resource/authority/country/"


def classification_csv(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "country_uri",
            "country_en",
            "scheme",
            "deprecated",
            "status",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def test_derived_bucket_precedence_is_fail_closed() -> None:
    assert derived_bucket("DEPRECATED", {"0004"}) == "HISTORICAL_OR_DEPRECATED"
    assert derived_bucket("CURRENT", {"0004", "0003"}) == "DISPUTED_ENTITY"
    assert derived_bucket("CURRENT", {"0002", "0003"}) == "MARINE_AREA"
    assert derived_bucket("CURRENT", {"0010", "0003"}) == "SPECIAL_STATUS_TERRITORY"
    assert derived_bucket("CURRENT", {"0003", "0001"}) == "TERRITORY"
    assert derived_bucket("CURRENT", {"0001"}) == "COUNTRY_OR_CITIZENSHIP_ENTITY"
    assert derived_bucket("CURRENT", set()) == "OTHER_GEOPOLITICAL_ENTITY"


def test_fold_preserves_official_memberships_and_notations() -> None:
    payload = classification_csv(
        [
            {
                "country_uri": f"{BASE}AAA",
                "country_en": "Alpha",
                "scheme": f"{BASE}0001",
                "deprecated": "",
                "status": "",
            },
            {
                "country_uri": f"{BASE}AAA",
                "country_en": "Alpha",
                "scheme": f"{BASE}0005",
                "deprecated": "",
                "status": "",
            },
            {
                "country_uri": f"{BASE}OLD",
                "country_en": "Old Alpha",
                "scheme": f"{BASE}0004",
                "deprecated": "true",
                "status": "",
            },
        ]
    )
    concepts = parse_classification_csv(payload, allowed_schemes=SCHEMES)
    notation_payload = (
        "country_uri,notation_type,notation_value\n"
        f"{BASE}AAA,http://publications.europa.eu/resource/authority/"
        "notation-type/ISO_3166_1_ALPHA_3,AAA\n"
        f"{BASE}OLD,,\n"
    ).encode()
    apply_notations_csv(notation_payload, concepts)
    final = finalise_concepts(concepts)
    assert final[0]["official_scheme_ids"] == ["0001", "0005"]
    assert final[0]["derived_bucket"] == "COUNTRY_OR_CITIZENSHIP_ENTITY"
    assert final[0]["notations"]["ISO_3166_1_ALPHA_3"] == ["AAA"]
    assert final[0]["standard_component_boundary"] == {
        "iso_mappings_present": True,
        "standard_text_ingested": False,
        "redistribution_authorised": False,
    }
    assert final[1]["derived_bucket"] == "HISTORICAL_OR_DEPRECATED"


def test_json_and_csv_surfaces_can_be_compared_exactly() -> None:
    payload = {
        "head": {"vars": ["country_uri", "country_en"]},
        "results": {
            "bindings": [
                {
                    "country_uri": {"type": "uri", "value": f"{BASE}AAA"},
                    "country_en": {"type": "literal", "value": "Alpha"},
                }
            ]
        },
    }
    assert parse_full_list_json(json.dumps(payload).encode()) == {
        f"{BASE}AAA": "Alpha"
    }


def test_conflicting_labels_are_rejected() -> None:
    payload = classification_csv(
        [
            {
                "country_uri": f"{BASE}AAA",
                "country_en": "Alpha",
                "scheme": f"{BASE}0001",
                "deprecated": "",
                "status": "",
            },
            {
                "country_uri": f"{BASE}AAA",
                "country_en": "Different",
                "scheme": f"{BASE}0005",
                "deprecated": "",
                "status": "",
            },
        ]
    )
    with pytest.raises(BaselineError, match="Conflicting English label"):
        parse_classification_csv(payload, allowed_schemes=SCHEMES)
