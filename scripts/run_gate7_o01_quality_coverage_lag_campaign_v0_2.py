from __future__ import annotations

import argparse
import json
import ssl
import time
from pathlib import Path
from typing import Any

from axignal_api.o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from axignal_api.o01_quality_common import canonical_json_bytes, sha256_prefixed
from axignal_api.o01_quality_http import request_payload

EVIDENCE_UA = "AXIGNAL-O01-C-Evidence/1.0"
DIAGNOSTIC_UA = "AXIGNAL-O01-C-Diagnostic/1.0"
SEQUENCE = (EVIDENCE_UA, DIAGNOSTIC_UA, DIAGNOSTIC_UA, EVIDENCE_UA)


def one_request(
    *,
    host: str,
    port: int,
    path: str,
    selected_address: str,
    body: bytes,
    user_agent: str,
    timeout: float,
    maximum_bytes: int,
) -> dict[str, Any]:
    connection = PinnedHTTPSConnection(
        host=host,
        port=port,
        selected_address=selected_address,
        timeout=timeout,
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
                "User-Agent": user_agent,
            },
        )
        response = connection.getresponse()
        response_body = response.read(maximum_bytes + 1)
        return {
            "user_agent": user_agent,
            "http_status": response.status,
            "content_type": response.getheader("Content-Type", ""),
            "response_bytes": len(response_body),
            "response_body_sha256": sha256_prefixed(response_body),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
            "raw_response_retained": False,
        }
    finally:
        connection.close()


def classify(observations: list[dict[str, Any]]) -> str:
    evidence = [
        item["http_status"]
        for item in observations
        if item["user_agent"] == EVIDENCE_UA
    ]
    diagnostic = [
        item["http_status"]
        for item in observations
        if item["user_agent"] == DIAGNOSTIC_UA
    ]
    if evidence == [400, 400] and diagnostic == [200, 200]:
        return "USER_AGENT_DEPENDENT"
    statuses = [item["http_status"] for item in observations]
    if statuses == [400, 200, 200, 200]:
        return "FIRST_REQUEST_DEPENDENT"
    if len(set(evidence)) > 1 or len(set(diagnostic)) > 1:
        return "NON_DETERMINISTIC"
    if evidence == [200, 200] and diagnostic == [200, 200]:
        return "ALL_ACCEPTED"
    return "OTHER_STABLE_DIFFERENCE"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authority-envelope", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--kill-switch-path", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.authority_envelope.is_file():
        raise SystemExit("Current authority envelope is missing")
    if args.raw_dir.exists() or args.kill_switch_path.exists():
        raise SystemExit("Diagnostic requires clean ephemeral paths")

    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    sampling = plan["sampling"]
    country = str(sampling["countries"][0])
    query = str(sampling["query_contract"]).format(country=country)
    fields = [str(item) for item in plan["fields"]["retained_raw_projection"]]
    payload = request_payload(query=query, fields=fields, page=1, plan=plan)
    body = canonical_json_bytes(payload)

    endpoint = str(plan["source"]["endpoint"])
    allowed_hosts = frozenset(str(item) for item in plan["source"]["allowed_hosts"])
    parsed = validate_official_url(endpoint, allowed_hosts=allowed_hosts)
    host = parsed.hostname or ""
    port = parsed.port or 443
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    addresses = resolve_public_addresses(host, port)
    selected_address = select_address(addresses)

    observations: list[dict[str, Any]] = []
    for index, user_agent in enumerate(SEQUENCE, start=1):
        observation = one_request(
            host=host,
            port=port,
            path=path,
            selected_address=selected_address,
            body=body,
            user_agent=user_agent,
            timeout=float(sampling["request_timeout_seconds"]),
            maximum_bytes=int(sampling["maximum_response_bytes"]),
        )
        observation["sequence"] = index
        observations.append(observation)
        time.sleep(max(0.5, float(sampling["minimum_delay_seconds"])))

    result = {
        "schema_version": "axignal.o01-transport-identity-diagnostic/v0.1",
        "status": "PASS",
        "output": "O01_TRANSPORT_IDENTITY_DIAGNOSTIC_COMPLETE",
        "classification": classify(observations),
        "requests": len(observations),
        "request_body_sha256": sha256_prefixed(body),
        "same_request_body": True,
        "same_selected_address": True,
        "selected_address_sha256": sha256_prefixed(selected_address.encode("utf-8")),
        "observations": observations,
        "raw_response_retained": False,
        "campaign_evidence_contribution": False,
        "public_claim_contribution": False,
        "source_state": "CANDIDATE",
        "fabricated_evidence": 0,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "transport-identity-diagnostic.v0.1.json"
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
