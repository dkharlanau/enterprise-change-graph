from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

from .analysis import ImpactResult, analyze_impact
from .model import EnterpriseGraph


@dataclass(frozen=True)
class ReleaseAnalysis:
    change_ids: tuple[str, ...]
    impacts: dict[str, ImpactResult]
    collisions: dict[str, tuple[str, ...]]
    regression_tests: tuple[str, ...]
    owners: tuple[str, ...]
    approval_routes: dict[str, tuple[str, ...]]

    def to_dict(self) -> dict:
        return {
            "summary": {
                "changes": len(self.change_ids),
                "colliding_nodes": len(self.collisions),
                "regression_tests": list(self.regression_tests),
                "owners": list(self.owners),
            },
            "change_ids": list(self.change_ids),
            "collisions": {node: list(changes) for node, changes in sorted(self.collisions.items())},
            "approval_routes": {owner: list(changes) for owner, changes in sorted(self.approval_routes.items())},
            "impacts": {change_id: self.impacts[change_id].to_dict() for change_id in self.change_ids},
        }


def analyze_release(
    graph: EnterpriseGraph,
    change_ids: Iterable[str],
    *,
    max_depth: int | None = None,
) -> ReleaseAnalysis:
    selected = tuple(sorted(set(change_ids)))
    if not selected:
        raise ValueError("at least one change id is required")
    unknown = sorted(set(selected) - set(graph.changes))
    if unknown:
        raise KeyError(f"unknown change id(s): {', '.join(unknown)}")

    impacts = {change_id: analyze_impact(graph, change_id=change_id, max_depth=max_depth) for change_id in selected}
    node_changes: dict[str, set[str]] = defaultdict(set)
    owner_changes: dict[str, set[str]] = defaultdict(set)
    tests: set[str] = set()
    owners: set[str] = set()
    for change_id, impact in impacts.items():
        for node in impact.impacted:
            node_changes[node.id].add(change_id)
        for test in impact.regression_tests:
            tests.add(test.id)
        for owner in impact.owners:
            owners.add(owner.id)
            owner_changes[owner.id].add(change_id)

    collisions = {
        node_id: tuple(sorted(changes))
        for node_id, changes in node_changes.items()
        if len(changes) > 1
    }
    approval_routes = {owner: tuple(sorted(changes)) for owner, changes in owner_changes.items()}
    return ReleaseAnalysis(
        change_ids=selected,
        impacts=impacts,
        collisions=dict(sorted(collisions.items())),
        regression_tests=tuple(sorted(tests)),
        owners=tuple(sorted(owners)),
        approval_routes=dict(sorted(approval_routes.items())),
    )
