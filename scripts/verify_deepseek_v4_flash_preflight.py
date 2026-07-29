from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx

BASE_URL = "https://api.deepseek.com"
MODEL = "deepseek-v4-flash"
OUTPUT = Path("deepseek-v4-flash-preflight-evidence.json")


class PreflightError(RuntimeError):
    pass


def require_secret() -> str:
    value = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not value:
        raise PreflightError("DEEPSEEK_API_KEY is not configured")
    return value


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
        if models_response.status_code != 200:
            raise PreflightError(
                f"DeepSeek model-list preflight failed with status {models_response.status_code}"
            )
        try:
            models_body = models_response.json()
            model_ids = {
                str(item["id"])
                for item in models_body["data"]
                if isinstance(item, dict) and "id" in item
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise PreflightError("DeepSeek model-list response was malformed") from exc
        if MODEL not in model_ids:
            raise PreflightError("deepseek-v4-flash is not available to this credential")

        chat_response = client.post(
            "/chat/completions",
            json={
                "model": MODEL,
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
                f"DeepSeek chat preflight failed with status {chat_response.status_code}"
            )
        try:
            chat_body = chat_response.json()
            content = chat_body["choices"][0]["message"]["content"]
            decoded = json.loads(content)
            usage = chat_body.get("usage") or {}
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise PreflightError("DeepSeek chat response was malformed") from exc
        if decoded != {"status": "ok"}:
            raise PreflightError("DeepSeek chat preflight returned an unexpected JSON contract")

    evidence = {
        "provider": "deepseek",
        "transport": "direct",
        "base_url_host": "api.deepseek.com",
        "model": MODEL,
        "credential_configured": True,
        "model_listed": True,
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
