from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

BASE_URL = "https://api.deepseek.com"
API_MODEL = "deepseek-v4-flash"
PROVIDER_CHECKPOINT = "deepseek-v4-flash-0731"
OUTPUT = Path("deepseek-v4-flash-0731-preflight-evidence.json")


class PreflightError(RuntimeError):
    pass


def require_secret() -> str:
    value = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not value:
        raise PreflightError("DEEPSEEK_API_KEY is not configured")
    return value


def read_model_listing(response: httpx.Response) -> tuple[bool, int]:
    if response.status_code != 200:
        return False, response.status_code
    try:
        models_body = response.json()
        model_ids = {
            str(item["id"])
            for item in models_body["data"]
            if isinstance(item, dict) and "id" in item
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise PreflightError("DeepSeek model-list response was malformed") from exc
    return API_MODEL in model_ids, response.status_code


def safe_provider_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return f"status={response.status_code}; non_json_error_body"
    if not isinstance(body, dict):
        return f"status={response.status_code}; malformed_error_body"
    error = body.get("error")
    if not isinstance(error, dict):
        return f"status={response.status_code}; missing_error_object"
    safe_fields = []
    for key in ("type", "code", "message"):
        value = error.get(key)
        if value is None:
            continue
        normalised = " ".join(str(value).split())[:240]
        safe_fields.append(f"{key}={normalised}")
    detail = "; ".join(safe_fields) or "empty_error_object"
    return f"status={response.status_code}; {detail}"


def main() -> int:
    api_key = require_secret()
    parsed = urlparse(BASE_URL)
    if parsed.scheme != "https" or parsed.hostname != "api.deepseek.com":
        raise PreflightError("DeepSeek endpoint is not the official HTTPS API host")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "AXIGNAL/0.1 credential-preflight",
    }
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=45.0) as client:
        models_response = client.get("/models")
        model_listed, model_list_status = read_model_listing(models_response)

        chat_response = client.post(
            "/chat/completions",
            json={
                "model": API_MODEL,
                "temperature": 0,
                "max_tokens": 32,
                "thinking": {"type": "disabled"},
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "Return JSON only. Do not call tools.",
                    },
                    {
                        "role": "user",
                        "content": (
                            'Return exactly one JSON object with key "status" '
                            'and string value "ok".'
                        ),
                    },
                ],
            },
        )
        if chat_response.status_code != 200:
            raise PreflightError(
                f"DeepSeek chat preflight failed: {safe_provider_error(chat_response)}"
            )
        try:
            chat_body = chat_response.json()
            content = chat_body["choices"][0]["message"]["content"]
            decoded = json.loads(content)
            usage = chat_body.get("usage") or {}
            returned_model = chat_body.get("model")
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise PreflightError("DeepSeek chat response was malformed") from exc
        if decoded != {"status": "ok"}:
            raise PreflightError("DeepSeek chat preflight returned an unexpected JSON contract")
        if returned_model is not None and returned_model not in {
            API_MODEL,
            PROVIDER_CHECKPOINT,
        }:
            raise PreflightError("DeepSeek response reported an unexpected model identity")

    evidence = {
        "provider": "deepseek",
        "transport": "direct",
        "base_url_host": "api.deepseek.com",
        "api_model_requested": API_MODEL,
        "api_model_returned": returned_model,
        "provider_checkpoint": PROVIDER_CHECKPOINT,
        "checkpoint_binding": "PROVIDER_MANAGED_ALIAS_USER_SUPPLIED_NOTICE",
        "checkpoint_exposed_by_api": returned_model == PROVIDER_CHECKPOINT,
        "credential_configured": True,
        "model_list_status": model_list_status,
        "api_model_listed": model_listed,
        "direct_chat_execution": True,
        "chat_completion_json_contract": True,
        "thinking": "disabled",
        "max_output_tokens": 32,
        "input_contains_project_data": False,
        "response_content_persisted": False,
        "secret_value_logged": False,
        "total_tokens": usage.get("total_tokens"),
    }
    OUTPUT.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PreflightError as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(1) from exc
