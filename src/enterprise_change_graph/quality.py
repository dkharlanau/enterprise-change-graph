from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass

from .model import EnterpriseGraph


@dataclass(frozen=True)
class QualityReport:
    orphan_nodes: tuple[str, ...]
    dead_end_nodes: tuple[str, ...]
    nodes_without_reachable_tests: tuple[str, ...]
    nodes_without_reachable_owners: tuple[str, ...]
    high_criticality_without_tests: tuple[str, ...]
    high_criticality_without_owners: tuple[str, ...]
    generic_relations: tuple[str, ...]
    relation_counts: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "summary": {
                "orphan_nodes": len(self.orphan_nodes),
                "dead_end_nodes": len(self.dead_end_nodes),
                "nodes_without_reachable_tests": len(self.nodes_without_reachable_tests),
                "nodes_without_reachable_owners": len(self.nodes_without_reachable_owners),
                "high_criticality_without_tests": len(self.high_criticality_without_tests),
                "high_criticality_without_owners": len(self.high_criticality_without_owners),
                "generic_relations": len(self.generic_relations),
            },
            "orphan_nodes": list(self.orphan_nodes),
            "dead_end_nodes": list(self.dead_end_nodes),
            "nodes_without_reachable_tests": list(self.nodes_without_reachable_tests),
            "nodes_without_reachable_owners": list(self.nodes_without_reachable_owners),
            "high_criticality_without_tests": list(self.high_criticality_without_tests),
            "high_criticality_without_owners": list(self.high_criticality_without_owners),
            "generic_relations": list(self.generic_relations),
            "relation_counts": dict(sorted(self.relation_counts.items())),
        }


def _adjacency(graph: EnterpriseGraph) -> dict[str, set[str]]:
    result = {node_id: set() for node_id in graph.nodes}
    for edge in graph.edges:
        direction = graph.effective_propagation(edge, None)
        if direction in {"forward", "both"}:
            result[edge.source].add(edge.target)
        if direction in {"reverse", "both"}:
            result[edge.target].add(edge.source)
    return result


def _reachable_kinds(start: str, graph: EnterpriseGraph, adjacency: dict[str, set[str]]) -> set[str]:
    seen = {start}
    queue = deque([start])
    kinds: set[str] = set()
    while queue:
        current = queue.popleft()
        for target in sorted(adjacency[current]):
            if target in seen:
                continue
            seen.add(target)
            kinds.add(graph.nodes[target].type)
            queue.append(target)
    return kinds


def analyze_quality(graph: EnterpriseGraph) -> QualityReport:
    connected = {edge.source for edge in graph.edges} | {edge.target for edge in graph.edges}
    orphan_nodes = tuple(sorted(set(graph.nodes) - connected))
    adjacency = _adjacency(graph)
    eligible = [node for node in graph.nodes.values() if node.type not in {"test", "owner"}]
    dead_end_nodes = tuple(sorted(node.id for node in eligible if not adjacency[node.id]))

    without_tests: list[str] = []
    without_owners: list[str] = []
    high_no_tests: list[str] = []
    high_no_owners: list[str] = []
    for node in sorted(eligible, key=lambda item: item.id):
        kinds = _reachable_kinds(node.id, graph, adjacency)
        if "test" not in kinds:
            without_tests.append(node.id)
            if node.criticality in {"high", "critical"}:
                high_no_tests.append(node.id)
        if "owner" not in kinds:
            without_owners.append(node.id)
            if node.criticality in {"high", "critical"}:
                high_no_owners.append(node.id)

    relation_counts = Counter(edge.relation for edge in graph.edges)
    generic = tuple(sorted(relation for relation in relation_counts if relation in {"related-to", "linked-to", "associated-with"}))
    return QualityReport(
        orphan_nodes=orphan_nodes,
        dead_end_nodes=dead_end_nodes,
        nodes_without_reachable_tests=tuple(without_tests),
        nodes_without_reachable_owners=tuple(without_owners),
        high_criticality_without_tests=tuple(high_no_tests),
        high_criticality_without_owners=tuple(high_no_owners),
        generic_relations=generic,
        relation_counts=dict(relation_counts),
    )
