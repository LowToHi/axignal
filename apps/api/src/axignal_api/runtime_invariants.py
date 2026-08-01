from __future__ import annotations

from typing import TypeVar

T = TypeVar("T")


class RuntimeConfigurationInvariantError(RuntimeError):
    """Raised when validated runtime settings still lack a required value."""


def require_runtime_value(value: T | None, *, name: str) -> T:
    """Return a required setting or fail explicitly after settings validation.

    Runtime entrypoints previously relied on ``assert`` for this boundary. Python
    assertions can be disabled with ``-O`` and communicate neither the failed
    contract nor the affected setting. This helper remains active in every
    interpreter mode and never includes the setting value in the exception.
    """

    if value is None or value == "":
        raise RuntimeConfigurationInvariantError(
            f"{name} is missing after runtime settings validation"
        )
    return value
