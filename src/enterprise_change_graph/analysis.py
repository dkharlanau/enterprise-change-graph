from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass
from typing import Iterable

from .model import Change, Edge, EnterpriseGraph

CRITICALITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class ImpactedNode:
    id: str
    type: str
    name: str
    criticality: str
    depth: int
    path: tuple[str, ...]
    relations: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "criticality": self.criticality,
            "depth": self.depth,
            "path": list(self.path),
            "relations": list(self.relations),
        }


@dataclass(frozen=True)
class ImpactResult:
    change_id: str | None
    change_title: str | None
    seeds: tuple[str, ...]
    impacted: tuple[ImpactedNode, ...]
    truncated: bool = False

    @property
    def by_type(self) -> dict[str, int]:
        return dict(sorted(Counter(node.type for node in self.impacted).items()))

    @property
    def by_criticality(self) -> dict[str, int]:
        counts = Counter(node.criticality for node in self.impacted)
        return {
            level: counts[level]
            for level in ("critical", "high", "medium", "low")
            if counts[level]
        }

    @property
    def max_criticality(self) -> str | None:
        if not self.impacted:
            return None
        return max(
            (node.criticality for node in self.impacted),
            key=lambda level: CRITICALITY_ORDER[level],
        )

    @property
    def regression_tests(self) -> tuple[ImpactedNode, ...]:
        return tuple(node for node in self.impacted if node.type == "test")

    @property
    def owners(self) -> tuple[ImpactedNode, ...]:
        return tuple(node for node in self.impacted if node.type == "owner")

    def to_dict(self) -> dict:
        return {
            "change_id": self.change_id,
            "change_title": self.change_title,
            "seeds": list(self.seeds),
            "summary": {
                "affected_nodes": len(self.impacted),
                "by_type": self.by_type,
                "by_criticality": self.by_criticality,
                "max_criticality": self.max_criticality,
                "regression_tests": [node.id for node in self.regression_tests],
                "owners": [node.id for node in self.owners],
                "truncated": self.truncated,
            },
            "impacted": [node.to_dict() for node in self.impacted],
        }


def _neighbors(node_id: str, edges: Iterable[Edge]) -> list[tuple[str, str]]:
    neighbors: list[tuple[str, str]] = []
    for edge in edges:
        if edge.propagation in {"forward", "both"} and edge.source == node_id:
            neighbors.append((edge.target, edge.relation))
        if edge.propagation in {"reverse", "both"} and edge.target == node_id:
            neighbors.append((edge.source, edge.relation))
    return sorted(neighbors, key=lambda item: (item[0], item[1]))


def analyze_impact(
    graph: EnterpriseGraph,
    *,
    change_id: str | None = None,
    seeds: Iterable[str] | None = None,
    max_depth: int | None = None,
) -> ImpactResult:
    if max_depth is not None and max_depth < 0:
        raise ValueError("max_depth must be >= 0")

    change: Change | None = None
    if change_id is not None:
        try:
            change = graph.changes[change_id]
        except KeyError as exc:
            raise KeyError(f"unknown change id: {change_id}") from exc

    selected_seeds = tuple(seeds or (change.seeds if change else ()))
    if not selected_seeds:
        raise ValueError("at least one seed node is required")

    unknown = sorted(set(selected_seeds) - set(graph.nodes))
    if unknown:
        raise KeyError(f"unknown seed node(s): {', '.join(unknown)}")

    queue = deque()
    visited: dict[str, tuple[int, tuple[str, ...], tuple[str, ...]]] = {}

    for seed in sorted(set(selected_seeds)):
        visited[seed] = (0, (seed,), ())
        queue.append(seed)

    truncated = False
    while queue:
        current = queue.popleft()
        depth, path, relations = visited[current]

        next_nodes = _neighbors(current, graph.edges)
        if max_depth is not None and depth >= max_depth:
            if any(neighbor not in visited for neighbor, _ in next_nodes):
                truncated = True
            continue

        for neighbor, relation in next_nodes:
            if neighbor in visited:
                continue
            visited[neighbor] = (
                depth + 1,
                path + (neighbor,),
                relations + (relation,),
            )
            queue.append(neighbor)

    impacted = []
    for node_id, (depth, path, relations) in visited.items():
        node = graph.nodes[node_id]
        impacted.append(
            ImpactedNode(
                id=node.id,
                type=node.type,
                name=node.name,
                criticality=node.criticality,
                depth=depth,
                path=path,
                relations=relations,
            )
        )

    impacted.sort(key=lambda node: (node.depth, node.type, node.id))
    return ImpactResult(
        change_id=change.id if change else None,
        change_title=change.title if change else None,
        seeds=tuple(sorted(set(selected_seeds))),
        impacted=tuple(impacted),
        truncated=truncated,
    )
