from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from .analysis import CRITICALITY_ORDER
from .io import load_payload
from .model import GraphValidationError


@dataclass(frozen=True)
class GatePolicy:
    max_affected_nodes: int | None = None
    min_tests: int = 0
    min_owners: int = 0
    fail_on_criticality: str | None = None
    forbid_node_ids: tuple[str, ...] = ()
    forbid_node_types: tuple[str, ...] = ()
    max_untested_nodes: int | None = None
    max_unowned_nodes: int | None = None
    require_complete_traversal: bool = False
    require_change_kind: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_affected_nodes": self.max_affected_nodes,
            "min_tests": self.min_tests,
            "min_owners": self.min_owners,
            "fail_on_criticality": self.fail_on_criticality,
            "forbid_node_ids": list(self.forbid_node_ids),
            "forbid_node_types": list(self.forbid_node_types),
            "max_untested_nodes": self.max_untested_nodes,
            "max_unowned_nodes": self.max_unowned_nodes,
            "require_complete_traversal": self.require_complete_traversal,
            "require_change_kind": self.require_change_kind,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GatePolicy":
        allowed = {
            "max_affected_nodes", "min_tests", "min_owners", "fail_on_criticality",
            "forbid_node_ids", "forbid_node_types", "max_untested_nodes",
            "max_unowned_nodes", "require_complete_traversal", "require_change_kind",
        }
        unknown = sorted(set(payload) - allowed)
        errors: list[str] = []
        if unknown:
            errors.append(f"unknown policy field(s): {', '.join(unknown)}")

        def nonnegative(name: str, default: int | None) -> int | None:
            value = payload.get(name, default)
            if value is None:
                return None
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"{name} must be a non-negative integer or null")
                return default
            return value

        def strings(name: str) -> tuple[str, ...]:
            value = payload.get(name, [])
            if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
                errors.append(f"{name} must be a list of non-empty strings")
                return ()
            return tuple(sorted(set(value)))

        criticality = payload.get("fail_on_criticality")
        if criticality is not None and criticality not in CRITICALITY_ORDER:
            errors.append("fail_on_criticality must be one of low, medium, high, critical, or null")
            criticality = None
        require_complete = payload.get("require_complete_traversal", False)
        require_kind = payload.get("require_change_kind", False)
        if not isinstance(require_complete, bool):
            errors.append("require_complete_traversal must be a boolean")
            require_complete = False
        if not isinstance(require_kind, bool):
            errors.append("require_change_kind must be a boolean")
            require_kind = False

        result = cls(
            max_affected_nodes=nonnegative("max_affected_nodes", None),
            min_tests=nonnegative("min_tests", 0) or 0,
            min_owners=nonnegative("min_owners", 0) or 0,
            fail_on_criticality=criticality,
            forbid_node_ids=strings("forbid_node_ids"),
            forbid_node_types=strings("forbid_node_types"),
            max_untested_nodes=nonnegative("max_untested_nodes", None),
            max_unowned_nodes=nonnegative("max_unowned_nodes", None),
            require_complete_traversal=require_complete,
            require_change_kind=require_kind,
        )
        if errors:
            raise GraphValidationError(errors)
        return result

    def with_overrides(self, **overrides: Any) -> "GatePolicy":
        clean = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **clean)


def load_policy(path: str | Path) -> GatePolicy:
    payload = load_payload(path)
    if "policy" in payload:
        payload = payload["policy"]
    if not isinstance(payload, dict):
        raise GraphValidationError(["policy document must be an object"])
    return GatePolicy.from_dict(payload)
