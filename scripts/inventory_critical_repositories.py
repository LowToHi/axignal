#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = (
    "apps/api/src/axignal_api/identity_repository.py",
    "apps/api/src/axignal_api/billing_repository.py",
    "apps/api/src/axignal_api/seat_repository.py",
    "apps/api/src/axignal_api/entitlement_repository.py",
    "apps/api/src/axignal_api/organic_repository.py",
    "apps/api/src/axignal_api/proposal_repository.py",
    "apps/api/src/axignal_api/ted_repository.py",
    "apps/api/src/axignal_api/admission_repository.py",
    "apps/api/src/axignal_api/retention_repository.py",
)


def call_name(node: ast.Call) -> str | None:
    function = node.func
    if isinstance(function, ast.Name):
        return function.id
    if isinstance(function, ast.Attribute):
        parts = [function.attr]
        value = function.value
        while isinstance(value, ast.Attribute):
            parts.append(value.attr)
            value = value.value
        if isinstance(value, ast.Name):
            parts.append(value.id)
        return ".".join(reversed(parts))
    return None


def main() -> None:
    files: dict[str, object] = {}
    total_methods = 0
    total_asserts = 0

    for relative in TARGETS:
        path = ROOT / relative
        if not path.exists():
            raise SystemExit(f"Missing critical repository: {relative}")
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=relative)
        classes: list[dict[str, object]] = []
        file_asserts = sum(isinstance(node, ast.Assert) for node in ast.walk(tree))
        total_asserts += file_asserts

        for class_node in [node for node in tree.body if isinstance(node, ast.ClassDef)]:
            methods: list[dict[str, object]] = []
            for method in [
                node
                for node in class_node.body
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
                and not node.name.startswith("__")
            ]:
                calls = sorted(
                    {
                        name
                        for node in ast.walk(method)
                        if isinstance(node, ast.Call)
                        if (name := call_name(node)) is not None
                    }
                )
                roles = sorted(
                    {
                        keyword.value.value
                        for node in ast.walk(method)
                        if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "_cursor"
                        for keyword in node.keywords
                        if keyword.arg == "role"
                        and isinstance(keyword.value, ast.Constant)
                        and isinstance(keyword.value.value, str)
                    }
                )
                methods.append(
                    {
                        "name": method.name,
                        "line_start": method.lineno,
                        "line_end": method.end_lineno,
                        "lines": (method.end_lineno or method.lineno) - method.lineno + 1,
                        "roles": roles,
                        "calls": calls,
                        "asserts": sum(
                            isinstance(node, ast.Assert) for node in ast.walk(method)
                        ),
                        "raises": sorted(
                            {
                                call_name(node.exc)
                                for node in ast.walk(method)
                                if isinstance(node, ast.Raise)
                                and isinstance(node.exc, ast.Call)
                                and call_name(node.exc) is not None
                            }
                        ),
                    }
                )
            if methods:
                total_methods += len(methods)
                classes.append(
                    {
                        "name": class_node.name,
                        "bases": [ast.unparse(base) for base in class_node.bases],
                        "methods": methods,
                    }
                )

        files[relative] = {
            "physical_lines": len(source.splitlines()),
            "asserts": file_asserts,
            "classes": classes,
        }

    print(
        json.dumps(
            {
                "schema": "axignal.critical-repository-inventory.v0.1",
                "files": files,
                "summary": {
                    "file_count": len(TARGETS),
                    "method_count": total_methods,
                    "assert_count": total_asserts,
                },
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
