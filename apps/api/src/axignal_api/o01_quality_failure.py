from __future__ import annotations

import json
import shutil
import ssl
from pathlib import Path
from typing import Any

from .o01_official_baseline import (
    PinnedHTTPSConnection,
    resolve_public_addresses,
    select_address,
    validate_official_url,
)
from .o01_quality_common import canonical_json_bytes, sha256_prefixed

_SAFE_SCALAR_KEYS = frozenset(
    {
        "code",
        "column",
        "detail",
        "errorcode",
        "field",
        "index",
        "line",
        "message",
        "position",
        "property",
        "reason",
        "status",
        "title",
        "type",
    }
)
_SAFE_CONTAINER_KEYS = frozenset(
    {
        "cause",
        "causes",
        "details",
        "errors",
        "invalidparams",
        "location",
        "violations",
    }
)
_MAX_DEPTH = 4
_MAX_ITEMS = 20
_MAX_TEXT_LENGTH = 512


def _safe_scalar(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:_MAX_TEXT_LENGTH]
    return None


def _sanitise_node(value: Any, *, depth: int) -> Any:
    if depth > _MAX_DEPTH:
        return None
    if isinstance(value, dict):
        retained: dict[str, Any] = {}
        for key, item in list(value.items())[:_MAX_ITEMS]:
            key_text = str(key)
            canonical_key = key_text.casefold().replace("_", "").replace("-", "")
            if canonical_key in _SAFE_SCALAR_KEYS:
                safe_value = _safe_scalar(item)
                if safe_value is not None:
                    retained[key_text] = safe_value
            elif canonical_key in _SAFE_CONTAINER_KEYS:
                nested = _sanitise_node(item, depth=depth + 1)
                if nested not in (None, {}, []):
                    retained[key_text] = nested
        return retained
    if isinstance(value, list):
        retained_items = [
            _sanitise_node(item, depth=depth + 1)
            for item in value[:_MAX_ITEMS]
        ]
        return [item for item in retained_items if item not in (None, {}, [])]
    return _safe_scalar(value)


def sanitise_ted_error_body(body: bytes) -> dict[str, Any]:
    """Retain only bounded, non-payload TED error metadata."""

    result: dict[str, Any] = {
        "response_bytes": len(body),
        "raw_response_retained": False,
    }
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        result.update(
            {
                "format": "NON_JSON",
                "diagnostic_fields_retained": False,
            }
        )
        return result
    sanitised = _sanitise_node(value, depth=0)
    result.update(
        {
            "format": "JSON",
            "details": sanitised if sanitised not in (None, {}, []) else {},
            "diagnostic_fields_retained": sanitised not in (None, {}, []),
        }
    )
    return result


def purge_ephemeral_directory(path: Path) -> bool:
    """Remove transient campaign plaintext and report whether it existed."""

    existed = path.exists()
    if existed:
        shutil.rmtree(path)
    return existed


def diagnose_frozen_first_request(plan_path: Path) -> dict[str, Any]:
    """Repeat page one once, retaining only redacted HTTP failure metadata."""

    from .o01_quality_http import request_payload

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    sampling = plan["sampling"]
    country = str(sampling["countries"][0])
    query = str(sampling["query_contract"]).format(country=country)
    fields = [str(item) for item in plan["fields"]["retained_raw_projection"]]
    payload = request_payload(
        query=query,
        fields=fields,
        page=1,
        plan=plan,
    )
    endpoint = str(plan["source"]["endpoint"])
    allowed_hosts = frozenset(str(item) for item in plan["source"]["allowed_hosts"])
    parsed = validate_official_url(endpoint, allowed_hosts=allowed_hosts)
    host = parsed.hostname or ""
    path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
    addresses = resolve_public_addresses(host, parsed.port or 443)
    selected_address = select_address(addresses)
    body = canonical_json_bytes(payload)
    maximum_bytes = int(sampling["maximum_response_bytes"])
    connection = PinnedHTTPSConnection(
        host=host,
        port=parsed.port or 443,
        selected_address=selected_address,
        timeout=float(sampling["request_timeout_seconds"]),
        context=ssl.create_default_context(),
    )
    try:
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
                "User-Agent": "AXIGNAL-O01-C-Diagnostic/1.0",
            },
        )
        response = connection.getresponse()
        response_body = response.read(maximum_bytes + 1)
        if len(response_body) > maximum_bytes:
            return {
                "diagnostic_network_requests": 1,
                "http_status": response.status,
                "response_exceeded_frozen_byte_limit": True,
                "raw_response_retained": False,
                "request_body_sha256": sha256_prefixed(body),
            }
        return {
            "diagnostic_network_requests": 1,
            "http_status": response.status,
            "content_type": response.getheader("Content-Type", ""),
            "request_body_sha256": sha256_prefixed(body),
            "response_body_sha256": sha256_prefixed(response_body),
            "diagnostic": sanitise_ted_error_body(response_body),
            "raw_response_retained": False,
            "country_stratum": country,
            "page": 1,
        }
    finally:
        connection.close()
