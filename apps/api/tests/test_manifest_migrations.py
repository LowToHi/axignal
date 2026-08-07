"""WP2-T11 — manifest schema migration strategy tests."""

from __future__ import annotations

import pytest

from axignal_api.manifest_migrations import (
    DEFAULT_MIGRATION_REGISTRY,
    ManifestMigration,
    ManifestMigrationRegistry,
)
from axignal_api.manifest_state_machine import VersioningError


class TestManifestMigrationContract:
    def test_migration_requires_forward_version(self) -> None:
        with pytest.raises(VersioningError):
            ManifestMigration(
                from_version="1.1.0",
                to_version="1.0.0",
                kind="minor",
                description="backwards",
                apply=lambda m: m,
            )

    def test_migration_requires_strict_forward(self) -> None:
        with pytest.raises(VersioningError):
            ManifestMigration(
                from_version="1.0.0",
                to_version="1.0.0",
                kind="patch",
                description="same",
                apply=lambda m: m,
            )

    def test_library_migration_is_additive(self) -> None:
        result = DEFAULT_MIGRATION_REGISTRY.migrate(
            "library",
            {"schema_version": "1.0.0", "library_id": "O01"},
        )
        assert result["schema_version"] == "1.1.0"
        assert result["source_manifests"] == []
        assert result["coverage"] == {}
        # Additive-only: existing fields untouched.
        assert result["library_id"] == "O01"

    def test_source_migration_is_additive(self) -> None:
        result = DEFAULT_MIGRATION_REGISTRY.migrate(
            "source",
            {"schema_version": "1.0.0", "source_id": "src_x"},
        )
        assert result["schema_version"] == "1.1.0"
        assert result["outage_profile"] == {}

    def test_migration_is_idempotent(self) -> None:
        once = DEFAULT_MIGRATION_REGISTRY.migrate(
            "source", {"schema_version": "1.0.0", "source_id": "src_x"}
        )
        twice = DEFAULT_MIGRATION_REGISTRY.migrate("source", once)
        assert once == twice

    def test_unknown_kind_returns_unchanged(self) -> None:
        manifest = {"schema_version": "1.0.0", "x": 1}
        assert DEFAULT_MIGRATION_REGISTRY.migrate("workspace", manifest) == manifest

    def test_already_migrated_is_noop(self) -> None:
        manifest = {"schema_version": "1.1.0", "source_id": "src_x"}
        assert DEFAULT_MIGRATION_REGISTRY.migrate("source", manifest) == manifest

    def test_never_overwrites_existing_values(self) -> None:
        manifest = {
            "schema_version": "1.0.0",
            "source_id": "src_x",
            "outage_profile": {"retry_max_attempts": 5},
        }
        result = DEFAULT_MIGRATION_REGISTRY.migrate("source", manifest)
        assert result["outage_profile"] == {"retry_max_attempts": 5}

    def test_registry_orders_migrations(self) -> None:
        registry = ManifestMigrationRegistry()
        registry.register(
            "x",
            ManifestMigration("1.0.0", "1.1.0", "minor", "a", lambda m: m),
        )
        registry.register(
            "x",
            ManifestMigration("0.9.0", "1.0.0", "minor", "b", lambda m: m),
        )
        versions = [m.from_version for m in registry.migrations_for("x")]
        assert versions == ["0.9.0", "1.0.0"]

    def test_chained_migrations(self) -> None:
        registry = ManifestMigrationRegistry()
        registry.register(
            "y",
            ManifestMigration(
                "1.0.0", "1.1.0", "minor", "a",
                lambda m: {**m, "a": 1},
            ),
        )
        registry.register(
            "y",
            ManifestMigration(
                "1.1.0", "1.2.0", "minor", "b",
                lambda m: {**m, "b": 2},
            ),
        )
        result = registry.migrate("y", {"schema_version": "1.0.0"})
        assert result == {"schema_version": "1.2.0", "a": 1, "b": 2}

    def test_can_migrate(self) -> None:
        assert DEFAULT_MIGRATION_REGISTRY.can_migrate("source", "1.0.0")
        assert not DEFAULT_MIGRATION_REGISTRY.can_migrate("source", "1.1.0")
        assert not DEFAULT_MIGRATION_REGISTRY.can_migrate("workspace", "1.0.0")

    def test_no_destructive_operations_in_default_registry(self) -> None:
        # Additive-only: default migrations must never delete a key.
        for kind in ("library", "source"):
            for migration in DEFAULT_MIGRATION_REGISTRY.migrations_for(kind):
                original = {"schema_version": "1.0.0", "keep_me": "value"}
                result = migration.apply(dict(original))
                assert "keep_me" in result
