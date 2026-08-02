from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_PATH = ROOT / "scripts/materialize_gate7_o01_official_baseline.py"
DEFAULT_OUTPUT_DIR = ROOT / "artifacts/o01-official-baseline/current"
FALLBACK_DOCUMENT_ID = "commission-decision-2011-833-eu"
FALLBACK_URL = "https://eur-lex.europa.eu/eli/dec/2011/833/oj/eng"
TRANSIENT_MARKER = "returned HTTP 202"


def load_original() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "axignal_o01_official_baseline_materializer",
        ORIGINAL_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the O01 official baseline materializer")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def fallback_contract(original: ModuleType, directory: Path) -> Path:
    contract = original.load_json(original.CONTRACT_PATH)
    matches = [
        item
        for item in contract["official_documents"]
        if item.get("document_id") == FALLBACK_DOCUMENT_ID
    ]
    if len(matches) != 1:
        raise RuntimeError("Expected exactly one EUR-Lex decision contract")
    primary_url = str(matches[0]["url"])
    if primary_url == FALLBACK_URL:
        raise RuntimeError("Fallback URL must differ from the contractual primary URL")
    matches[0]["url"] = FALLBACK_URL
    path = directory / "official-baseline-contract-fallback.v0.1.json"
    path.write_text(
        json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def clear_output(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def materialize_resilient(
    *,
    output_dir: Path,
    previous_baseline_path: Path | None,
    now: datetime,
) -> tuple[dict[str, Any], dict[str, Any]]:
    original = load_original()
    clear_output(output_dir)
    try:
        result = original.materialize(
            output_dir=output_dir,
            previous_baseline_path=previous_baseline_path,
            now=now,
        )
        return result, {
            "fallback_used": False,
            "primary_contract_path": str(original.CONTRACT_PATH.relative_to(ROOT)),
        }
    except original.BaselineError as exc:
        if TRANSIENT_MARKER not in str(exc):
            raise
        primary_error = str(exc)

    clear_output(output_dir)
    with tempfile.TemporaryDirectory(prefix="axignal-o01-eli-fallback-") as temporary:
        fallback_path = fallback_contract(original, Path(temporary))
        primary_contract_path = original.CONTRACT_PATH
        original.CONTRACT_PATH = fallback_path
        try:
            result = original.materialize(
                output_dir=output_dir,
                previous_baseline_path=previous_baseline_path,
                now=now,
            )
        finally:
            original.CONTRACT_PATH = primary_contract_path

    audit = {
        "schema_version": "axignal.o01-official-preflight-fallback/v0.1",
        "fallback_used": True,
        "trigger": "PRIMARY_REPRESENTATION_HTTP_202_AFTER_BOUNDED_RETRIES",
        "primary_error": primary_error,
        "document_id": FALLBACK_DOCUMENT_ID,
        "primary_url": next(
            item["url"]
            for item in original.load_json(primary_contract_path)["official_documents"]
            if item["document_id"] == FALLBACK_DOCUMENT_ID
        ),
        "fallback_url": FALLBACK_URL,
        "fallback_host_authority": "EUR_LEX_OFFICIAL",
        "terms_change_class": result["terms_change_class"],
        "content_change_is_not_suppressed": True,
    }
    (output_dir / "official-preflight-fallback.v0.1.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result, audit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--previous-baseline", type=Path)
    parser.add_argument("--now")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    now = (
        datetime.fromisoformat(args.now.replace("Z", "+00:00"))
        if args.now
        else datetime.now(UTC)
    )
    try:
        result, audit = materialize_resilient(
            output_dir=args.output_dir,
            previous_baseline_path=args.previous_baseline,
            now=now,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps({**result, "preflight_fallback": audit}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
