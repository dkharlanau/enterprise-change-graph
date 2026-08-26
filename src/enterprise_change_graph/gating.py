from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .analysis import CRITICALITY_ORDER, ImpactResult


@dataclass(frozen=True)
class GateResult:
    violations: tuple[str, ...]
    impact: ImpactResult

    @property
    def passed(self) -> bool:
        return not self.violations

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violations": list(self.violations),
            "impact": self.impact.to_dict()["summary"],
        }


def evaluate_gate(
    impact: ImpactResult,
    *,
    max_affected_nodes: int | None = None,
    min_tests: int = 0,
    min_owners: int = 0,
    fail_on_criticality: str | None = None,
    forbid_node_ids: Iterable[str] = (),
    forbid_node_types: Iterable[str] = (),
) -> GateResult:
    if max_affected_nodes is not None and max_affected_nodes < 0:
        raise ValueError("max_affected_nodes must be >= 0")
    if min_tests < 0:
        raise ValueError("min_tests must be >= 0")
    if min_owners < 0:
        raise ValueError("min_owners must be >= 0")
    if fail_on_criticality is not None and fail_on_criticality not in CRITICALITY_ORDER:
        raise ValueError(
            "fail_on_criticality must be one of: low, medium, high, critical"
        )

    violations: list[str] = []

    if max_affected_nodes is not None and len(impact.impacted) > max_affected_nodes:
        violations.append(
            f"affected nodes {len(impact.impacted)} exceeds maximum "
            f"{max_affected_nodes}"
        )

    if len(impact.regression_tests) < min_tests:
        violations.append(
            f"regression tests {len(impact.regression_tests)} is below minimum "
            f"{min_tests}"
        )

    if len(impact.owners) < min_owners:
        violations.append(
            f"owners {len(impact.owners)} is below minimum {min_owners}"
        )

    if fail_on_criticality is not None:
        threshold = CRITICALITY_ORDER[fail_on_criticality]
        violating = tuple(
            node
            for node in impact.impacted
            if CRITICALITY_ORDER[node.criticality] >= threshold
        )
        if violating:
            ids = ", ".join(node.id for node in violating)
            violations.append(
                f"criticality threshold {fail_on_criticality} reached by: {ids}"
            )

    forbidden_ids = set(forbid_node_ids)
    hit_ids = sorted(node.id for node in impact.impacted if node.id in forbidden_ids)
    if hit_ids:
        violations.append(f"forbidden impacted node(s): {', '.join(hit_ids)}")

    forbidden_types = set(forbid_node_types)
    hit_types = sorted(
        {node.type for node in impact.impacted if node.type in forbidden_types}
    )
    if hit_types:
        violations.append(f"forbidden impacted node type(s): {', '.join(hit_types)}")

    return GateResult(violations=tuple(violations), impact=impact)
