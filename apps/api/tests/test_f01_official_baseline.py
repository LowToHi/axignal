from __future__ import annotations

import csv
import io
import json

import pytest
from scripts.build_gate7_f01_official_baseline import (
    BaselineError,
    derived_bucket,
    finalise_concepts,
    finalise_entries,
    parse_category_entries,
    parse_classification_csv,
    parse_full_list_json,
    parse_rdf_concepts,
    verify_sparql_parity,
)

SCHEMES = {f"{value:04d}" for value in range(1, 11)}
BASE = "http://publications.europa.eu/resource/authority/country/"
SKOS = "http://www.w3.org/2004/02/skos/core#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OWL = "http://www.w3.org/2002/07/owl#"
AUTH = "http://publications.europa.eu/ontology/authority/"


def classification_csv(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO()
    writer = csv.DictWriter(
        stream,
        fieldnames=[
            "country_uri",
            "country_en",
            "scheme",
            "deprecated",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def rdf_fixture() -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="{RDF}" xmlns:skos="{SKOS}"
         xmlns:owl="{OWL}" xmlns:authority="{AUTH}">
  <skos:ConceptScheme rdf:about="{BASE}" />
  <skos:ConceptScheme rdf:about="{BASE}0001" />
  <skos:ConceptScheme rdf:about="{BASE}0004" />
  <skos:Concept rdf:about="{BASE}AAA">
    <skos:prefLabel xml:lang="en">Alpha</skos:prefLabel>
    <skos:prefLabel xml:lang="es">Alfa</skos:prefLabel>
    <skos:inScheme rdf:resource="{BASE}0001" />
    <skos:notation rdf:datatype="{AUTH}notation-type/ISO_3166_1_ALPHA_3">
      AAA
    </skos:notation>
    <authority:start.use>2000-01-01</authority:start.use>
  </skos:Concept>
  <skos:Concept rdf:about="{BASE}OLD">
    <skos:prefLabel xml:lang="en">Old Alpha</skos:prefLabel>
    <skos:inScheme rdf:resource="{BASE}0004" />
    <owl:deprecated>true</owl:deprecated>
    <authority:end.use>1999-12-31</authority:end.use>
  </skos:Concept>
  <skos:Concept rdf:about="{BASE}RET">
    <skos:prefLabel xml:lang="en">Retired Alpha</skos:prefLabel>
    <skos:inScheme rdf:resource="{BASE}0003" />
    <owl:deprecated>true</owl:deprecated>
  </skos:Concept>
  <skos:Concept rdf:about="{BASE}OP_DATPRO">
    <skos:prefLabel xml:lang="en">Data provision</skos:prefLabel>
  </skos:Concept>
</rdf:RDF>
""".encode()


def category_fixture() -> bytes:
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<countries version="20260617-0">
  <record id="REC001" adm.status="current" deprecated="false">
    <authority-code>AAA</authority-code>
    <label><lg.version lg="eng">Alpha</lg.version></label>
    <start.use>2000-01-01</start.use>
    <country.membership country.classification="country" />
  </record>
  <record id="REC002" adm.status="deprecated" deprecated="true">
    <authority-code>AAA</authority-code>
    <label><lg.version lg="eng">Former Alpha name</lg.version></label>
    <end.use>1999-12-31</end.use>
    <country.membership country.classification="country" />
  </record>
  <record id="REC003" adm.status="deprecated" deprecated="true">
    <authority-code>OLD</authority-code>
    <label><lg.version lg="eng">Old Alpha</lg.version></label>
    <country.membership country.classification="disputed" />
  </record>
  <record id="REC004" adm.status="retired" deprecated="true">
    <authority-code>RET</authority-code>
    <label><lg.version lg="eng">Retired Alpha</lg.version></label>
    <parent.id>REC003</parent.id>
    <country.membership country.classification="territory" />
  </record>
</countries>
"""


def test_derived_bucket_precedence_is_fail_closed() -> None:
    assert derived_bucket("DEPRECATED", {"0004"}) == "HISTORICAL_OR_DEPRECATED"
    assert derived_bucket("CURRENT", {"0004", "0003"}) == "DISPUTED_ENTITY"
    assert derived_bucket("CURRENT", {"0002", "0003"}) == "MARINE_AREA"
    assert derived_bucket("CURRENT", {"0010", "0003"}) == "SPECIAL_STATUS_TERRITORY"
    assert derived_bucket("CURRENT", {"0003", "0001"}) == "TERRITORY"
    assert derived_bucket("CURRENT", {"0001"}) == "COUNTRY_OR_CITIZENSHIP_ENTITY"
    assert derived_bucket("CURRENT", set()) == "OTHER_GEOPOLITICAL_ENTITY"


def test_rdf_parser_preserves_concepts_schemes_and_iso_notation() -> None:
    concepts, scheme_count = parse_rdf_concepts(
        rdf_fixture(),
        allowed_schemes=SCHEMES,
    )
    assert scheme_count == 3
    assert set(concepts) == {f"{BASE}AAA", f"{BASE}OLD", f"{BASE}RET"}
    assert concepts[f"{BASE}AAA"]["official_scheme_ids"] == {"0001"}
    assert concepts[f"{BASE}AAA"]["label_languages"] == ["en", "es"]
    assert concepts[f"{BASE}AAA"]["notations"] == {
        "ISO_3166_1_ALPHA_3": {"AAA"}
    }
    assert concepts[f"{BASE}OLD"]["official_status"] == "DEPRECATED"
    final = finalise_concepts(concepts)
    assert final[0]["derived_bucket"] == "COUNTRY_OR_CITIZENSHIP_ENTITY"
    assert final[0]["standard_component_boundary"] == {
        "iso_mappings_present": True,
        "standard_text_ingested": False,
        "redistribution_authorised": False,
    }


def test_category_entries_retain_historical_duplicate_records() -> None:
    version, entries = parse_category_entries(category_fixture())
    assert version == "20260617-0"
    assert len(entries) == 4
    assert [entry["authority_code"] for entry in entries].count("AAA") == 2
    assert Counter(entry["entry_status"] for entry in entries) == {
        "CURRENT": 1,
        "DEPRECATED": 2,
        "RETIRED": 1,
    }


def test_entries_map_to_concepts_without_collapsing_record_history() -> None:
    concepts, _ = parse_rdf_concepts(
        rdf_fixture(),
        allowed_schemes=SCHEMES,
    )
    _, entries = parse_category_entries(category_fixture())
    final = finalise_entries(entries, concepts)
    assert len(final) == 4
    assert final[0]["derived_bucket"] == "COUNTRY_OR_CITIZENSHIP_ENTITY"
    assert final[1]["derived_bucket"] == "HISTORICAL_OR_DEPRECATED"
    assert final[3]["entry_status"] == "RETIRED"
    assert final[3]["parent_record_id"] == "REC003"


def test_sparql_csv_and_json_match_canonical_rdf() -> None:
    rdf_concepts, _ = parse_rdf_concepts(
        rdf_fixture(),
        allowed_schemes=SCHEMES,
    )
    rows = [
        {
            "country_uri": f"{BASE}AAA",
            "country_en": "Alpha",
            "scheme": f"{BASE}0001",
            "deprecated": "",
        },
        {
            "country_uri": f"{BASE}OLD",
            "country_en": "Old Alpha",
            "scheme": f"{BASE}0004",
            "deprecated": "true",
        },
        {
            "country_uri": f"{BASE}RET",
            "country_en": "Retired Alpha",
            "scheme": f"{BASE}0003",
            "deprecated": "true",
        },
    ]
    sparql = parse_classification_csv(
        classification_csv(rows),
        allowed_schemes=SCHEMES,
    )
    document = {
        "results": {
            "bindings": [
                {
                    "country_uri": {"value": row["country_uri"]},
                    "country_en": {"value": row["country_en"]},
                }
                for row in rows
            ]
        }
    }
    labels = parse_full_list_json(json.dumps(document).encode())
    verify_sparql_parity(rdf_concepts, sparql, labels)


def test_parity_rejects_missing_sparql_concept() -> None:
    rdf_concepts, _ = parse_rdf_concepts(
        rdf_fixture(),
        allowed_schemes=SCHEMES,
    )
    rows = [
        {
            "country_uri": f"{BASE}AAA",
            "country_en": "Alpha",
            "scheme": f"{BASE}0001",
            "deprecated": "",
        }
    ]
    sparql = parse_classification_csv(
        classification_csv(rows),
        allowed_schemes=SCHEMES,
    )
    with pytest.raises(BaselineError, match="classification sets differ"):
        verify_sparql_parity(
            rdf_concepts,
            sparql,
            {f"{BASE}AAA": "Alpha"},
        )


def test_category_parser_rejects_status_flag_mismatch() -> None:
    payload = category_fixture().replace(
        b'adm.status="retired" deprecated="true"',
        b'adm.status="retired" deprecated="false"',
    )
    with pytest.raises(BaselineError, match="Status/deprecated mismatch"):
        parse_category_entries(payload)
