"""LibraryManifest — WP2-T01 base contract.

A LibraryManifest declares the canonical identity, scope, dependencies,
workspace and product-shell placement of a library (F01-F07 foundational
or O01-O09 opportunity) exactly as governed by AX-GE2E-FINISH-004 v2.1.0.

Cardinality rules enforced here:
- libraries are NOT shells (is_shell=false always);
- O01-O09 belong to AXIGNAL_OPPORTUNITY_INTELLIGENCE;
- F01-F07 are shared foundational libraries available to both shells;
- no third shell, no per-country/per-source/per-language shells;
- Public Employment is never registered as O10.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

FOUNDATIONAL_LIBRARIES = ("F01", "F02", "F03", "F04", "F05", "F06", "F07")
OPPORTUNITY_LIBRARIES = ("O01", "O02", "O03", "O04", "O05", "O06", "O07", "O08", "O09")
ALL_LIBRARIES = FOUNDATIONAL_LIBRARIES + OPPORTUNITY_LIBRARIES

PRIMARY_SHELL = "AXIGNAL_OPPORTUNITY_INTELLIGENCE"
SECOND_SHELL = "AXIGNAL_PUBLIC_EMPLOYMENT"
CANONICAL_SHELLS = (PRIMARY_SHELL, SECOND_SHELL)

# Canonical workspace per opportunity library (contract section 7).
CANONICAL_WORKSPACES = {
    "O01": "BID_WORKSPACE",
    "O02": "GRANTS_WORKSPACE",
    "O03": "REGULATION_WORKSPACE",
    "O04": "INFRASTRUCTURE_WORKSPACE",
    "O05": "CORPORATE_WORKSPACE",
    "O06": "SOVEREIGN_WORKSPACE",
    "O07": "TRADE_WORKSPACE",
    "O08": "ENERGY_CLIMATE_WORKSPACE",
    "O09": "INNOVATION_IP_WORKSPACE",
}


class LibraryType(StrEnum):
    FOUNDATIONAL = "FOUNDATIONAL"
    OPPORTUNITY = "OPPORTUNITY"


class LibraryStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    ENGINEERING_IN_PROGRESS = "ENGINEERING_IN_PROGRESS"
    ENGINEERING_EVIDENCE_READY = "ENGINEERING_EVIDENCE_READY"
    ENGINEERING_E2E_PASS = "ENGINEERING_E2E_PASS"
    ENGINEERING_REJECTED = "ENGINEERING_REJECTED"
    SUPERSEDED = "SUPERSEDED"


class LibraryManifest(BaseModel):
    """Canonical, versioned contract of a single library."""

    schema_version: Literal["axignal.library-manifest.v1"] = "axignal.library-manifest.v1"
    library_id: str = Field(pattern=r"^[FO]\d{2}$")
    name: str = Field(min_length=3, max_length=200)
    library_type: LibraryType
    status: LibraryStatus = LibraryStatus.NOT_STARTED
    manifest_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    workspace: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    product_shell_ids: list[str] = Field(default_factory=list)
    is_shell: Literal[False] = False
    is_root_product: Literal[False] = False
    source_manifests: list[str] = Field(default_factory=list)
    coverage: dict[str, Any] = Field(default_factory=dict)
    rights: dict[str, Any] = Field(default_factory=dict)
    privacy: dict[str, Any] = Field(default_factory=dict)
    exact_head: str | None = None

    @model_validator(mode="after")
    def validate_library_rules(self) -> LibraryManifest:
        if self.library_id not in ALL_LIBRARIES:
            raise ValueError(
                f"library_id must be one of {ALL_LIBRARIES}; got {self.library_id!r}"
            )
        if self.library_id == "O10":
            raise ValueError(
                "O10 is not a canonical library; Public Employment is a shell, not O10"
            )
        if (
            self.library_type == LibraryType.FOUNDATIONAL
            and self.library_id not in FOUNDATIONAL_LIBRARIES
        ):
            raise ValueError(
                f"foundational library_id must be in {FOUNDATIONAL_LIBRARIES}"
            )
        if (
            self.library_type == LibraryType.OPPORTUNITY
            and self.library_id not in OPPORTUNITY_LIBRARIES
        ):
            raise ValueError(
                f"opportunity library_id must be in {OPPORTUNITY_LIBRARIES}"
            )
        if self.library_type == LibraryType.OPPORTUNITY:
            expected = CANONICAL_WORKSPACES[self.library_id]
            if self.workspace != expected:
                raise ValueError(
                    f"workspace for {self.library_id} must be {expected!r}; got {self.workspace!r}"
                )
        if self.library_type == LibraryType.FOUNDATIONAL and self.workspace is not None:
            raise ValueError("foundational libraries must not declare a workspace")
        # Shell placement rules.
        if self.library_type == LibraryType.OPPORTUNITY:
            if self.product_shell_ids != [PRIMARY_SHELL]:
                raise ValueError(
                    f"opportunity library {self.library_id} must belong to {PRIMARY_SHELL!r}"
                )
        else:
            if set(self.product_shell_ids) != set(CANONICAL_SHELLS):
                raise ValueError(
                    f"foundational library {self.library_id} must be available to both shells"
                )
        for shell_id in self.product_shell_ids:
            if shell_id not in CANONICAL_SHELLS:
                raise ValueError(
                    f"unknown shell {shell_id!r}; only {CANONICAL_SHELLS} are canonical"
                )
        return self


def canonical_library_manifests() -> list[LibraryManifest]:
    """Return the canonical manifests for F01-F07 and O01-O09 (contract section 6-7)."""
    foundational = {
        "F01": "Jurisdictions and Geography",
        "F02": "Entities, Organisations and Ownership",
        "F03": "Taxonomies and Classifications",
        "F04": "Time, Currency, Value and Units",
        "F05": "Languages, Terminology and Translation",
        "F06": "Rights, Sources and Provenance",
        "F07": "Documents and Content",
    }
    opportunity = {
        "O01": "Global Public Procurement",
        "O02": "Grants and Non-Dilutive Funding",
        "O03": "Regulation and Policy-Induced Demand",
        "O04": "Infrastructure and Capital Projects",
        "O05": "Corporate, Filings and Ownership Signals",
        "O06": "Sovereign, Macro and Public Investment",
        "O07": "Trade, Supply Chain and Market Flows",
        "O08": "Energy and Climate Transition",
        "O09": "Innovation, Research and Intellectual Property",
    }
    manifests: list[LibraryManifest] = []
    for library_id, name in foundational.items():
        manifests.append(
            LibraryManifest(
                library_id=library_id,
                name=name,
                library_type=LibraryType.FOUNDATIONAL,
                manifest_version="1.0.0",
                dependencies=_foundational_dependencies(library_id),
                product_shell_ids=[PRIMARY_SHELL, SECOND_SHELL],
            )
        )
    for library_id, name in opportunity.items():
        manifests.append(
            LibraryManifest(
                library_id=library_id,
                name=name,
                library_type=LibraryType.OPPORTUNITY,
                manifest_version="1.0.0",
                workspace=CANONICAL_WORKSPACES[library_id],
                dependencies=[*FOUNDATIONAL_LIBRARIES],
                product_shell_ids=[PRIMARY_SHELL],
            )
        )
    return manifests


def _foundational_dependencies(library_id: str) -> list[str]:
    dependencies: dict[str, list[str]] = {
        "F01": [],
        "F02": ["F01"],
        "F03": [],
        "F04": [],
        "F05": ["F03"],
        "F06": ["F01", "F04"],
        "F07": ["F05", "F06"],
    }
    return dependencies[library_id]
