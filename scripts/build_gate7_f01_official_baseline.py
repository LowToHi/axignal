from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SKOS = "http://www.w3.org/2004/02/skos/core#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OWL = "http://www.w3.org/2002/07/owl#"
DCT = "http://purl.org/dc/terms/"
EUVOC = "http://publications.europa.eu/ontology/euvoc#"
COUNTRY = "http://publications.europa.eu/resource/authority/country/"
GRAPH = "http://publications.europa.eu/resource/authority/country"

CLASSIFICATION_QUERY = f"""
PREFIX skos: <{SKOS}>
PREFIX owl: <{OWL}>
PREFIX euvoc: <{EUVOC}>
SELECT ?country_uri ?country_en ?scheme ?deprecated ?status
FROM <{GRAPH}>
WHERE {{
  ?country_uri a skos:Concept .
  ?country_uri skos:prefLabel ?label .
  FILTER(lang(?label) = "en")
  FILTER(?country_uri != <{COUNTRY}OP_DATPRO>)
  BIND(str(?label) AS ?country_en)
  OPTIONAL {{ ?country_uri skos:inScheme ?scheme }}
  OPTIONAL {{ ?country_uri owl:deprecated ?deprecated }}
  OPTIONAL {{ ?country_uri euvoc:status ?status }}
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

NOTATIONS_QUERY = f"""
PREFIX skos: <{SKOS}>
PREFIX euvoc: <{EUVOC}>
PREFIX rdf: <{RDF}>
PREFIX dct: <{DCT}>
SELECT ?country_uri ?notation_type ?notation_value
FROM <{GRAPH}>
WHERE {{
  ?country_uri a skos:Concept .
  FILTER(?country_uri != <{COUNTRY}OP_DATPRO>)
  OPTIONAL {{
    ?country_uri euvoc:xlNotation ?notation .
    ?notation rdf:value ?notation_value .
    ?notation dct:type ?notation_type .
  }}
}}
ORDER BY ?country_uri ?notation_type ?notation_value
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
            "User-Agent": "AXIGNAL-F01-evidence/0.1",
        }
        request_url = url
        if form is not None:
            encoded = urllib.parse.urlencode(form)
            if method == "GET":
                request_url = f"{url}?{encoded}"
            elif method == "POST":
                body = encoded.encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded"
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
                    raise BaselineError("Response exceeded frozen byte budget")
                status = int(response.status)
                if status < 200 or status >= 300:
                    raise BaselineError(f"Unexpected HTTP status: {status}")
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


def _normalise_status(deprecated: str, status: str) -> str:
    lowered = deprecated.strip().casefold()
    if lowered in {"true", "1"}:
        return "DEPRECATED"
    if status.rstrip("/").endswith("RETIRED"):
        return "RETIRED"
    return "CURRENT"


def _merge_status(left: str, right: str) -> str:
    order = {"CURRENT": 0, "RETIRED": 1, "DEPRECATED": 2}
    return left if order[left] >= order[right] else right


def _scheme_id(uri: str, allowed: set[str]) -> str | None:
    value = uri.rstrip("/").rsplit("/", 1)[-1]
    return value if value in allowed else None


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
        "status",
    }
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise BaselineError("SPARQL CSV columns do not match contract")
    concepts: dict[str, dict[str, Any]] = {}
    for row in reader:
        uri = (row.get("country_uri") or "").strip()
        label = (row.get("country_en") or "").strip()
        if not uri.startswith(COUNTRY) or not label:
            raise BaselineError("Invalid concept URI or English label")
        concept = concepts.setdefault(
            uri,
            {
                "uri": uri,
                "authority_code": uri.rsplit("/", 1)[-1],
                "label_en": label,
                "official_scheme_ids": set(),
                "official_status": "CURRENT",
                "notations": {},
            },
        )
        if concept["label_en"] != label:
            raise BaselineError(f"Conflicting English label for {uri}")
        scheme = _scheme_id((row.get("scheme") or "").strip(), allowed_schemes)
        if scheme is not None:
            concept["official_scheme_ids"].add(scheme)
        observed_status = _normalise_status(
            row.get("deprecated") or "",
            row.get("status") or "",
        )
        concept["official_status"] = _merge_status(
            concept["official_status"],
            observed_status,
        )
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


def apply_notations_csv(
    payload: bytes,
    concepts: dict[str, dict[str, Any]],
) -> None:
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {"country_uri", "notation_type", "notation_value"}
    if reader.fieldnames is None or not required.issubset(reader.fieldnames):
        raise BaselineError("Notation CSV columns do not match contract")
    for row in reader:
        uri = (row.get("country_uri") or "").strip()
        if uri not in concepts:
            raise BaselineError(f"Notation references unknown concept: {uri}")
        type_uri = (row.get("notation_type") or "").strip()
        value = (row.get("notation_value") or "").strip()
        if not type_uri and not value:
            continue
        if not type_uri or not value:
            raise BaselineError(f"Incomplete notation for {uri}")
        notation_type = type_uri.rstrip("/").rsplit("/", 1)[-1]
        bucket = concepts[uri]["notations"].setdefault(notation_type, set())
        bucket.add(value)


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
                "official_status": item["official_status"],
                "official_scheme_ids": sorted(schemes),
                "derived_bucket": derived_bucket(
                    item["official_status"],
                    schemes,
                ),
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


def extract_latest_version(payload: bytes, expected: str) -> str:
    text = payload.decode("utf-8", errors="replace")
    if re.search(rf"\b{re.escape(expected)}\b[^\n]{{0,80}}\bLATEST\b", text):
        return expected
    if expected in text and "LATEST" in text:
        return expected
    matches = re.findall(r"\b(20\d{6}-\d)\b", text)
    raise BaselineError(
        "Expected latest catalogue version not proven; observed versions: "
        + ", ".join(sorted(set(matches))[-8:])
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

    catalogue, metadata = client.fetch(
        publication["catalogue_url"],
        method="GET",
        accept="text/html",
    )
    access_records.append(metadata)
    (raw_dir / "catalogue.html").write_bytes(catalogue)
    latest_version = extract_latest_version(
        catalogue,
        publication["expected_latest_version"],
    )

    classification_csv, metadata = client.fetch(
        publication["sparql_endpoint"],
        method="POST",
        accept="text/csv",
        form={"query": CLASSIFICATION_QUERY, "format": "text/csv"},
    )
    access_records.append(metadata)
    (raw_dir / "classification.csv").write_bytes(classification_csv)
    concepts = parse_classification_csv(
        classification_csv,
        allowed_schemes=schemes,
    )

    full_list_json, metadata = client.fetch(
        publication["sparql_endpoint"],
        method="GET",
        accept="application/sparql-results+json",
        form={
            "query": FULL_LIST_QUERY,
            "format": "application/sparql-results+json",
        },
    )
    access_records.append(metadata)
    (raw_dir / "full-list.json").write_bytes(full_list_json)
    json_concepts = parse_full_list_json(full_list_json)
    csv_labels = {uri: item["label_en"] for uri, item in concepts.items()}
    if json_concepts != csv_labels:
        raise BaselineError("CSV and JSON concept surfaces are not identical")

    notations_csv, metadata = client.fetch(
        publication["sparql_endpoint"],
        method="POST",
        accept="text/csv",
        form={"query": NOTATIONS_QUERY, "format": "text/csv"},
    )
    access_records.append(metadata)
    (raw_dir / "notations.csv").write_bytes(notations_csv)
    apply_notations_csv(notations_csv, concepts)

    expected_count = int(publication["expected_concept_count"])
    if len(concepts) != expected_count:
        raise BaselineError(
            f"Expected {expected_count} concepts, observed {len(concepts)}"
        )
    final_concepts = finalise_concepts(concepts)
    bucket_counts = Counter(item["derived_bucket"] for item in final_concepts)
    status_counts = Counter(item["official_status"] for item in final_concepts)
    scheme_subsets = {
        scheme: [
            item["authority_code"]
            for item in final_concepts
            if scheme in item["official_scheme_ids"]
        ]
        for scheme in sorted(schemes)
    }
    derived_subsets = {
        bucket: [
            item["authority_code"]
            for item in final_concepts
            if item["derived_bucket"] == bucket
        ]
        for bucket in contract["derived_bucket_precedence"]
    }
    raw_evidence = {
        path.name: sha256_prefixed(path.read_bytes())
        for path in sorted(raw_dir.iterdir())
        if path.is_file()
    }
    payload = {
        "schema_version": "axignal.f01-official-baseline/v0.1",
        "library_id": contract["library_id"],
        "source_id": contract["source_id"],
        "source_state": "CANDIDATE",
        "lineage": contract["lineage"],
        "official_publication_version": latest_version,
        "authority_graph_uri": publication["authority_graph_uri"],
        "access_contract": access,
        "access_proof": access_records,
        "raw_evidence_digests": raw_evidence,
        "concept_count": len(final_concepts),
        "status_counts": dict(sorted(status_counts.items())),
        "derived_bucket_counts": dict(sorted(bucket_counts.items())),
        "official_scheme_subsets": scheme_subsets,
        "derived_subsets": derived_subsets,
        "concepts": final_concepts,
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
    baseline_path = output_dir / "official-online-baseline.v0.1.json"
    baseline_path.write_text(
        json.dumps(baseline, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    result = {
        "status": "PASS",
        "output": baseline["output"],
        "exact_head_sha": exact_head_sha,
        "official_publication_version": latest_version,
        "concept_count": len(final_concepts),
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
