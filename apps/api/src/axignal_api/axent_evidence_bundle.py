"""AXENT evidence bundle, ranking and grounded response composer
(Mandato AXENT — secciones 7.4, 7.5, 7.6).

The composer only receives a structured bundle: query plan, matched
objects, claims, evidence, contradictions, source status, coverage,
ranking components, missing information, tenant context. The model never
gets free database access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class ScoreComponents:
    structured_match: float = 0.0
    semantic_relevance: float = 0.0
    sector_fit: float = 0.0
    geographic_fit: float = 0.0
    economic_fit: float = 0.0
    capability_fit: float = 0.0
    historical_similarity: float = 0.0
    requirement_fit: float = 0.0
    deadline_fit: float = 0.0
    source_quality: float = 0.0
    freshness: float = 0.0
    evidence_coverage: float = 0.0
    contradiction_penalty: float = 0.0
    missing_data_penalty: float = 0.0

    def total(self) -> float:
        return sum(
            (
                self.structured_match, self.semantic_relevance,
                self.sector_fit, self.geographic_fit, self.economic_fit,
                self.capability_fit, self.historical_similarity,
                self.requirement_fit, self.deadline_fit,
                self.source_quality, self.freshness, self.evidence_coverage,
            )
        ) - (self.contradiction_penalty + self.missing_data_penalty)

    def as_dict(self) -> dict[str, float]:
        return {
            "structured_match": self.structured_match,
            "semantic_relevance": self.semantic_relevance,
            "sector_fit": self.sector_fit,
            "geographic_fit": self.geographic_fit,
            "economic_fit": self.economic_fit,
            "capability_fit": self.capability_fit,
            "historical_similarity": self.historical_similarity,
            "requirement_fit": self.requirement_fit,
            "deadline_fit": self.deadline_fit,
            "source_quality": self.source_quality,
            "freshness": self.freshness,
            "evidence_coverage": self.evidence_coverage,
            "contradiction_penalty": self.contradiction_penalty,
            "missing_data_penalty": self.missing_data_penalty,
            "total": self.total(),
        }


@dataclass(frozen=True)
class RankedResult:
    rank: int
    object_ref: str
    object_type: str
    title: str
    score_components: ScoreComponents
    match_reasons: tuple[str, ...] = ()
    risk_factors: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    source_freshness: str = "unknown"

    def as_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "object_ref": self.object_ref,
            "object_type": self.object_type,
            "title": self.title,
            "score_components": self.score_components.as_dict(),
            "match_reasons": list(self.match_reasons),
            "risk_factors": list(self.risk_factors),
            "missing_information": list(self.missing_information),
            "source_freshness": self.source_freshness,
        }


@dataclass(frozen=True)
class EvidenceBundle:
    query_plan: dict[str, Any]
    matched_objects: tuple[dict[str, Any], ...] = ()
    structured_fields: dict[str, Any] = field(default_factory=dict)
    claims: tuple[dict[str, Any], ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    contradictions: tuple[dict[str, Any], ...] = ()
    source_status: tuple[dict[str, Any], ...] = ()
    coverage: str = "PARTIAL"
    freshness: str = "unknown"
    ranking: tuple[RankedResult, ...] = ()
    missing_information: tuple[str, ...] = ()
    tenant_context: dict[str, Any] = field(default_factory=dict)
    permitted_actions: tuple[str, ...] = ()
    built_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "query_plan": self.query_plan,
            "matched_objects": list(self.matched_objects),
            "structured_fields": self.structured_fields,
            "claims": list(self.claims),
            "evidence": list(self.evidence),
            "contradictions": list(self.contradictions),
            "source_status": list(self.source_status),
            "coverage": self.coverage,
            "freshness": self.freshness,
            "ranking": [r.as_dict() for r in self.ranking],
            "missing_information": list(self.missing_information),
            "tenant_context": self.tenant_context,
            "permitted_actions": list(self.permitted_actions),
            "built_at": self.built_at,
        }


class AxentRanker:
    """Explainable, reproducible ranking. The model is not the authority."""

    def rank(
        self,
        *,
        objects: list[dict[str, Any]],
        plan: dict[str, Any],
    ) -> list[RankedResult]:
        countries = set(plan.get("countries") or [])
        keywords = set(str(k).lower() for k in plan.get("keywords") or [])
        value_min = plan.get("value_min")
        value_max = plan.get("value_max")
        sectors = set(plan.get("sectors") or [])

        results: list[RankedResult] = []
        for obj in objects:
            payload = obj.get("payload") or {}
            title = str(payload.get("title") or obj.get("opportunity_ref") or "")
            description = str(payload.get("description") or "")
            country = str(payload.get("country") or "")
            sector = str(payload.get("sector") or "")
            value = payload.get("value")
            currency = str(payload.get("currency") or "EUR")

            components = ScoreComponents()

            match_reasons: list[str] = []

            if keywords:
                haystack = (title + " " + description).lower()
                hits = sum(1 for keyword in keywords if keyword in haystack)
                components = ScoreComponents(
                    structured_match=min(1.0, hits / max(len(keywords), 1)),
                    semantic_relevance=min(1.0, hits / max(len(keywords), 1) * 0.8),
                )
                if hits:
                    match_reasons.append(f"{hits}/{len(keywords)} keywords matched")

            if countries and country in countries:
                merged = {k: v for k, v in components.as_dict().items()
                          if k not in ("geographic_fit", "total")}
                components = ScoreComponents(geographic_fit=1.0, **merged)
                match_reasons.append(f"country {country}")

            if sectors and sector in sectors:
                merged = {k: v for k, v in components.as_dict().items()
                          if k not in ("sector_fit", "total")}
                components = ScoreComponents(sector_fit=1.0, **merged)
                match_reasons.append(f"sector {sector}")

            if value is not None:
                numeric = float(value)
                if value_min is not None and numeric >= value_min:
                    match_reasons.append(f"value >= {value_min}")
                if value_max is not None and numeric <= value_max:
                    match_reasons.append(f"value <= {value_max}")
                if currency == "EUR":
                    merged = {k: v for k, v in components.as_dict().items()
                              if k not in ("economic_fit", "total")}
                    components = ScoreComponents(economic_fit=1.0, **merged)

            results.append(
                RankedResult(
                    rank=0,
                    object_ref=str(obj.get("opportunity_ref") or ""),
                    object_type=str(obj.get("library_id") or "O01"),
                    title=title,
                    score_components=components,
                    match_reasons=tuple(match_reasons),
                    missing_information=(
                        () if value is not None else ("value unknown",)
                    ),
                    source_freshness=str(obj.get("produced_at") or "unknown"),
                )
            )

        results.sort(key=lambda r: r.score_components.total(), reverse=True)
        for rank, result in enumerate(results, start=1):
            results[rank - 1] = RankedResult(
                rank=rank,
                object_ref=result.object_ref,
                object_type=result.object_type,
                title=result.title,
                score_components=result.score_components,
                match_reasons=result.match_reasons,
                risk_factors=result.risk_factors,
                missing_information=result.missing_information,
                source_freshness=result.source_freshness,
            )
        return results


EPISTEMIC_MARKERS = (
    "SOURCE_FACT", "CANONICAL_CLAIM", "INFERENCE", "RECOMMENDATION",
    "UNKNOWN", "CONTRADICTION",
)


@dataclass(frozen=True)
class GroundedSegment:
    text: str
    epistemic_class: str
    citations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "epistemic_class": self.epistemic_class,
            "citations": list(self.citations),
        }


class GroundedResponseComposer:
    """Builds grounded responses from the bundle, never from model memory."""

    def compose(
        self,
        *,
        bundle: EvidenceBundle,
        user_query: str,
    ) -> dict[str, Any]:
        segments: list[GroundedSegment] = []

        ranked = bundle.ranking
        if not ranked:
            segments.append(
                GroundedSegment(
                    "No se ha identificado ninguna oportunidad que cumpla "
                    "los criterios con evidencia admitida.",
                    "UNKNOWN",
                )
            )
        else:
            for result in ranked[:5]:
                reasons = ", ".join(result.match_reasons) or "criterios del plan"
                segments.append(
                    GroundedSegment(
                        f"{result.title} ({result.object_ref}): coincide por "
                        f"{reasons}. Puntuación {result.score_components.total():.2f}.",
                        "SOURCE_FACT",
                        (result.object_ref,),
                    )
                )
            if bundle.contradictions:
                segments.append(
                    GroundedSegment(
                        "Existen contradicciones abiertas en el contexto "
                        "consultado; no se resuelven automáticamente.",
                        "CONTRADICTION",
                        tuple(c["contradiction_id"] for c in bundle.contradictions[:3]),
                    )
                )
            if bundle.missing_information:
                segments.append(
                    GroundedSegment(
                        "Información ausente: " + ", ".join(bundle.missing_information[:5]),
                        "UNKNOWN",
                    )
                )

        if "exclu" in user_query.lower() or bundle.query_plan.get("exclusions"):
            segments.append(
                GroundedSegment(
                    "Los criterios de exclusión se aplicaron a la recuperación "
                    "estructurada.",
                    "INFERENCE",
                )
            )

        if "recomend" in user_query.lower():
            segments.append(
                GroundedSegment(
                    "Recomendación: revisar la evidencia de las oportunidades "
                    "mejor puntuadas antes de cualificar.",
                    "RECOMMENDATION",
                )
            )

        segments.append(
            GroundedSegment(
                "AXIGNAL proporciona información, análisis y acompañamiento "
                "operativo. No sustituye los portales oficiales ni ejecuta "
                "actuaciones del procedimiento. La verificación y actuación "
                "oficial corresponden al usuario.",
                "UNKNOWN",
            )
        )

        return {
            "segments": [s.as_dict() for s in segments],
            "bundle": bundle.as_dict(),
            "model_outage_degraded": False,
        }
