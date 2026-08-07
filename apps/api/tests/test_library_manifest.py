"""WP2-T01 — LibraryManifest base contract tests."""

from __future__ import annotations

import pytest

from axignal_api.library_manifest import (
    ALL_LIBRARIES,
    CANONICAL_SHELLS,
    FOUNDATIONAL_LIBRARIES,
    OPPORTUNITY_LIBRARIES,
    PRIMARY_SHELL,
    SECOND_SHELL,
    LibraryManifest,
    LibraryStatus,
    LibraryType,
    canonical_library_manifests,
)


class TestLibraryManifestContract:
    def test_canonical_manifests_cover_exactly_16_libraries(self) -> None:
        manifests = canonical_library_manifests()
        assert [m.library_id for m in manifests] == list(ALL_LIBRARIES)
        assert len(manifests) == 16
        assert all(m.is_shell is False for m in manifests)
        assert all(m.is_root_product is False for m in manifests)

    def test_foundational_libraries_available_to_both_shells(self) -> None:
        manifests = canonical_library_manifests()
        foundational = [m for m in manifests if m.library_type == LibraryType.FOUNDATIONAL]
        assert [m.library_id for m in foundational] == list(FOUNDATIONAL_LIBRARIES)
        for manifest in foundational:
            assert manifest.product_shell_ids == [PRIMARY_SHELL, SECOND_SHELL]
            assert manifest.workspace is None

    def test_opportunity_libraries_belong_to_primary_shell(self) -> None:
        manifests = canonical_library_manifests()
        opportunity = [m for m in manifests if m.library_type == LibraryType.OPPORTUNITY]
        assert [m.library_id for m in opportunity] == list(OPPORTUNITY_LIBRARIES)
        for manifest in opportunity:
            assert manifest.product_shell_ids == [PRIMARY_SHELL]
            assert manifest.workspace == {
                "O01": "BID_WORKSPACE",
                "O02": "GRANTS_WORKSPACE",
                "O03": "REGULATION_WORKSPACE",
                "O04": "INFRASTRUCTURE_WORKSPACE",
                "O05": "CORPORATE_WORKSPACE",
                "O06": "SOVEREIGN_WORKSPACE",
                "O07": "TRADE_WORKSPACE",
                "O08": "ENERGY_CLIMATE_WORKSPACE",
                "O09": "INNOVATION_IP_WORKSPACE",
            }[manifest.library_id]

    def test_o01_is_a_library_not_a_shell(self) -> None:
        o01 = LibraryManifest(
            library_id="O01",
            name="Global Public Procurement",
            library_type=LibraryType.OPPORTUNITY,
            manifest_version="1.0.0",
            workspace="BID_WORKSPACE",
            product_shell_ids=[PRIMARY_SHELL],
        )
        assert o01.is_shell is False
        assert o01.is_root_product is False

    def test_public_employment_is_not_o10(self) -> None:
        with pytest.raises(ValueError, match="O10"):
            LibraryManifest(
                library_id="O10",
                name="Public Employment",
                library_type=LibraryType.OPPORTUNITY,
                manifest_version="1.0.0",
                workspace="CANDIDACY_WORKSPACE",
                product_shell_ids=[PRIMARY_SHELL],
            )

    def test_rejects_unknown_library_id(self) -> None:
        with pytest.raises(ValueError, match="library_id must be one of"):
            LibraryManifest(
                library_id="O42",
                name="Unknown",
                library_type=LibraryType.OPPORTUNITY,
                manifest_version="1.0.0",
                workspace="BID_WORKSPACE",
                product_shell_ids=[PRIMARY_SHELL],
            )

    def test_rejects_procurement_as_shell(self) -> None:
        # "PROC" violates the ^[FO]\d{2}$ pattern at pydantic level, which is
        # exactly the required behaviour: Procurement is not a library id.
        with pytest.raises(ValueError, match="library_id"):
            LibraryManifest(
                library_id="PROC",
                name="Procurement Shell",
                library_type=LibraryType.OPPORTUNITY,
                manifest_version="1.0.0",
                workspace="BID_WORKSPACE",
                product_shell_ids=[PRIMARY_SHELL],
            )

    def test_rejects_wrong_workspace_for_library(self) -> None:
        with pytest.raises(ValueError, match="workspace for O02"):
            LibraryManifest(
                library_id="O02",
                name="Grants",
                library_type=LibraryType.OPPORTUNITY,
                manifest_version="1.0.0",
                workspace="BID_WORKSPACE",
                product_shell_ids=[PRIMARY_SHELL],
            )

    def test_rejects_unknown_shell_placement(self) -> None:
        # Rejected either by the both-shells rule (foundational) or the
        # unknown-shell rule; the contract only requires rejection.
        with pytest.raises(ValueError, match="both shells|unknown shell"):
            LibraryManifest(
                library_id="F01",
                name="Jurisdictions",
                library_type=LibraryType.FOUNDATIONAL,
                manifest_version="1.0.0",
                product_shell_ids=["AXIGNAL_PROCUREMENT"],
            )

    def test_rejects_foundational_library_with_workspace(self) -> None:
        with pytest.raises(ValueError, match="must not declare a workspace"):
            LibraryManifest(
                library_id="F01",
                name="Jurisdictions",
                library_type=LibraryType.FOUNDATIONAL,
                manifest_version="1.0.0",
                workspace="BID_WORKSPACE",
                product_shell_ids=[PRIMARY_SHELL, SECOND_SHELL],
            )

    def test_rejects_opportunity_library_in_second_shell_only(self) -> None:
        with pytest.raises(ValueError, match=PRIMARY_SHELL):
            LibraryManifest(
                library_id="O01",
                name="Procurement",
                library_type=LibraryType.OPPORTUNITY,
                manifest_version="1.0.0",
                workspace="BID_WORKSPACE",
                product_shell_ids=[SECOND_SHELL],
            )

    def test_status_vocabulary_is_authorized(self) -> None:
        allowed = {s.value for s in LibraryStatus}
        assert allowed == {
            "NOT_STARTED",
            "ENGINEERING_IN_PROGRESS",
            "ENGINEERING_EVIDENCE_READY",
            "ENGINEERING_E2E_PASS",
            "ENGINEERING_REJECTED",
            "SUPERSEDED",
        }

    def test_canonical_shell_ids_are_exact_two(self) -> None:
        assert CANONICAL_SHELLS == (
            "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            "AXIGNAL_PUBLIC_EMPLOYMENT",
        )

    def test_foundational_dependencies_match_registry(self) -> None:
        manifests = {m.library_id: m for m in canonical_library_manifests()}
        assert manifests["F02"].dependencies == ["F01"]
        assert manifests["F05"].dependencies == ["F03"]
        assert manifests["F06"].dependencies == ["F01", "F04"]
        assert manifests["F07"].dependencies == ["F05", "F06"]
        assert manifests["O01"].dependencies == list(FOUNDATIONAL_LIBRARIES)
