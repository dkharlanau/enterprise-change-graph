from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .analysis import ImpactResult
from .model import EnterpriseGraph


@dataclass(frozen=True)
class CoverageAssessment:
    eligible_nodes: tuple[str, ...]
    test_coverage: dict[str, tuple[str, ...]]
    owner_coverage: dict[str, tuple[str, ...]]
    untested_nodes: tuple[str, ...]
    unowned_nodes: tuple[str, ...]
    minimal_regression_tests: tuple[str, ...]
    minimal_owners: tuple[str, ...]

    @property
    def test_coverage_ratio(self) -> float:
        if not self.eligible_nodes:
            return 1.0
        return (len(self.eligible_nodes) - len(self.untested_nodes)) / len(self.eligible_nodes)

    @property
    def owner_coverage_ratio(self) -> float:
        if not self.eligible_nodes:
            return 1.0
        return (len(self.eligible_nodes) - len(self.unowned_nodes)) / len(self.eligible_nodes)

    def to_dict(self) -> dict:
        return {
            "eligible_nodes": list(self.eligible_nodes),
            "test_coverage_ratio": round(self.test_coverage_ratio, 4),
            "owner_coverage_ratio": round(self.owner_coverage_ratio, 4),
            "minimal_regression_tests": list(self.minimal_regression_tests),
            "minimal_owners": list(self.minimal_owners),
            "untested_nodes": list(self.untested_nodes),
            "unowned_nodes": list(self.unowned_nodes),
            "test_coverage": {key: list(value) for key, value in sorted(self.test_coverage.items())},
            "owner_coverage": {key: list(value) for key, value in sorted(self.owner_coverage.items())},
        }


def _effective_adjacency(graph: EnterpriseGraph, impact: ImpactResult) -> dict[str, set[str]]:
    impacted_ids = {node.id for node in impact.impacted}
    filters = impact.filters
    include_rel = set(filters.get("include_relations", ()))
    exclude_rel = set(filters.get("exclude_relations", ()))
    include_types = set(filters.get("include_node_types", ()))
    exclude_types = set(filters.get("exclude_node_types", ()))

    def relation_allowed(relation: str) -> bool:
        return relation not in exclude_rel and (not include_rel or relation in include_rel)

    def node_allowed(node_id: str) -> bool:
        if node_id not in impacted_ids:
            return False
        node_type = graph.nodes[node_id].type
        if node_type in exclude_types:
            return False
        if include_types and node_type not in include_types and node_id not in impact.seeds:
            return False
        return True

    adjacency = {node_id: set() for node_id in impacted_ids}
    for edge in graph.edges:
        if not relation_allowed(edge.relation):
            continue
        direction = graph.effective_propagation(edge, impact.change_kind)
        pairs: list[tuple[str, str]] = []
        if direction in {"forward", "both"}:
            pairs.append((edge.source, edge.target))
        if direction in {"reverse", "both"}:
            pairs.append((edge.target, edge.source))
        for source, target in pairs:
            if source in impacted_ids and target in impacted_ids and node_allowed(target):
                adjacency[source].add(target)
    return adjacency


def _ancestors(target: str, adjacency: dict[str, set[str]]) -> set[str]:
    reverse: dict[str, set[str]] = {node: set() for node in adjacency}
    for source, targets in adjacency.items():
        for child in targets:
            reverse.setdefault(child, set()).add(source)
    seen = {target}
    stack = [target]
    while stack:
        current = stack.pop()
        for parent in sorted(reverse.get(current, ())):
            if parent not in seen:
                seen.add(parent)
                stack.append(parent)
    seen.discard(target)
    return seen


def _greedy_cover(coverage: dict[str, tuple[str, ...]], target: set[str]) -> tuple[str, ...]:
    remaining = set(target)
    selected: list[str] = []
    while remaining:
        ranked = sorted(
            ((len(set(nodes) & remaining), key) for key, nodes in coverage.items()),
            key=lambda item: (-item[0], item[1]),
        )
        if not ranked or ranked[0][0] == 0:
            break
        _, chosen = ranked[0]
        selected.append(chosen)
        remaining -= set(coverage[chosen])
    return tuple(selected)


def assess_coverage(
    graph: EnterpriseGraph,
    impact: ImpactResult,
    *,
    excluded_types: Iterable[str] = ("test", "owner"),
) -> CoverageAssessment:
    excluded = set(excluded_types)
    eligible = tuple(sorted(node.id for node in impact.impacted if node.type not in excluded))
    eligible_set = set(eligible)
    adjacency = _effective_adjacency(graph, impact)

    test_coverage: dict[str, tuple[str, ...]] = {}
    for test in sorted(impact.regression_tests, key=lambda node: node.id):
        covered = tuple(sorted(_ancestors(test.id, adjacency) & eligible_set))
        test_coverage[test.id] = covered

    owner_coverage: dict[str, tuple[str, ...]] = {}
    for owner in sorted(impact.owners, key=lambda node: node.id):
        covered = tuple(sorted(_ancestors(owner.id, adjacency) & eligible_set))
        owner_coverage[owner.id] = covered

    tested = {node for nodes in test_coverage.values() for node in nodes}
    owned = {node for nodes in owner_coverage.values() for node in nodes}
    untested = tuple(sorted(eligible_set - tested))
    unowned = tuple(sorted(eligible_set - owned))
    minimal_tests = _greedy_cover(test_coverage, tested)
    minimal_owners = _greedy_cover(owner_coverage, owned)

    return CoverageAssessment(
        eligible_nodes=eligible,
        test_coverage=test_coverage,
        owner_coverage=owner_coverage,
        untested_nodes=untested,
        unowned_nodes=unowned,
        minimal_regression_tests=minimal_tests,
        minimal_owners=minimal_owners,
    )
