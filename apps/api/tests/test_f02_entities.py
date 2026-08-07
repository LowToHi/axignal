"""WP3-T02 — F02 Entities & Ownership tests."""

from __future__ import annotations

from datetime import date

import pytest

from axignal_api.foundations.f02_entities import (
    Entity,
    EntityFact,
    EntityIdentifier,
    EntityName,
    EntityRegistry,
    resolve_entity,
)


def buyer_entity() -> Entity:
    return Entity(
        entity_id="ent_ministerio_fomento_es",
        entity_type="PUBLIC_BODY",
        names=[
            EntityName(name="Ministerio de Fomento", language="es"),
            EntityName(name="Ministry of Public Works", language="en"),
        ],
        identifiers=[
            EntityIdentifier(scheme="es-registry", value="S2800135B", source_id="src_es_boe"),
        ],
        facts=[
            EntityFact(
                fact_type="registered_name",
                value="Ministerio de Fomento",
                provenance="OBSERVED",
                source_id="src_es_boe",
                observed_at=date(2026, 1, 1),
            ),
            EntityFact(
                fact_type="sector",
                value="infrastructure",
                provenance="INFERRED",
                evidence_ref="evidence-1",
            ),
        ],
    )


class TestEntityModel:
    def test_requires_name_or_identifier(self) -> None:
        with pytest.raises(ValueError, match="name or identifier"):
            Entity(entity_id="ent_empty_0001", entity_type="COMPANY")

    def test_person_must_be_tenant_private(self) -> None:
        with pytest.raises(ValueError, match="tenant-private"):
            Entity(
                entity_id="ent_person_0001",
                entity_type="PERSON",
                names=[EntityName(name="A Person")],
            )

    def test_person_tenant_private_ok(self) -> None:
        entity = Entity(
            entity_id="ent_person_0001",
            entity_type="PERSON",
            names=[EntityName(name="A Person")],
            tenant_id="tenant-a",
            is_tenant_private=True,
        )
        assert entity.is_tenant_private

    def test_observed_fact_requires_source(self) -> None:
        with pytest.raises(ValueError, match="source_id"):
            EntityFact(
                fact_type="x",
                value="y",
                provenance="OBSERVED",
            )

    def test_inferred_fact_requires_evidence(self) -> None:
        with pytest.raises(ValueError, match="evidence_ref"):
            EntityFact(
                fact_type="x",
                value="y",
                provenance="INFERRED",
            )

    def test_observed_inferred_separation(self) -> None:
        entity = buyer_entity()
        assert len(entity.observed_facts()) == 1
        assert len(entity.inferred_facts()) == 1
        assert entity.observed_facts()[0].fact_type == "registered_name"
        assert entity.inferred_facts()[0].fact_type == "sector"

    def test_canonical_name_skips_historical(self) -> None:
        entity = Entity(
            entity_id="ent_test_0001",
            entity_type="COMPANY",
            names=[
                EntityName(name="Old Name", is_historical=True),
                EntityName(name="New Name"),
            ],
        )
        assert entity.canonical_name() == "New Name"

    def test_native_identifiers_retained(self) -> None:
        entity = buyer_entity()
        assert entity.identifiers[0].scheme == "es-registry"
        assert entity.identifiers[0].value == "S2800135B"


class TestResolution:
    def test_fingerprint_reproducible(self) -> None:
        first = buyer_entity()
        second = buyer_entity()
        assert first.resolve_fingerprint() == second.resolve_fingerprint()

    def test_fingerprint_deterministic(self) -> None:
        entity = buyer_entity()
        assert resolve_entity(entity).resolution_fingerprint == entity.resolve_fingerprint()

    def test_no_silent_merge_different_identifiers(self) -> None:
        a = buyer_entity()
        b = buyer_entity().model_copy(
            update={
                "entity_id": "ent_otra_entidad_01",
                "identifiers": [
                    EntityIdentifier(scheme="es-registry", value="A28015865")
                ],
            }
        )
        assert a.resolve_fingerprint() != b.resolve_fingerprint()

    def test_fingerprint_stable_across_name_changes(self) -> None:
        a = buyer_entity()
        renamed = buyer_entity().model_copy(
            update={
                "names": [EntityName(name="Ministerio de Transportes", language="es")],
            }
        )
        # Resolution is keyed on native identifiers, not display names.
        assert a.resolve_fingerprint() == renamed.resolve_fingerprint()

    def test_temporal_ownership(self) -> None:
        parent = Entity(
            entity_id="ent_parent_0001",
            entity_type="COMPANY",
            names=[EntityName(name="Parent Co")],
        )
        child = Entity(
            entity_id="ent_child_0001",
            entity_type="COMPANY",
            names=[EntityName(name="Child Co")],
            parent_entity_id=parent.entity_id,
            control_observed_at=date(2025, 6, 1),
        )
        assert child.parent_entity_id == "ent_parent_0001"
        assert child.control_observed_at == date(2025, 6, 1)


class TestEntityRegistry:
    def test_register_and_get(self) -> None:
        registry = EntityRegistry()
        registry.register(buyer_entity())
        assert len(registry) == 1
        assert registry.get("ent_ministerio_fomento_es") is not None

    def test_tenant_private_isolation(self) -> None:
        registry = EntityRegistry()
        registry.register(
            Entity(
                entity_id="ent_private_0001",
                entity_type="COMPANY",
                names=[EntityName(name="Private Co")],
                tenant_id="tenant-a",
                is_tenant_private=True,
            )
        )
        assert registry.get_for_tenant("ent_private_0001", "tenant-a") is not None
        assert registry.get_for_tenant("ent_private_0001", "tenant-b") is None

    def test_shared_entity_visible_to_all_tenants(self) -> None:
        registry = EntityRegistry()
        registry.register(buyer_entity())
        assert registry.get_for_tenant("ent_ministerio_fomento_es", "tenant-a") is not None
        assert registry.get_for_tenant("ent_ministerio_fomento_es", "tenant-b") is not None
