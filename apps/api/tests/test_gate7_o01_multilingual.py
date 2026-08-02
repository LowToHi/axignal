from __future__ import annotations

import json

from axignal_api.gate7_o01_multilingual import (
    load_retained_records,
    measure_multilingual_journeys,
)


def multilingual_record() -> dict[str, object]:
    return {
        "publication-number": "000001-2026",
        "notice-title": {
            "deu": ["Öffentliche Softwaredienste"],
            "eng": ["Public software services"],
            "spa": ["Servicios públicos de software"],
            "fra": ["Services logiciels publics"],
            "ita": ["Servizi software pubblici"],
            "por": ["Serviços públicos de software"],
        },
        "buyer-name": {"eng": ["Example public authority"]},
    }


def test_all_required_language_journeys_pass_without_persisting_text() -> None:
    report = measure_multilingual_journeys(
        [multilingual_record()],
        required_languages=["de", "en", "es", "fr", "it", "pt"],
    )

    assert report["status"] == "PASS"
    assert report["all_languages_complete"] is True
    for journey in report["journeys"].values():
        assert journey["ingestion"] == "PASS"
        assert journey["normalisation"] == "PASS"
        assert journey["search"] == "PASS"
        assert journey["presentation"] == "PASS"
        assert journey["raw_text_persisted"] is False
        assert journey["presentation_sample_sha256"].startswith("sha256:")


def test_retained_record_loader_accepts_ted_notice_envelope() -> None:
    payload = json.dumps({"notices": [multilingual_record()]}).encode()
    records = load_retained_records([payload])
    assert len(records) == 1
