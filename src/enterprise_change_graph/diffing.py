from __future__ import annotations

from dataclasses import asdict, dataclass

from .model import Change, Edge, EnterpriseGraph, Node


@dataclass(frozen=True)
class ModifiedNode:
    id: str
    before: Node
    after: Node

    def to_dict(self) -> dict:
        return {"id": self.id, "before": asdict(self.before), "after": asdict(self.after)}


@dataclass(frozen=True)
class ModifiedEdge:
    key: tuple[str, str, str]
    before: Edge
    after: Edge

    def to_dict(self) -> dict:
        return {
            "source": self.key[0],
            "target": self.key[1],
            "relation": self.key[2],
            "before": asdict(self.before),
            "after": asdict(self.after),
        }


@dataclass(frozen=True)
class ModifiedChange:
    id: str
    before: Change
    after: Change

    def to_dict(self) -> dict:
        before = asdict(self.before)
        after = asdict(self.after)
        before["seeds"] = list(before["seeds"])
        after["seeds"] = list(after["seeds"])
        return {"id": self.id, "before": before, "after": after}


@dataclass(frozen=True)
class GraphDiff:
    added_nodes: tuple[Node, ...]
    removed_nodes: tuple[Node, ...]
    modified_nodes: tuple[ModifiedNode, ...]
    added_edges: tuple[Edge, ...]
    removed_edges: tuple[Edge, ...]
    modified_edges: tuple[ModifiedEdge, ...]
    added_changes: tuple[Change, ...]
    removed_changes: tuple[Change, ...]
    modified_changes: tuple[ModifiedChange, ...]

    @property
    def impact_seeds_after(self) -> tuple[str, ...]:
        removed_ids = {node.id for node in self.removed_nodes}
        candidates = (
            {node.id for node in self.added_nodes}
            | {node.id for node in self.modified_nodes}
            | {
                endpoint
                for edge in self.added_edges
                for endpoint in (edge.source, edge.target)
            }
            | {
                endpoint
                for edge in self.removed_edges
                for endpoint in (edge.source, edge.target)
            }
            | {
                endpoint
                for edge in self.modified_edges
                for endpoint in (edge.before.source, edge.before.target)
            }
        )
        return tuple(sorted(candidates - removed_ids))

    @property
    def removed_seed_candidates(self) -> tuple[str, ...]:
        return tuple(sorted(node.id for node in self.removed_nodes))

    @property
    def is_empty(self) -> bool:
        return not any(
            (
                self.added_nodes,
                self.removed_nodes,
                self.modified_nodes,
                self.added_edges,
                self.removed_edges,
                self.modified_edges,
                self.added_changes,
                self.removed_changes,
                self.modified_changes,
            )
        )

    def to_dict(self) -> dict:
        return {
            "summary": {
                "added_nodes": len(self.added_nodes),
                "removed_nodes": len(self.removed_nodes),
                "modified_nodes": len(self.modified_nodes),
                "added_edges": len(self.added_edges),
                "removed_edges": len(self.removed_edges),
                "modified_edges": len(self.modified_edges),
                "added_changes": len(self.added_changes),
                "removed_changes": len(self.removed_changes),
                "modified_changes": len(self.modified_changes),
                "impact_seeds_after": list(self.impact_seeds_after),
                "removed_seed_candidates": list(self.removed_seed_candidates),
            },
            "nodes": {
                "added": [asdict(node) for node in self.added_nodes],
                "removed": [asdict(node) for node in self.removed_nodes],
                "modified": [node.to_dict() for node in self.modified_nodes],
            },
            "edges": {
                "added": [asdict(edge) for edge in self.added_edges],
                "removed": [asdict(edge) for edge in self.removed_edges],
                "modified": [edge.to_dict() for edge in self.modified_edges],
            },
            "changes": {
                "added": [_change_dict(change) for change in self.added_changes],
                "removed": [_change_dict(change) for change in self.removed_changes],
                "modified": [change.to_dict() for change in self.modified_changes],
            },
        }


def compare_graphs(before: EnterpriseGraph, after: EnterpriseGraph) -> GraphDiff:
    before_node_ids = set(before.nodes)
    after_node_ids = set(after.nodes)

    added_nodes = tuple(
        after.nodes[node_id] for node_id in sorted(after_node_ids - before_node_ids)
    )
    removed_nodes = tuple(
        before.nodes[node_id] for node_id in sorted(before_node_ids - after_node_ids)
    )
    modified_nodes = tuple(
        ModifiedNode(node_id, before.nodes[node_id], after.nodes[node_id])
        for node_id in sorted(before_node_ids & after_node_ids)
        if before.nodes[node_id] != after.nodes[node_id]
    )

    before_edges = {_edge_key(edge): edge for edge in before.edges}
    after_edges = {_edge_key(edge): edge for edge in after.edges}
    before_edge_keys = set(before_edges)
    after_edge_keys = set(after_edges)

    added_edges = tuple(
        after_edges[key] for key in sorted(after_edge_keys - before_edge_keys)
    )
    removed_edges = tuple(
        before_edges[key] for key in sorted(before_edge_keys - after_edge_keys)
    )
    modified_edges = tuple(
        ModifiedEdge(key, before_edges[key], after_edges[key])
        for key in sorted(before_edge_keys & after_edge_keys)
        if before_edges[key] != after_edges[key]
    )

    before_change_ids = set(before.changes)
    after_change_ids = set(after.changes)
    added_changes = tuple(
        after.changes[change_id]
        for change_id in sorted(after_change_ids - before_change_ids)
    )
    removed_changes = tuple(
        before.changes[change_id]
        for change_id in sorted(before_change_ids - after_change_ids)
    )
    modified_changes = tuple(
        ModifiedChange(change_id, before.changes[change_id], after.changes[change_id])
        for change_id in sorted(before_change_ids & after_change_ids)
        if before.changes[change_id] != after.changes[change_id]
    )

    return GraphDiff(
        added_nodes=added_nodes,
        removed_nodes=removed_nodes,
        modified_nodes=modified_nodes,
        added_edges=added_edges,
        removed_edges=removed_edges,
        modified_edges=modified_edges,
        added_changes=added_changes,
        removed_changes=removed_changes,
        modified_changes=modified_changes,
    )


def _edge_key(edge: Edge) -> tuple[str, str, str]:
    return (edge.source, edge.target, edge.relation)


def _change_dict(change: Change) -> dict:
    payload = asdict(change)
    payload["seeds"] = list(payload["seeds"])
    return payload
