from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
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
    change_kind: str | None = None
    truncated: bool = False
    filtered: bool = False
    filters: dict[str, tuple[str, ...]] = field(default_factory=dict)

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
            "change_kind": self.change_kind,
            "seeds": list(self.seeds),
            "summary": {
                "affected_nodes": len(self.impacted),
                "by_type": self.by_type,
                "by_criticality": self.by_criticality,
                "max_criticality": self.max_criticality,
                "regression_tests": [node.id for node in self.regression_tests],
                "owners": [node.id for node in self.owners],
                "truncated": self.truncated,
                "filtered": self.filtered,
            },
            "filters": {key: list(value) for key, value in sorted(self.filters.items()) if value},
            "impacted": [node.to_dict() for node in self.impacted],
        }


def _relation_allowed(
    relation: str,
    include_relations: set[str],
    exclude_relations: set[str],
) -> bool:
    if relation in exclude_relations:
        return False
    if include_relations and relation not in include_relations:
        return False
    return True


def _node_allowed(node_type: str, include_types: set[str], exclude_types: set[str]) -> bool:
    if node_type in exclude_types:
        return False
    if include_types and node_type not in include_types:
        return False
    return True


def _neighbors(
    graph: EnterpriseGraph,
    node_id: str,
    *,
    change_kind: str | None,
    include_relations: set[str],
    exclude_relations: set[str],
) -> tuple[list[tuple[str, str]], bool]:
    neighbors: list[tuple[str, str]] = []
    filtered = False
    for edge in graph.edges:
        direction = graph.effective_propagation(edge, change_kind)
        candidates: list[str] = []
        if direction in {"forward", "both"} and edge.source == node_id:
            candidates.append(edge.target)
        if direction in {"reverse", "both"} and edge.target == node_id:
            candidates.append(edge.source)
        if not candidates:
            continue
        if not _relation_allowed(edge.relation, include_relations, exclude_relations):
            filtered = True
            continue
        for target in candidates:
            neighbors.append((target, edge.relation))
    return sorted(set(neighbors), key=lambda item: (item[0], item[1])), filtered


def analyze_impact(
    graph: EnterpriseGraph,
    *,
    change_id: str | None = None,
    seeds: Iterable[str] | None = None,
    change_kind: str | None = None,
    max_depth: int | None = None,
    include_relations: Iterable[str] = (),
    exclude_relations: Iterable[str] = (),
    include_node_types: Iterable[str] = (),
    exclude_node_types: Iterable[str] = (),
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

    effective_kind = change_kind or (change.kind if change else None)
    inc_rel = set(include_relations)
    exc_rel = set(exclude_relations)
    inc_types = set(include_node_types)
    exc_types = set(exclude_node_types)
    overlap_rel = inc_rel & exc_rel
    overlap_types = inc_types & exc_types
    if overlap_rel:
        raise ValueError(f"relations cannot be both included and excluded: {', '.join(sorted(overlap_rel))}")
    if overlap_types:
        raise ValueError(f"node types cannot be both included and excluded: {', '.join(sorted(overlap_types))}")

    queue = deque()
    visited: dict[str, tuple[int, tuple[str, ...], tuple[str, ...]]] = {}
    seed_set = set(selected_seeds)
    for seed in sorted(seed_set):
        visited[seed] = (0, (seed,), ())
        queue.append(seed)

    truncated = False
    filtered = False
    while queue:
        current = queue.popleft()
        depth, path, relations = visited[current]
        next_nodes, relation_filtered = _neighbors(
            graph,
            current,
            change_kind=effective_kind,
            include_relations=inc_rel,
            exclude_relations=exc_rel,
        )
        filtered = filtered or relation_filtered
        if max_depth is not None and depth >= max_depth:
            if any(neighbor not in visited for neighbor, _ in next_nodes):
                truncated = True
            continue
        for neighbor, relation in next_nodes:
            if neighbor in visited:
                continue
            node = graph.nodes[neighbor]
            if not _node_allowed(node.type, inc_types, exc_types):
                filtered = True
                continue
            visited[neighbor] = (
                depth + 1,
                path + (neighbor,),
                relations + (relation,),
            )
            queue.append(neighbor)

    impacted: list[ImpactedNode] = []
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
        change_kind=effective_kind,
        seeds=tuple(sorted(seed_set)),
        impacted=tuple(impacted),
        truncated=truncated,
        filtered=filtered,
        filters={
            "include_relations": tuple(sorted(inc_rel)),
            "exclude_relations": tuple(sorted(exc_rel)),
            "include_node_types": tuple(sorted(inc_types)),
            "exclude_node_types": tuple(sorted(exc_types)),
        },
    )
