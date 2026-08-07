"""F02 — Entities, Organisations and Ownership (WP3-T02).

Canonical entity model per contract F02:

- public bodies, buyers and suppliers, companies, universities and
  research centres, funds and agencies; persons only with legal basis
  and minimisation;
- native identifiers retained (no re-keying);
- historical names and aliases;
- parent/subsidiary/control relations;
- temporal observed ownership;
- strict separation between OBSERVED and INFERRED facts;
- entity resolution reproducible (deterministic fingerprint), no silent
  merge; tenant-private entities isolated from shared registry.

Gate: reproducible resolution + no silent merge + native identifiers +
temporal ownership + tenant-private isolation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class EntityName(BaseModel):
    """A name with history and language."""

    name: str = Field(min_length=1, max_length=300)
    language: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    is_historical: bool = False


class EntityIdentifier(BaseModel):
    """A native identifier retained from its source."""

    scheme: str = Field(min_length=2, max_length=50)
    value: str = Field(min_length=1, max_length=200)
    source_id: str | None = None
    observed_at: date | None = None


class EntityFact(BaseModel):
    """A single entity fact with provenance class."""

    fact_type: str
    value: str
    provenance: Literal["OBSERVED", "INFERRED"]
    source_id: str | None = None
    observed_at: date | None = None
    evidence_ref: str | None = None

    @model_validator(mode="after")
    def validate_provenance_rules(self) -> EntityFact:
        if self.provenance == "OBSERVED" and not self.source_id:
            raise ValueError("OBSERVED facts require source_id")
        if self.provenance == "INFERRED" and not self.evidence_ref:
            raise ValueError("INFERRED facts require evidence_ref")
        return self


class Entity(BaseModel):
    """A canonical entity with temporal identity and ownership."""

    schema_version: Literal["axignal.f02.entity.v1"] = "axignal.f02.entity.v1"
    entity_id: str = Field(pattern=r"^ent_[A-Za-z0-9_-]{8,}$")
    entity_type: Literal[
        "PUBLIC_BODY",
        "BUYER",
        "SUPPLIER",
        "COMPANY",
        "UNIVERSITY_RESEARCH",
        "FUND_AGENCY",
        "PERSON",
    ]
    names: list[EntityName] = Field(default_factory=list)
    identifiers: list[EntityIdentifier] = Field(default_factory=list)
    facts: list[EntityFact] = Field(default_factory=list)
    parent_entity_id: str | None = None
    control_observed_at: date | None = None
    tenant_id: str | None = None
    is_tenant_private: bool = False
    resolution_fingerprint: str | None = None

    @model_validator(mode="after")
    def validate_entity_rules(self) -> Entity:
        if not self.names and not self.identifiers:
            raise ValueError("entity requires at least one name or identifier")
        if self.entity_type == "PERSON" and not self.is_tenant_private:
            raise ValueError("PERSON entities must be tenant-private")
        return self

    def canonical_name(self) -> str | None:
        active = [n for n in self.names if not n.is_historical]
        if active:
            return active[0].name
        return self.names[0].name if self.names else None

    def resolve_fingerprint(self) -> str:
        """Deterministic, reproducible resolution fingerprint."""
        native = sorted(
            f"{i.scheme}:{i.value}" for i in self.identifiers
        )
        payload = {
            "entity_type": self.entity_type,
            "native_identifiers": native,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return f"fp:{hashlib.sha256(encoded).hexdigest()}"

    def observed_facts(self) -> list[EntityFact]:
        return [f for f in self.facts if f.provenance == "OBSERVED"]

    def inferred_facts(self) -> list[EntityFact]:
        return [f for f in self.facts if f.provenance == "INFERRED"]


def resolve_entity(entity: Entity) -> Entity:
    """Resolve and stamp the reproducible fingerprint (no silent merge)."""
    return entity.model_copy(update={"resolution_fingerprint": entity.resolve_fingerprint()})


class EntityRegistry:
    """Shared + tenant-private entity registry with isolation."""

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}

    def register(self, entity: Entity) -> None:
        resolved = resolve_entity(entity)
        self._entities[resolved.entity_id] = resolved

    def get(self, entity_id: str) -> Entity | None:
        return self._entities.get(entity_id)

    def get_for_tenant(self, entity_id: str, tenant_id: str) -> Entity | None:
        entity = self._entities.get(entity_id)
        if entity is None:
            return None
        if entity.is_tenant_private and entity.tenant_id != tenant_id:
            return None
        return entity

    def all(self) -> tuple[Entity, ...]:
        return tuple(sorted(self._entities.values(), key=lambda e: e.entity_id))

    def __len__(self) -> int:
        return len(self._entities)
