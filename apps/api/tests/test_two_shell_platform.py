"""WP15 — Two-Shell Platform conformance tests."""

from __future__ import annotations

import pytest

from axignal_api.two_shell_platform import (
    TwoShellConformanceFailure,
    TwoShellPlatform,
)


@pytest.fixture()
def platform() -> TwoShellPlatform:
    instance = TwoShellPlatform()
    instance.load_registries()
    return instance


class TestTwoShellPlatform:
    def test_exact_two_shells(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t01_exact_two_shells() is True
        assert platform.registry_shells() == {
            "AXIGNAL_OPPORTUNITY_INTELLIGENCE",
            "AXIGNAL_PUBLIC_EMPLOYMENT",
        }

    def test_registered_once(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t02_t03_registered_once() is True

    def test_domain_manifests_declared(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t05_no_duplicated_identity() is True
        for shell in ("AXIGNAL_OPPORTUNITY_INTELLIGENCE", "AXIGNAL_PUBLIC_EMPLOYMENT"):
            assert platform.domain_manifest_version(shell) is not None

    def test_authorization_metadata(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t06_authorization_metadata() is True

    def test_workspace_factory_reused(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t07_workspace_factory() is True

    def test_capability_matrix(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t08_capability_matrix() is True

    def test_analytics_disclosures(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t09_analytics_disclosures() is True

    def test_no_core_split(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t10_no_core_split() is True

    def test_no_fork(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t11_no_fork() is True

    def test_procurement_rejected_as_shell(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t12_procurement_rejected() is True

    def test_no_country_or_library_shells(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t13_no_country_library_shells() is True

    def test_third_shell_rejected(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t14_third_shell_rejected() is True

    def test_library_placement(self, platform: TwoShellPlatform) -> None:
        assert platform.conformance_t15_library_placement() is True

    def test_full_conformance(self, platform: TwoShellPlatform) -> None:
        checks = platform.run_all()
        assert all(checks.values())
        assert len(checks) == 14

    def test_failure_contract(self) -> None:
        with pytest.raises(TwoShellConformanceFailure):
            raise TwoShellConformanceFailure("conformance failed")
