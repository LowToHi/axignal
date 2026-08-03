from axignal_api.axent_knowledge import knowledge_coverage


def test_knowledge_coverage_none() -> None:
    assert knowledge_coverage([]) == "NONE"


def test_knowledge_coverage_partial_for_single_hit() -> None:
    assert knowledge_coverage([{"rank": 0.8}]) == "PARTIAL"


def test_knowledge_coverage_partial_for_weak_hits() -> None:
    assert knowledge_coverage([{"rank": 0.01}, {"rank": 0.02}]) == "PARTIAL"


def test_knowledge_coverage_sufficient_for_multiple_strong_hits() -> None:
    assert knowledge_coverage([{"rank": 0.08}, {"rank": 0.06}]) == "SUFFICIENT"
