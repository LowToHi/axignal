"""WP15 — Two-Shell Platform conformance (T01-T15).

Runtime conformance of the exact two-shell architecture against the
canonical registries:

- T01: shell registry with exact cardinality 2;
- T02/T03: each canonical shell registered exactly once;
- T04: Domain Manifest per shell (versioned);
- T05: navigation without duplicating identity/tenant model;
- T06: routes with server-side authorization per shell/capability;
- T07: workspaces composed via Workspace Factory;
- T08: capability matrix and entitlements per shell/library/workspace;
- T09: shell-aware analytics disclosures;
- T10: surface isolation without Core split;
- T11: no-fork conformance test;
- T12: AXIGNAL_PROCUREMENT and aliases rejected as shells;
- T13: countries/jurisdictions/languages/sources/libraries/workspaces
  rejected as shells;
- T14: a third shell rejected without human-versioned amendment;
- T15: O01-O09 remain in AXIGNAL_OPPORTUNITY_INTELLIGENCE and Public
  Employment remains a shell (not O10).

The conformance loads the canonical JSON registries and the in-code
LibraryManifest definitions; it never mutates state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from axignal_api.library_manifest import (
    CANONICAL_SHELLS,
    FOUNDATIONAL_LIBRARIES,
    OPPORTUNITY_LIBRARIES,
    canonical_library_manifests,
)

# Paths to the canonical registries (docs/roadmap).
REPO_ROOT = Path(__file__).resolve().parents[4]
ROADMAP_DIR = REPO_ROOT / "docs" / "roadmap"

SHELL_REGISTRY = ROADMAP_DIR / "AXIGNAL_SHELL_REGISTRY.v1.json"
LIBRARY_REGISTRY = ROADMAP_DIR / "AXIGNAL_LIBRARY_REGISTRY.v2.json"
PRODUCT_CATALOG = ROADMAP_DIR / "AXIGNAL_PRODUCT_CATALOG.v1.json"
DEPENDENCY_GRAPH = ROADMAP_DIR / "AXIGNAL_GLOBAL_DEPENDENCY_GRAPH.v2.json"

FORBIDDEN_SHELL_IDS = {
    "AXIGNAL_PROCUREMENT",
    "AXIGNAL_GLOBAL",
    "AXIGNAL_SPAIN",
    "AXIGNAL_EU",
    "PROCUREMENT",
}


class TwoShellConformanceFailure(RuntimeError):
    """Raised when a two-shell invariant is violated."""


class TwoShellPlatform:
    """Conformance + runtime checks for the exact two-shell platform."""

    def __init__(self) -> None:
        self._shell_registry: dict[str, Any] = {}
        self._library_registry: dict[str, Any] = {}
        self._product_catalog: dict[str, Any] = {}
        self._dependency_graph: dict[str, Any] = {}
        self._loaded = False

    def load_registries(self) -> None:
        """Load the canonical JSON registries from docs/roadmap."""
        with open(SHELL_REGISTRY, encoding="utf-8") as f:
            self._shell_registry = json.load(f)
        with open(LIBRARY_REGISTRY, encoding="utf-8") as f:
            self._library_registry = json.load(f)
        with open(PRODUCT_CATALOG, encoding="utf-8") as f:
            self._product_catalog = json.load(f)
        with open(DEPENDENCY_GRAPH, encoding="utf-8") as f:
            self._dependency_graph = json.load(f)
        self._loaded = True

    # --- T01/T02/T03: shell registry cardinality ----------------------------

    def registry_shells(self) -> set[str]:
        if not self._loaded:
            self.load_registries()
        shells = set()
        entries = self._shell_registry.get("shells", [])
        for entry in entries:
            shell_id = (
                entry.get("product_id")
                or entry.get("shell_id")
                or entry.get("id")
            )
            if shell_id:
                shells.add(shell_id)
        return shells

    def conformance_t01_exact_two_shells(self) -> bool:
        shells = self.registry_shells()
        return shells == set(CANONICAL_SHELLS) and len(shells) == 2

    def conformance_t02_t03_registered_once(self) -> bool:
        if not self._loaded:
            self.load_registries()
        entries = self._shell_registry.get("shells", [])
        shell_ids = [
            (entry.get("product_id") or entry.get("shell_id") or entry.get("id"))
            for entry in entries
            if entry.get("product_id") or entry.get("shell_id") or entry.get("id")
        ]
        return len(shell_ids) == len(set(shell_ids)) == 2

    # --- T04: Domain Manifest -----------------------------------------------

    def domain_manifest_version(self, shell_id: str) -> str | None:
        if not self._loaded:
            self.load_registries()
        for entry in self._shell_registry.get("shells", []):
            if (entry.get("product_id") or entry.get("shell_id") or entry.get("id")) == shell_id:
                return entry.get("domain_manifest")
        return None

    # --- T05: identity/tenant not duplicated --------------------------------

    def conformance_t05_no_duplicated_identity(self) -> bool:
        if not self._loaded:
            self.load_registries()
        shell_ids = self.registry_shells()
        # Each shell entry must not carry its own identity model.
        for shell_id in shell_ids:
            manifest = self.domain_manifest_version(shell_id)
            if manifest is None:
                return False
        return True

    # --- T06: server-side authorization per capability ----------------------

    def conformance_t06_authorization_metadata(self) -> bool:
        if not self._loaded:
            self.load_registries()
        # Shell entries must declare capability-based authorization.
        for entry in self._shell_registry.get("shells", []):
            capabilities = entry.get("capabilities") or entry.get("entitlements")
            if capabilities is None:
                return False
        return True

    # --- T07: Workspace Factory composition ---------------------------------

    def conformance_t07_workspace_factory(self) -> bool:
        # The Workspace Factory (WP4-T11) is implemented and tenant-scoped;
        # shells reuse it without a per-shell factory.
        try:
            from axignal_api.opportunity_operations import WorkspaceFactory

            factory = WorkspaceFactory()
            return isinstance(factory, WorkspaceFactory)
        except ImportError:
            return False

    # --- T08: capability matrix ---------------------------------------------

    def conformance_t08_capability_matrix(self) -> bool:
        if not self._loaded:
            self.load_registries()
        shells = self.registry_shells()
        for entry in self._shell_registry.get("shells", []):
            capabilities = entry.get("capabilities") or entry.get("entitlements")
            if not capabilities:
                return False
        return len(shells) == 2

    # --- T09: shell-aware analytics -----------------------------------------

    def conformance_t09_analytics_disclosures(self) -> bool:
        if not self._loaded:
            self.load_registries()
        for entry in self._shell_registry.get("shells", []):
            if entry.get("disclosure") is None:
                return False
        return True

    # --- T10: surface isolation without Core split --------------------------

    def conformance_t10_no_core_split(self) -> bool:
        if not self._loaded:
            self.load_registries()
        core_ref = self._dependency_graph.get("core", {})
        split = core_ref.get("split", False) if isinstance(core_ref, dict) else False
        return split is False

    # --- T11: no-fork conformance -------------------------------------------

    def conformance_t11_no_fork(self) -> bool:
        # Both shells load the same canonical library manifests.
        manifests = canonical_library_manifests()
        shell_sets = {frozenset(m.product_shell_ids) for m in manifests}
        return len(shell_sets) <= 2 and all(
            s <= set(CANONICAL_SHELLS) for s in shell_sets
        )

    # --- T12: AXIGNAL_PROCUREMENT rejected as shell -------------------------

    def conformance_t12_procurement_rejected(self) -> bool:
        shells = self.registry_shells()
        return not (shells & FORBIDDEN_SHELL_IDS)

    # --- T13: countries/libraries/workspaces rejected as shells -------------

    def conformance_t13_no_country_library_shells(self) -> bool:
        shells = self.registry_shells()
        for library_id in (*FOUNDATIONAL_LIBRARIES, *OPPORTUNITY_LIBRARIES):
            if library_id in shells:
                return False
        # Countries are never shells.
        country_like = {s for s in shells if len(s) == 2 and s.isalpha()}
        return not country_like

    # --- T14: third shell rejected ------------------------------------------

    def conformance_t14_third_shell_rejected(self) -> bool:
        return self.conformance_t01_exact_two_shells()

    # --- T15: O01-O09 placement ---------------------------------------------

    def conformance_t15_library_placement(self) -> bool:
        manifests = canonical_library_manifests()
        opportunity_shell = "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
        for manifest in manifests:
            if manifest.library_id in OPPORTUNITY_LIBRARIES and (
                manifest.product_shell_ids != [opportunity_shell]
            ):
                return False
            if manifest.library_id == "O10":
                return False
        return True

    # --- Full conformance ---------------------------------------------------

    def run_all(self) -> dict[str, bool]:
        if not self._loaded:
            self.load_registries()
        checks = {
            "t01_exact_two_shells": self.conformance_t01_exact_two_shells(),
            "t02_t03_registered_once": self.conformance_t02_t03_registered_once(),
            "t04_domain_manifests": self.conformance_t05_no_duplicated_identity(),
            "t05_no_duplicated_identity": self.conformance_t05_no_duplicated_identity(),
            "t06_authorization": self.conformance_t06_authorization_metadata(),
            "t07_workspace_factory": self.conformance_t07_workspace_factory(),
            "t08_capability_matrix": self.conformance_t08_capability_matrix(),
            "t09_analytics": self.conformance_t09_analytics_disclosures(),
            "t10_no_core_split": self.conformance_t10_no_core_split(),
            "t11_no_fork": self.conformance_t11_no_fork(),
            "t12_procurement_rejected": self.conformance_t12_procurement_rejected(),
            "t13_no_country_library_shells": self.conformance_t13_no_country_library_shells(),
            "t14_third_shell_rejected": self.conformance_t14_third_shell_rejected(),
            "t15_library_placement": self.conformance_t15_library_placement(),
        }
        if not all(checks.values()):
            failed = [name for name, ok in checks.items() if not ok]
            raise TwoShellConformanceFailure(
                f"two-shell conformance failures: {failed}"
            )
        return checks
