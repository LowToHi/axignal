from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

SKOS = "http://www.w3.org/2004/02/skos/core#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OWL = "http://www.w3.org/2002/07/owl#"
AUTH = "http://publications.europa.eu/ontology/authority/"
COUNTRY = "http://publications.europa.eu/resource/authority/country/"
GRAPH = "http://publications.europa.eu/resource/authority/country"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

CLASSIFICATION_QUERY = f"""
PREFIX skos: <{SKOS}>
PREFIX owl: <{OWL}>
SELECT ?country_uri ?country_en ?scheme ?deprecated
FROM <{GRAPH}>
WHERE {{
  ?country_uri a skos:Concept .
  ?country_uri skos:prefLabel ?label .
  FILTER(lang(?label) = "en")
  FILTER(?country_uri != <{COUNTRY}OP_DATPRO>)
  BIND(str(?label) AS ?country_en)
  OPTIONAL {{ ?country_uri skos:inScheme ?scheme }}
  OPTIONAL {{ ?country_uri owl:deprecated ?deprecated }}
}}
ORDER BY ?country_uri ?scheme
""".strip()

FULL_LIST_QUERY = f"""
PREFIX skos: <{SKOS}>
SELECT ?country_uri ?country_en
FROM <{GRAPH}>
WHERE {{
  ?country_uri a skos:Concept .
  ?country_uri skos:prefLabel ?label .
  FILTER(lang(?label) = "en")
  FILTER(?country_uri != <{COUNTRY}OP_DATPRO>)
  BIND(str(?label) AS ?country_en)
}}
ORDER BY ?country_uri
""".strip()


class BaselineError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_prefixed(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


@dataclass
class BudgetedHttpClient:
    maximum_requests: int
    timeout_seconds: int
    maximum_response_bytes: int
    requests_made: int = 0

    def fetch(
        self,
        url: str,
        *,
        method: str,
        accept: str,
        form: dict[str, str] | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        if not url.startswith("https://"):
            raise BaselineError("Only HTTPS access is permitted")
        if self.requests_made >= self.maximum_requests:
            raise BaselineError("Frozen HTTP request budget exhausted")
        self.requests_made += 1
        body = None
        headers = {
            "Accept": accept,
            "User-Agent": "AXIGNAL-F01-evidence/0.2",
        }
        request_url = url
        if form is not None:
            encoded = urllib.parse.urlencode(form)
            if method == "GET":
                separator = "&" if "?" in url else "?"
                request_url = f"{url}{separator}{encoded}"
            elif method == "POST":
                body = encoded.encode("utf-8")
                headers["Content-Type"] = (
                    "application/x-www-form-urlencoded"
                )
            else:
                raise BaselineError(f"Unsupported HTTP method: {method}")
        request = urllib.request.Request(
            request_url,
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout_seconds,
            ) as response:
                payload = response.read(self.maximum_response_bytes + 1)
                if len(payload) > self.maximum_response_bytes:
                    raise BaselineError(
                        "Response exceeded frozen byte budget"
                    )
                status = int(response.status)
                if status < 200 or status >= 300:
                    raise BaselineError(
                        f"Unexpected HTTP status: {status}"
                    )
                metadata = {
                    "request_number": self.requests_made,
                    "method": method,
                    "url": request_url,
                    "status": status,
                    "content_type": response.headers.get("Content-Type"),
                    "content_length": len(payload),
                    "content_digest": sha256_prefixed(payload),
                }
                return payload, metadata
        except BaselineError:
            raise
        except Exception as exc:
            raise BaselineError(
                f"Official endpoint access failed without retry: {exc}"
            ) from exc


def _scheme_id(uri: str, allowed: set[str]) -> str | None:
    value = uri.rstrip("/").rsplit("/", 1)[-1]
    return value if value in allowed else None


def _datatype_name(uri: str) -> str:
    return uri.rsplit("#", 1)[-1].rstrip("/").rsplit("/", 1)[-1]


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None


def _bool_text(value: str | None) -> bool:
    return (value or "").strip().casefold() in {"true", "1"}


def extract_latest_version(payload: bytes, expected: str) -> str:
    text = payload.decode("utf-8", errors="replace")
    pattern = rf"\b{re.escape(expected)}\b[^\n]{{0,80}}\bLATEST\b"
    if re.search(pattern, text) or (expected in text and "LATEST" in text):
        return expected
    matches = re.findall(r"\b(20\d{6}-\d)\b", text)
    observed = ", ".join(sorted(set(matches))[-8:])
    raise BaselineError(
        "Expected latest catalogue version not proven; observed versions: "
        + observed
    )


def extract_downloads_url(catalogue_payload: bytes) -> str:
    text = catalogue_payload.decode("utf-8", errors="replace")

    def extract(patterns: tuple[str, ...], name: str) -> str:
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return html.unescape(match.group(1))
        raise BaselineError(f"Unable to extract {name}")

    namespace = extract(
        (
            r"conceptDisplayPortletNamespace\s*=\s*['\"]([^'\"]+)['\"]",
            r"portletNamespace\s*=\s*['\"]([^'\"]+)['\"]",
        ),
        "concept display namespace",
    )
    render_url = extract(
        (r"tabPageRenderUrl\s*=\s*['\"]([^'\"]+)['\"]",),
        "tab page render URL",
    )
    separator = "&" if "?" in render_url else "?"
    parameter = urllib.parse.quote(namespace, safe="_") + "tabPageId=14"
    return f"{render_url}{separator}{parameter}"


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.current: dict[str, str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.current = {"href": href, "text": ""}

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current is not None:
            self.current["text"] = " ".join(
                self.current["text"].split()
            )
            self.links.append(self.current)
            self.current = None


def parse_distributions(payload: bytes, base_url: str) -> dict[str, str]:
    parser = _LinkParser()
    parser.feed(payload.decode("utf-8", errors="replace"))
    distributions: dict[str, str] = {}
    for link in parser.links:
        name = link["text"]
        if not name:
            continue
        if name in distributions:
            raise BaselineError(f"Duplicate distribution name: {name}")
        distributions[name] = urllib.parse.urljoin(
            base_url,
            link["href"],
        )
    return distributions


def parse_rdf_concepts(
    payload: bytes,
    *,
    allowed_schemes: set[str],
) -> tuple[dict[str, dict[str, Any]], int]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise BaselineError("Canonical RDF distribution is invalid") from exc
    concepts: dict[str, dict[str, Any]] = {}
    concept_scheme_count = 0
    for resource in root:
        if resource.tag == f"{{{SKOS}}}ConceptScheme":
            concept_scheme_count += 1
            continue
        if resource.tag != f"{{{SKOS}}}Concept":
            continue
        uri = resource.attrib.get(f"{{{RDF}}}about", "")
        if not uri.startswith(COUNTRY):
            continue
        if uri == f"{COUNTRY}OP_DATPRO":
            continue
        if uri in concepts:
            raise BaselineError(f"Duplicate RDF concept: {uri}")
        labels: dict[str, str] = {}
        schemes: set[str] = set()
        notations: dict[str, set[str]] = {}
        deprecated = False
        start_use = None
        end_use = None
        for child in resource:
            if child.tag == f"{{{SKOS}}}prefLabel":
                language = child.attrib.get(XML_LANG, "")
                value = _text(child)
                if language and value:
                    labels[language] = value
            elif child.tag == f"{{{SKOS}}}inScheme":
                scheme_uri = child.attrib.get(f"{{{RDF}}}resource", "")
                scheme = _scheme_id(scheme_uri, allowed_schemes)
                if scheme is not None:
                    schemes.add(scheme)
            elif child.tag == f"{{{SKOS}}}notation":
                datatype = child.attrib.get(f"{{{RDF}}}datatype", "")
                value = _text(child)
                if datatype and value:
                    name = _datatype_name(datatype)
                    notations.setdefault(name, set()).add(value)
            elif child.tag == f"{{{OWL}}}deprecated":
                deprecated = _bool_text(_text(child))
            elif child.tag == f"{{{AUTH}}}start.use":
                start_use = _text(child)
            elif child.tag == f"{{{AUTH}}}end.use":
                end_use = _text(child)
        if "en" not in labels:
            raise BaselineError(f"RDF concept lacks English label: {uri}")
        concepts[uri] = {
            "uri": uri,
            "authority_code": uri.rsplit("/", 1)[-1],
            "label_en": labels["en"],
            "label_languages": sorted(labels),
            "official_status": "DEPRECATED" if deprecated else "CURRENT",
            "official_scheme_ids": schemes,
            "notations": notations,
            "start_use": start_use,
            "end_use": end_use,
        }
    return concepts, concept_scheme_count


def parse_classification_csv(
    payload: bytes,
    *,
    allowed_schemes: set[str],
) -> dict[str, dict[str, Any]]:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {
        "country_uri",
        "country_en",
        "scheme",
        "deprecated",
    }
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise BaselineError("SPARQL CSV columns do not match contract")
    concepts: dict[str, dict[str, Any]] = {}
    for row in reader:
        uri = (row.get("country_uri") or "").strip()
        label = (row.get("country_en") or "").strip()
        if not uri.startswith(COUNTRY) or not label:
            raise BaselineError("Invalid SPARQL concept URI or English label")
        concept = concepts.setdefault(
            uri,
            {
                "uri": uri,
                "label_en": label,
                "official_status": "CURRENT",
                "official_scheme_ids": set(),
            },
        )
        if concept["label_en"] != label:
            raise BaselineError(f"Conflicting SPARQL label for {uri}")
        scheme_uri = (row.get("scheme") or "").strip()
        scheme = _scheme_id(scheme_uri, allowed_schemes)
        if scheme is not None:
            concept["official_scheme_ids"].add(scheme)
        if _bool_text(row.get("deprecated")):
            concept["official_status"] = "DEPRECATED"
    return concepts


def parse_full_list_json(payload: bytes) -> dict[str, str]:
    try:
        document = json.loads(payload)
        bindings = document["results"]["bindings"]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise BaselineError("SPARQL JSON result is not valid") from exc
    concepts: dict[str, str] = {}
    for binding in bindings:
        uri = binding["country_uri"]["value"]
        label = binding["country_en"]["value"]
        if uri in concepts and concepts[uri] != label:
            raise BaselineError(f"Conflicting JSON label for {uri}")
        concepts[uri] = label
    return concepts


def parse_category_entries(
    payload: bytes,
) -> tuple[str, list[dict[str, Any]]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise BaselineError("Canonical category XML is invalid") from exc
    if root.tag != "countries":
        raise BaselineError(f"Unexpected category root tag: {root.tag}")
    version = root.attrib.get("version", "")
    entries: list[dict[str, Any]] = []
    seen_record_ids: set[str] = set()
    for record in root.findall("record"):
        record_id = record.attrib.get("id", "")
        if not record_id or record_id in seen_record_ids:
            raise BaselineError("Missing or duplicate category record ID")
        seen_record_ids.add(record_id)
        authority_code = _text(record.find("authority-code"))
        label_en = _text(record.find("label/lg.version[@lg='eng']"))
        status = record.attrib.get("adm.status", "").upper()
        if not authority_code or not label_en:
            raise BaselineError(f"Incomplete category record: {record_id}")
        if status not in {"CURRENT", "DEPRECATED", "RETIRED"}:
            raise BaselineError(
                f"Unsupported category status for {record_id}: {status}"
            )
        deprecated_flag = record.attrib.get("deprecated", "").casefold()
        expected_flag = "false" if status == "CURRENT" else "true"
        if deprecated_flag != expected_flag:
            raise BaselineError(
                f"Status/deprecated mismatch for category record {record_id}"
            )
        membership = record.find("country.membership")
        entries.append(
            {
                "record_id": record_id,
                "authority_code": authority_code,
                "concept_uri": f"{COUNTRY}{authority_code}",
                "label_en": label_en,
                "entry_status": status,
                "start_use": _text(record.find("start.use")),
                "end_use": _text(record.find("end.use")),
                "parent_record_id": _text(record.find("parent.id")),
                "country_classification": (
                    membership.attrib.get("country.classification")
                    if membership is not None
                    else None
                ),
            }
        )
    return version, entries


def derived_bucket(status: str, schemes: set[str]) -> str:
    if status != "CURRENT":
        return "HISTORICAL_OR_DEPRECATED"
    if "0004" in schemes:
        return "DISPUTED_ENTITY"
    if "0002" in schemes:
        return "MARINE_AREA"
    if "0010" in schemes:
        return "SPECIAL_STATUS_TERRITORY"
    if "0003" in schemes:
        return "TERRITORY"
    if "0001" in schemes:
        return "COUNTRY_OR_CITIZENSHIP_ENTITY"
    return "OTHER_GEOPOLITICAL_ENTITY"


def finalise_concepts(
    concepts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for uri in sorted(concepts):
        item = concepts[uri]
        schemes = set(item["official_scheme_ids"])
        notations = {
            key: sorted(values)
            for key, values in sorted(item["notations"].items())
        }
        result.append(
            {
                "uri": item["uri"],
                "authority_code": item["authority_code"],
                "label_en": item["label_en"],
                "label_languages": item["label_languages"],
                "official_status": item["official_status"],
                "official_scheme_ids": sorted(schemes),
                "derived_bucket": derived_bucket(
                    item["official_status"],
                    schemes,
                ),
                "start_use": item["start_use"],
                "end_use": item["end_use"],
                "notations": notations,
                "standard_component_boundary": {
                    "iso_mappings_present": any(
                        key.startswith("ISO_") for key in notations
                    ),
                    "standard_text_ingested": False,
                    "redistribution_authorised": False,
                },
            }
        )
    return result


def finalise_entries(
    entries: list[dict[str, Any]],
    concepts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in sorted(entries, key=lambda item: item["record_id"]):
        uri = entry["concept_uri"]
        concept = concepts.get(uri)
        if concept is None:
            raise BaselineError(
                f"Category record references unknown concept: {uri}"
            )
        schemes = set(concept["official_scheme_ids"])
        result.append(
            {
                **entry,
                "concept_label_en": concept["label_en"],
                "concept_status": concept["official_status"],
                "official_scheme_ids": sorted(schemes),
                "derived_bucket": derived_bucket(
                    entry["entry_status"],
                    schemes,
                ),
            }
        )
    return result


def verify_sparql_parity(
    rdf_concepts: dict[str, dict[str, Any]],
    sparql_concepts: dict[str, dict[str, Any]],
    json_labels: dict[str, str],
) -> None:
    rdf_uris = set(rdf_concepts)
    if set(sparql_concepts) != rdf_uris:
        raise BaselineError("RDF and SPARQL classification sets differ")
    if set(json_labels) != rdf_uris:
        raise BaselineError("RDF and SPARQL JSON sets differ")
    for uri in sorted(rdf_uris):
        rdf_item = rdf_concepts[uri]
        sparql_item = sparql_concepts[uri]
        if rdf_item["label_en"] != sparql_item["label_en"]:
            raise BaselineError(f"RDF/SPARQL label mismatch for {uri}")
        if rdf_item["label_en"] != json_labels[uri]:
            raise BaselineError(f"RDF/JSON label mismatch for {uri}")
        if rdf_item["official_status"] != sparql_item["official_status"]:
            raise BaselineError(f"RDF/SPARQL status mismatch for {uri}")
        if (
            set(rdf_item["official_scheme_ids"])
            != set(sparql_item["official_scheme_ids"])
        ):
            raise BaselineError(f"RDF/SPARQL scheme mismatch for {uri}")


def require_count(actual: int, expected: int, label: str) -> None:
    if actual != expected:
        raise BaselineError(
            f"Expected {expected} {label}, observed {actual}"
        )


def build_baseline(
    contract: dict[str, Any],
    *,
    exact_head_sha: str,
    output_dir: Path,
) -> dict[str, Any]:
    publication = contract["official_publication"]
    access = contract["access_contract"]
    schemes = set(contract["concept_schemes"])
    client = BudgetedHttpClient(
        maximum_requests=access["maximum_http_requests"],
        timeout_seconds=access["timeout_seconds_per_request"],
        maximum_response_bytes=access["maximum_response_bytes_per_request"],
    )
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    access_records: list[dict[str, Any]] = []

    def fetch_raw(
        name: str,
        url: str,
        *,
        method: str,
        accept: str,
        form: dict[str, str] | None = None,
    ) -> bytes:
        payload, metadata = client.fetch(
            url,
            method=method,
            accept=accept,
            form=form,
        )
        access_records.append(metadata)
        (raw_dir / name).write_bytes(payload)
        return payload

    catalogue = fetch_raw(
        "catalogue.html",
        publication["catalogue_url"],
        method="GET",
        accept="text/html",
    )
    latest_version = extract_latest_version(
        catalogue,
        publication["expected_latest_version"],
    )
    downloads_url = extract_downloads_url(catalogue)
    downloads_tab = fetch_raw(
        "downloads-tab.html",
        downloads_url,
        method="GET",
        accept="text/html",
    )
    distributions = parse_distributions(downloads_tab, downloads_url)
    required_distributions = set(publication["required_distributions"])
    if set(distributions) != required_distributions:
        raise BaselineError("Official distribution inventory drift")
    rdf_name = publication["canonical_concept_distribution"]
    xml_name = publication["canonical_entry_distribution"]
    rdf_url = distributions[rdf_name]
    xml_url = distributions[xml_name]
    version_token = f"/{latest_version}/"
    if version_token not in urllib.parse.unquote(rdf_url):
        raise BaselineError("RDF distribution is not bound to latest version")
    if version_token not in urllib.parse.unquote(xml_url):
        raise BaselineError("Category XML is not bound to latest version")

    rdf_payload = fetch_raw(
        rdf_name,
        rdf_url,
        method="GET",
        accept="application/rdf+xml",
    )
    xml_payload = fetch_raw(
        xml_name,
        xml_url,
        method="GET",
        accept="application/xml",
    )
    classification_csv = fetch_raw(
        "classification.csv",
        publication["sparql_endpoint"],
        method="POST",
        accept="text/csv",
        form={"query": CLASSIFICATION_QUERY, "format": "text/csv"},
    )
    full_list_json = fetch_raw(
        "full-list.json",
        publication["sparql_endpoint"],
        method="GET",
        accept="application/sparql-results+json",
        form={
            "query": FULL_LIST_QUERY,
            "format": "application/sparql-results+json",
        },
    )

    rdf_concepts, concept_scheme_count = parse_rdf_concepts(
        rdf_payload,
        allowed_schemes=schemes,
    )
    category_version, raw_entries = parse_category_entries(xml_payload)
    if category_version != latest_version:
        raise BaselineError("Category XML version does not match catalogue")
    sparql_concepts = parse_classification_csv(
        classification_csv,
        allowed_schemes=schemes,
    )
    json_labels = parse_full_list_json(full_list_json)
    verify_sparql_parity(rdf_concepts, sparql_concepts, json_labels)

    expected = publication
    require_count(
        len(rdf_concepts),
        expected["expected_canonical_concept_count"],
        "canonical concepts",
    )
    require_count(
        concept_scheme_count,
        len(schemes) + 1,
        "RDF concept schemes including the root scheme",
    )
    require_count(
        len(raw_entries),
        expected["expected_category_xml_record_count"],
        "category XML records",
    )
    retired_entries = [
        entry for entry in raw_entries
        if entry["entry_status"] == "RETIRED"
    ]
    published_entries = [
        entry for entry in raw_entries
        if entry["entry_status"] != "RETIRED"
    ]
    require_count(
        len(retired_entries),
        expected["expected_retired_record_count"],
        "retired category records",
    )
    require_count(
        len(published_entries),
        expected["expected_catalogue_entry_count"],
        "non-retired catalogue entries",
    )
    published_codes = {
        entry["authority_code"] for entry in published_entries
    }
    require_count(
        len(published_codes),
        expected["expected_non_retired_unique_concept_count"],
        "non-retired unique authority codes",
    )
    duplicate_surplus = len(published_entries) - len(published_codes)
    require_count(
        duplicate_surplus,
        expected["expected_non_retired_duplicate_record_surplus"],
        "duplicate historical record instances",
    )
    all_entry_codes = {entry["authority_code"] for entry in raw_entries}
    rdf_codes = {
        concept["authority_code"] for concept in rdf_concepts.values()
    }
    if all_entry_codes != rdf_codes:
        raise BaselineError("Category XML and RDF authority-code sets differ")

    final_concepts = finalise_concepts(rdf_concepts)
    final_entries = finalise_entries(raw_entries, rdf_concepts)
    final_published_entries = [
        entry for entry in final_entries
        if entry["entry_status"] != "RETIRED"
    ]
    final_retired_entries = [
        entry for entry in final_entries
        if entry["entry_status"] == "RETIRED"
    ]
    concept_bucket_counts = Counter(
        item["derived_bucket"] for item in final_concepts
    )
    entry_bucket_counts = Counter(
        item["derived_bucket"] for item in final_published_entries
    )
    concept_status_counts = Counter(
        item["official_status"] for item in final_concepts
    )
    entry_status_counts = Counter(
        item["entry_status"] for item in final_published_entries
    )
    scheme_subsets = {
        scheme: [
            item["authority_code"]
            for item in final_concepts
            if scheme in item["official_scheme_ids"]
        ]
        for scheme in sorted(schemes)
    }
    concept_subsets = {
        bucket: [
            item["authority_code"]
            for item in final_concepts
            if item["derived_bucket"] == bucket
        ]
        for bucket in contract["derived_bucket_precedence"]
    }
    entry_subsets = {
        bucket: [
            item["record_id"]
            for item in final_published_entries
            if item["derived_bucket"] == bucket
        ]
        for bucket in contract["derived_bucket_precedence"]
    }
    records_by_code: dict[str, list[str]] = {}
    for entry in final_published_entries:
        records_by_code.setdefault(entry["authority_code"], []).append(
            entry["record_id"]
        )
    duplicate_groups = {
        code: sorted(record_ids)
        for code, record_ids in sorted(records_by_code.items())
        if len(record_ids) > 1
    }
    raw_evidence = {
        path.name: sha256_prefixed(path.read_bytes())
        for path in sorted(raw_dir.iterdir())
        if path.is_file()
    }
    payload = {
        "schema_version": "axignal.f01-official-baseline/v0.2",
        "library_id": contract["library_id"],
        "source_id": contract["source_id"],
        "source_state": "CANDIDATE",
        "lineage": contract["lineage"],
        "official_publication_version": latest_version,
        "authority_graph_uri": publication["authority_graph_uri"],
        "distribution_inventory": [
            {"name": name, "url": distributions[name]}
            for name in sorted(distributions)
        ],
        "access_contract": access,
        "access_proof": access_records,
        "raw_evidence_digests": raw_evidence,
        "count_semantics": contract["count_semantics"],
        "count_reconciliation": {
            "category_xml_records": len(final_entries),
            "catalogue_non_retired_entries": len(final_published_entries),
            "retired_entries": len(final_retired_entries),
            "non_retired_unique_authority_codes": len(published_codes),
            "non_retired_duplicate_record_surplus": duplicate_surplus,
            "canonical_concepts": len(final_concepts),
            "rdf_concept_schemes_including_root": concept_scheme_count,
            "sparql_concepts": len(sparql_concepts),
            "rdf_sparql_exact_parity": True,
        },
        "concept_status_counts": dict(sorted(concept_status_counts.items())),
        "published_entry_status_counts": dict(
            sorted(entry_status_counts.items())
        ),
        "concept_derived_bucket_counts": dict(
            sorted(concept_bucket_counts.items())
        ),
        "published_entry_derived_bucket_counts": dict(
            sorted(entry_bucket_counts.items())
        ),
        "official_scheme_subsets": scheme_subsets,
        "canonical_concept_subsets": concept_subsets,
        "published_entry_subsets": entry_subsets,
        "duplicate_historical_record_groups": duplicate_groups,
        "canonical_concepts": final_concepts,
        "published_entries": final_published_entries,
        "retired_entries": final_retired_entries,
        "rights_boundary": contract["rights_boundary"],
        "privacy_boundary": contract["privacy_boundary"],
        "campaign_plan": contract["campaign_plan"],
        "authority_boundary": {
            "technical_baseline_present": True,
            "legal_decision": "MISSING",
            "privacy_data_rights_decision": "MISSING",
            "campaign_authorised": False,
            "product_admitted": False,
            "active_source": False,
            "f01_state": "BLOCKED",
            "claim_decision": "DENIED",
            "gate7": "IN_PROGRESS",
            "public_launch": "NO_GO",
        },
    }
    payload_digest = sha256_prefixed(canonical_bytes(payload))
    baseline = {
        "status": "PASS",
        "output": "F01_OFFICIAL_CONTENT_ADDRESSED_BASELINE_PASS",
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "exact_head_sha": exact_head_sha,
        "baseline_payload_digest": payload_digest,
        "evidence_expires_at": contract["evidence_expires_at"],
        "baseline_payload": payload,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = output_dir / "official-online-baseline.v0.2.json"
    baseline_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    result = {
        "status": "PASS",
        "output": baseline["output"],
        "exact_head_sha": exact_head_sha,
        "official_publication_version": latest_version,
        "catalogue_entry_count": len(final_published_entries),
        "category_xml_record_count": len(final_entries),
        "retired_record_count": len(final_retired_entries),
        "canonical_concept_count": len(final_concepts),
        "non_retired_unique_concept_count": len(published_codes),
        "duplicate_record_surplus": duplicate_surplus,
        "baseline_payload_digest": payload_digest,
        "baseline_file_digest": sha256_prefixed(baseline_path.read_bytes()),
        "http_requests_used": client.requests_made,
        "http_request_budget": client.maximum_requests,
        "external_monetary_spend_eur": 0,
        "technical_baseline": "PRESENT",
        "legal": "MISSING",
        "privacy_data_rights": "MISSING",
        "campaign_authorised": False,
        "f01_state": "BLOCKED",
        "claim_decision": "DENIED",
        "gate7": "IN_PROGRESS",
        "public_launch": "NO_GO",
    }
    (output_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--exact-head-sha",
        default=os.environ.get("AXIGNAL_EXACT_SHA", ""),
    )
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.exact_head_sha):
        raise BaselineError("A valid exact head SHA is required")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = build_baseline(
        contract,
        exact_head_sha=args.exact_head_sha,
        output_dir=args.output_dir,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
