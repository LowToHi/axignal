# ruff: noqa: F401,F403,F405
from __future__ import annotations
from .o01_quality_common import *
from .o01_quality_reports import *

def reference_contact_classification(field: str, value: str, contact_point: str | None) -> tuple[str, str]:
    lower = value.casefold().strip()
    if field in {"buyer-internet-address", "buyer-profile", "submission-url-lot"}:
        return "INSTITUTIONAL", "BUYER_PROFILE"
    if field == "buyer-email":
        local = lower.split("@", 1)[0] if "@" in lower else lower
        functional_markers = (
            "info",
            "contact",
            "procurement",
            "tender",
            "public",
            "office",
            "service",
            "achats",
            "marches",
            "compras",
            "contratacion",
            "gare",
            "appalti",
            "vergabe",
        )
        if any(marker in local for marker in functional_markers):
            return "FUNCTIONAL_NON_PERSONAL", "FUNCTIONAL_EMAIL"
        if contact_point and len(contact_point.split()) >= 2:
            return "PROFESSIONAL_PERSONAL", "NAMED_PROFESSIONAL_EMAIL"
        return "AMBIGUOUS_PERSONAL", "SOURCE_LINK_ONLY"
    if field == "buyer-tel":
        if contact_point and len(contact_point.split()) >= 2:
            return "PROFESSIONAL_PERSONAL", "NAMED_PROFESSIONAL_PHONE"
        return "FUNCTIONAL_NON_PERSONAL", "OFFICIAL_PHONE"
    if field == "buyer-contact-point":
        organisation_markers = (
            "department",
            "service",
            "unit",
            "office",
            "procurement",
            "achats",
            "marches",
            "contratacion",
            "vergabe",
            "appalti",
        )
        if any(marker in lower for marker in organisation_markers):
            return "FUNCTIONAL_NON_PERSONAL", "SOURCE_LINK_ONLY"
        return "AMBIGUOUS_PERSONAL", "SOURCE_LINK_ONLY"
    return "BLOCKED", "SOURCE_LINK_ONLY"


def contact_classification_report(contact_records: list[dict[str, Any]]) -> dict[str, Any]:
    expected_policy = {
        ("INSTITUTIONAL", "BUYER_PROFILE"): "ALLOW",
        ("FUNCTIONAL_NON_PERSONAL", "FUNCTIONAL_EMAIL"): "ALLOW",
        ("FUNCTIONAL_NON_PERSONAL", "OFFICIAL_PHONE"): "ALLOW",
        ("PROFESSIONAL_PERSONAL", "NAMED_PROFESSIONAL_EMAIL"): "CONTEXTUAL",
        ("PROFESSIONAL_PERSONAL", "NAMED_PROFESSIONAL_PHONE"): "CONTEXTUAL",
        ("AMBIGUOUS_PERSONAL", "SOURCE_LINK_ONLY"): "LINK_ONLY",
        ("BLOCKED", "SOURCE_LINK_ONLY"): "BLOCK",
    }
    assessed = 0
    conformant = 0
    class_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    fields = (
        "buyer-internet-address",
        "buyer-profile",
        "submission-url-lot",
        "buyer-email",
        "buyer-tel",
    )
    for record in contact_records:
        contact_point_values = values(record, "buyer-contact-point")
        contact_point = contact_point_values[0] if contact_point_values else None
        for field in fields:
            for item in values(record, field):
                assessed += 1
                data_class, channel_type = reference_contact_classification(
                    field, item, contact_point
                )
                decision = expected_policy.get((data_class, channel_type))
                class_counts[data_class] += 1
                if decision:
                    conformant += 1
                    decision_counts[decision] += 1
                else:
                    decision_counts["UNMAPPED"] += 1
    result = ratio(conformant, assessed)
    result.update(
        {
            "classification_count": assessed,
            "class_counts": dict(sorted(class_counts.items())),
            "policy_decision_counts": dict(sorted(decision_counts.items())),
            "raw_contact_values_persisted": False,
        }
    )
    return result


