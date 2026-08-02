from __future__ import annotations

import argparse
import json
import ssl
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from axignal_api.o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from axignal_api.o01_quality_common import canonical_json_bytes, sha256_prefixed
from axignal_api.o01_quality_failure import sanitise_ted_error_body
from axignal_api.o01_quality_http import request_payload

REQUEST_DELAY_SECONDS = 2.0
RATE_LIMIT_WAIT_SECONDS = 10.0
MAXIMUM_REQUESTS = 20


def projection_cases(contract: dict[str, Any]) -> list[tuple[str, list[str]]]:
    configured = [
        str(value)
        for value in contract["fields"]["ephemeral_contact_projection"]
    ]
    publication_number = "publication-number"
    contact_fields = [value for value in configured if value != publication_number]
    cases: list[tuple[str, list[str]]] = [
        ("CONTROL_START", [publication_number]),
    ]
    cases.extend(
        (f"FIELD_{field.upper().replace('-', '_')}", [publication_number, field])
        for field in contact_fields
    )
    cases.extend(
        [
            ("FULL_EPHEMERAL_CONTACT_PROJECTION", configured),
            ("CONTROL_END", [publication_number]),
        ]
    )
    return cases


def execute_case(
    *,
    name: str,
    fields: list[str],
    endpoint: str,
    query: str,
    contract: dict[str, Any],
    selected_address: str,
    allowed_hosts: frozenset[str],
    request_counter: list[int],
) -> dict[str, Any]:
    parsed = validate_official_url(endpoint, allowed_hosts=allowed_hosts)
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    payload = request_payload(
        query=query,
        fields=fields,
        page=1,
        plan=contract,
    )
    body = canonical_json_bytes(payload)
    attempts: list[dict[str, Any]] = []
    final_status: int | None = None

    for attempt in range(1, 3):
        if request_counter[0] >= MAXIMUM_REQUESTS:
            raise RuntimeError("Diagnostic request budget exceeded")
        request_counter[0] += 1
        connection = PinnedHTTPSConnection(
            host=parsed.hostname or "",
            port=parsed.port or 443,
            selected_address=selected_address,
            timeout=float(contract["sampling"]["request_timeout_seconds"]),
            context=ssl.create_default_context(),
        )
        try:
            started = time.monotonic()
            connection.request(
                "POST",
                path,
                body=body,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "identity",
                    "Cache-Control": "no-cache",
                    "Connection": "close",
                    "Content-Type": "application/json",
                    "User-Agent": "AXIGNAL-O01-Contact-Projection-Diagnostic/1.0",
                },
            )
            response = connection.getresponse()
            response_body = response.read(
                int(contract["sampling"]["maximum_response_bytes"]) + 1
            )
            final_status = response.status
            attempt_result: dict[str, Any] = {
                "attempt": attempt,
                "http_status": response.status,
                "content_type": response.getheader("Content-Type", ""),
                "retry_after": response.getheader("Retry-After"),
                "response_bytes": len(response_body),
                "response_body_sha256": sha256_prefixed(response_body),
                "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
                "raw_response_retained": False,
            }
            if response.status >= 400:
                attempt_result["sanitised_diagnostic"] = sanitise_ted_error_body(
                    response_body
                )
            attempts.append(attempt_result)
            if response.status == 429 and attempt == 1:
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                continue
            break
        finally:
            connection.close()
        
    time.sleep(REQUEST_DELAY_SECONDS)
    return {
        "case": name,
        "fields": fields,
        "field_count": len(fields),
        "request_body_sha256": sha256_prefixed(body),
        "attempts": attempts,
        "final_http_status": final_status,
        "accepted": final_status == 200,
        "raw_response_retained": False,
    }


def classify(results: list[dict[str, Any]]) -> dict[str, Any]:
    field_results = {
        result["fields"][-1]: result["accepted"]
        for result in results
        if result["case"].startswith("FIELD_")
    }
    unsupported = sorted(
        field for field, accepted in field_results.items() if not accepted
    )
    full = next(
        result
        for result in results
        if result["case"] == "FULL_EPHEMERAL_CONTACT_PROJECTION"
    )
    controls = [
        result
        for result in results
        if result["case"] in {"CONTROL_START", "CONTROL_END"}
    ]
    controls_pass = all(result["accepted"] for result in controls)
    if not controls_pass:
        outcome = "INCONCLUSIVE_CONTROL_FAILURE"
    elif unsupported:
        outcome = "UNSUPPORTED_CONTACT_FIELDS_IDENTIFIED"
    elif not full["accepted"]:
        outcome = "COMBINATION_OR_FIELD_COUNT_DEFECT"
    else:
        outcome = "CONTACT_PROJECTION_ACCEPTED"
    return {
        "classification": outcome,
        "controls_pass": controls_pass,
        "unsupported_fields": unsupported,
        "all_individual_fields_accepted": not unsupported,
        "full_projection_accepted": full["accepted"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--authority-envelope", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    authority = json.loads(args.authority_envelope.read_text(encoding="utf-8"))
    if authority.get("output") != "O01_CAMPAIGN_AUTHORISED":
        raise SystemExit("Current human authority is required")
    expiry = datetime.fromisoformat(
        str(authority["effective_expiry"]).replace("Z", "+00:00")
    )
    if expiry.tzinfo is None or datetime.now(UTC) >= expiry:
        raise SystemExit("Human authority is expired")

    sampling = contract["sampling"]
    country = str(sampling["countries"][0])
    query = str(sampling["query_contract"]).format(country=country)
    endpoint = str(contract["source"]["endpoint"])
    allowed_hosts = frozenset(
        str(value) for value in contract["source"]["allowed_hosts"]
    )
    parsed = validate_official_url(endpoint, allowed_hosts=allowed_hosts)
    addresses = resolve_public_addresses(parsed.hostname or "", parsed.port or 443)
    selected_address = select_address(addresses)

    request_counter = [0]
    results = [
        execute_case(
            name=name,
            fields=fields,
            endpoint=endpoint,
            query=query,
            contract=contract,
            selected_address=selected_address,
            allowed_hosts=allowed_hosts,
            request_counter=request_counter,
        )
        for name, fields in projection_cases(contract)
    ]
    classification = classify(results)
    output = {
        "schema_version": "axignal.o01-contact-projection-diagnostic/v0.1",
        "status": "PASS",
        "output": "O01_CONTACT_PROJECTION_DIAGNOSTIC_COMPLETE",
        "country_stratum": country,
        "page": 1,
        "same_query": True,
        "same_selected_address": True,
        "selected_address_sha256": sha256_prefixed(
            selected_address.encode("utf-8")
        ),
        "resolved_address_count": len(addresses),
        "network_requests_used": request_counter[0],
        "network_requests_maximum": MAXIMUM_REQUESTS,
        "cases": results,
        **classification,
        "raw_response_retained": False,
        "contact_values_retained": False,
        "campaign_evidence_contribution": False,
        "public_claim_contribution": False,
        "source_state": "CANDIDATE",
        "fabricated_evidence": 0,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
