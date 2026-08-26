from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from typing import Iterable

from .model import Change, EnterpriseGraph

CRITICALITY_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class _Trace:
    node_id: str
    parent: "_Trace | None" = None
    relation: str | None = None

    def materialize(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        nodes: list[str] = []
        relations: list[str] = []
        current: _Trace | None = self
        while current is not None:
            nodes.append(current.node_id)
            if current.relation is not None:
                relations.append(current.relation)
            current = current.parent
        nodes.reverse()
        relations.reverse()
        return tuple(nodes), tuple(relations)


@dataclass(frozen=True)
class ImpactedNode:
    id: str
    type: str
    name: str
    criticality: str
    depth: int
    _trace: _Trace = field(repr=False, compare=False)

    @property
    def path(self) -> tuple[str, ...]:
        return self._trace.materialize()[0]

    @property
    def relations(self) -> tuple[str, ...]:
        return self._trace.materialize()[1]

    def to_dict(self) -> dict:
        path, relations = self._trace.materialize()
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "criticality": self.criticality,
            "depth": self.depth,
            "path": list(path),
            "relations": list(relations),
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


def _relation_allowed(relation: str, include_relations: set[str], exclude_relations: set[str]) -> bool:
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


def _build_adjacency(
    graph: EnterpriseGraph,
    *,
    change_kind: str | None,
    include_relations: set[str],
    exclude_relations: set[str],
) -> tuple[dict[str, tuple[tuple[str, str], ...]], set[str]]:
    """Build one deterministic O(E) traversal index for the analysis."""
    allowed: dict[str, set[tuple[str, str]]] = {node_id: set() for node_id in graph.nodes}
    blocked_relation_sources: set[str] = set()
    for edge in graph.edges:
        direction = graph.effective_propagation(edge, change_kind)
        candidates: list[tuple[str, str]] = []
        if direction in {"forward", "both"}:
            candidates.append((edge.source, edge.target))
        if direction in {"reverse", "both"}:
            candidates.append((edge.target, edge.source))
        if not candidates:
            continue
        if not _relation_allowed(edge.relation, include_relations, exclude_relations):
            blocked_relation_sources.update(source for source, _ in candidates)
            continue
        for source, target in candidates:
            allowed[source].add((target, edge.relation))
    return (
        {
            node_id: tuple(sorted(neighbors, key=lambda item: (item[0], item[1])))
            for node_id, neighbors in allowed.items()
        },
        blocked_relation_sources,
    )


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

    adjacency, blocked_relation_sources = _build_adjacency(
        graph,
        change_kind=effective_kind,
        include_relations=inc_rel,
        exclude_relations=exc_rel,
    )

    queue = deque()
    visited: dict[str, tuple[int, _Trace]] = {}
    seed_set = set(selected_seeds)
    for seed in sorted(seed_set):
        trace = _Trace(seed)
        visited[seed] = (0, trace)
        queue.append(seed)

    truncated = False
    filtered = False
    while queue:
        current = queue.popleft()
        depth, trace = visited[current]
        if current in blocked_relation_sources:
            filtered = True
        next_nodes = adjacency[current]
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
                _Trace(neighbor, parent=trace, relation=relation),
            )
            queue.append(neighbor)

    impacted: list[ImpactedNode] = []
    for node_id, (depth, trace) in visited.items():
        node = graph.nodes[node_id]
        impacted.append(
            ImpactedNode(
                id=node.id,
                type=node.type,
                name=node.name,
                criticality=node.criticality,
                depth=depth,
                _trace=trace,
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
