from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .analysis import ImpactResult
from .model import Edge, EnterpriseGraph


@dataclass(frozen=True)
class NonImpactExplanation:
    target_id: str
    impacted: bool
    reason: str
    path: tuple[str, ...] = ()
    barrier_at: str | None = None
    barrier_relation: str | None = None
    barrier_detail: str | None = None

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "impacted": self.impacted,
            "reason": self.reason,
            "path": list(self.path),
            "barrier_at": self.barrier_at,
            "barrier_relation": self.barrier_relation,
            "barrier_detail": self.barrier_detail,
        }


def _physical_path(
    graph: EnterpriseGraph,
    seeds: tuple[str, ...],
    target_id: str,
) -> tuple[tuple[str, ...], tuple[Edge, ...]] | None:
    adjacency: dict[str, list[tuple[str, Edge]]] = {node_id: [] for node_id in graph.nodes}
    for edge in graph.edges:
        adjacency[edge.source].append((edge.target, edge))
        adjacency[edge.target].append((edge.source, edge))
    for node_id in adjacency:
        adjacency[node_id].sort(key=lambda item: (item[0], item[1].relation, item[1].source, item[1].target))

    queue = deque()
    visited: dict[str, tuple[str | None, Edge | None]] = {}
    for seed in sorted(set(seeds)):
        visited[seed] = (None, None)
        queue.append(seed)
    while queue:
        current = queue.popleft()
        if current == target_id:
            break
        for neighbor, edge in adjacency[current]:
            if neighbor in visited:
                continue
            visited[neighbor] = (current, edge)
            queue.append(neighbor)
    if target_id not in visited:
        return None

    nodes: list[str] = []
    edges: list[Edge] = []
    current: str | None = target_id
    while current is not None:
        nodes.append(current)
        previous, edge = visited[current]
        if edge is not None:
            edges.append(edge)
        current = previous
    nodes.reverse()
    edges.reverse()
    return tuple(nodes), tuple(edges)


def _direction_allows(graph: EnterpriseGraph, edge: Edge, source: str, target: str, change_kind: str | None) -> bool:
    direction = graph.effective_propagation(edge, change_kind)
    if source == edge.source and target == edge.target:
        return direction in {"forward", "both"}
    if source == edge.target and target == edge.source:
        return direction in {"reverse", "both"}
    return False


def explain_non_impact(
    graph: EnterpriseGraph,
    impact: ImpactResult,
    target_id: str,
    *,
    max_depth: int | None = None,
) -> NonImpactExplanation:
    if target_id not in graph.nodes:
        raise KeyError(f"unknown target node: {target_id}")
    impacted = {node.id: node for node in impact.impacted}
    if target_id in impacted:
        node = impacted[target_id]
        return NonImpactExplanation(
            target_id=target_id,
            impacted=True,
            reason="target is impacted",
            path=node.path,
        )

    physical = _physical_path(graph, impact.seeds, target_id)
    if physical is None:
        return NonImpactExplanation(
            target_id=target_id,
            impacted=False,
            reason="disconnected",
            barrier_detail="no graph path connects the selected seed set to the target",
        )

    path, edges = physical
    include_relations = set(impact.filters.get("include_relations", ()))
    exclude_relations = set(impact.filters.get("exclude_relations", ()))
    include_types = set(impact.filters.get("include_node_types", ()))
    exclude_types = set(impact.filters.get("exclude_node_types", ()))

    for depth, edge in enumerate(edges):
        source = path[depth]
        target = path[depth + 1]
        if max_depth is not None and depth >= max_depth:
            return NonImpactExplanation(
                target_id=target_id,
                impacted=False,
                reason="max_depth",
                path=path,
                barrier_at=source,
                barrier_relation=edge.relation,
                barrier_detail=f"max depth {max_depth} stops traversal before {target}",
            )
        if edge.relation in exclude_relations or (include_relations and edge.relation not in include_relations):
            return NonImpactExplanation(
                target_id=target_id,
                impacted=False,
                reason="relation_filter",
                path=path,
                barrier_at=source,
                barrier_relation=edge.relation,
                barrier_detail=f"relation {edge.relation!r} is excluded by the active traversal filters",
            )
        node_type = graph.nodes[target].type
        if node_type in exclude_types or (include_types and node_type not in include_types):
            return NonImpactExplanation(
                target_id=target_id,
                impacted=False,
                reason="node_type_filter",
                path=path,
                barrier_at=target,
                barrier_relation=edge.relation,
                barrier_detail=f"node type {node_type!r} is excluded and acts as a traversal barrier",
            )
        if not _direction_allows(graph, edge, source, target, impact.change_kind):
            direction = graph.effective_propagation(edge, impact.change_kind)
            return NonImpactExplanation(
                target_id=target_id,
                impacted=False,
                reason="propagation_direction",
                path=path,
                barrier_at=source,
                barrier_relation=edge.relation,
                barrier_detail=(
                    f"relation {edge.relation!r} propagates {direction!r} for change kind "
                    f"{impact.change_kind or 'unspecified'!r}; it does not propagate from {source} to {target}"
                ),
            )

    return NonImpactExplanation(
        target_id=target_id,
        impacted=False,
        reason="alternate_path_required",
        path=path,
        barrier_detail="the shortest physical path is traversable, but the target is outside the computed result; inspect alternate/cyclic paths",
    )
