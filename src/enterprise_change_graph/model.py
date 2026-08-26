from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ALLOWED_PROPAGATION = {"forward", "reverse", "both", "none"}
ALLOWED_CRITICALITY = {"low", "medium", "high", "critical"}


class GraphValidationError(ValueError):
    """Raised when a graph document is structurally invalid."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    name: str
    criticality: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    propagation: str = "forward"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Change:
    id: str
    title: str
    seeds: tuple[str, ...]
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EnterpriseGraph:
    nodes: dict[str, Node]
    edges: list[Edge]
    changes: dict[str, Change]
    version: int = 1

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EnterpriseGraph":
        if not isinstance(payload, dict):
            raise GraphValidationError(["graph document must be an object"])

        errors: list[str] = []
        version = payload.get("version", 1)
        if version != 1:
            errors.append(f"unsupported version: {version!r}; expected 1")

        raw_nodes = payload.get("nodes", [])
        raw_edges = payload.get("edges", [])
        raw_changes = payload.get("changes", [])

        if not isinstance(raw_nodes, list):
            errors.append("nodes must be a list")
            raw_nodes = []
        if not isinstance(raw_edges, list):
            errors.append("edges must be a list")
            raw_edges = []
        if not isinstance(raw_changes, list):
            errors.append("changes must be a list")
            raw_changes = []

        nodes: dict[str, Node] = {}
        for index, raw in enumerate(raw_nodes):
            prefix = f"nodes[{index}]"
            if not isinstance(raw, dict):
                errors.append(f"{prefix} must be an object")
                continue
            node_id = raw.get("id")
            node_type = raw.get("type")
            if not isinstance(node_id, str) or not node_id.strip():
                errors.append(f"{prefix}.id must be a non-empty string")
                continue
            if node_id in nodes:
                errors.append(f"duplicate node id: {node_id}")
                continue
            if not isinstance(node_type, str) or not node_type.strip():
                errors.append(f"{prefix}.type must be a non-empty string")
                continue
            criticality = raw.get("criticality", "medium")
            if criticality not in ALLOWED_CRITICALITY:
                errors.append(
                    f"{prefix}.criticality must be one of {sorted(ALLOWED_CRITICALITY)}"
                )
                continue
            name = raw.get("name", node_id)
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{prefix}.name must be a non-empty string")
                continue
            metadata = raw.get("metadata", {})
            if not isinstance(metadata, dict):
                errors.append(f"{prefix}.metadata must be an object")
                continue
            nodes[node_id] = Node(
                id=node_id,
                type=node_type,
                name=name,
                criticality=criticality,
                metadata=metadata,
            )

        edges: list[Edge] = []
        for index, raw in enumerate(raw_edges):
            prefix = f"edges[{index}]"
            if not isinstance(raw, dict):
                errors.append(f"{prefix} must be an object")
                continue
            source = raw.get("source")
            target = raw.get("target")
            relation = raw.get("relation")
            propagation = raw.get("propagation", "forward")
            if not isinstance(source, str) or not source:
                errors.append(f"{prefix}.source must be a non-empty string")
                continue
            if not isinstance(target, str) or not target:
                errors.append(f"{prefix}.target must be a non-empty string")
                continue
            if not isinstance(relation, str) or not relation:
                errors.append(f"{prefix}.relation must be a non-empty string")
                continue
            if propagation not in ALLOWED_PROPAGATION:
                errors.append(
                    f"{prefix}.propagation must be one of {sorted(ALLOWED_PROPAGATION)}"
                )
                continue
            metadata = raw.get("metadata", {})
            if not isinstance(metadata, dict):
                errors.append(f"{prefix}.metadata must be an object")
                continue
            edges.append(
                Edge(
                    source=source,
                    target=target,
                    relation=relation,
                    propagation=propagation,
                    metadata=metadata,
                )
            )

        changes: dict[str, Change] = {}
        for index, raw in enumerate(raw_changes):
            prefix = f"changes[{index}]"
            if not isinstance(raw, dict):
                errors.append(f"{prefix} must be an object")
                continue
            change_id = raw.get("id")
            title = raw.get("title")
            seeds = raw.get("seeds")
            if not isinstance(change_id, str) or not change_id:
                errors.append(f"{prefix}.id must be a non-empty string")
                continue
            if change_id in changes:
                errors.append(f"duplicate change id: {change_id}")
                continue
            if not isinstance(title, str) or not title:
                errors.append(f"{prefix}.title must be a non-empty string")
                continue
            if (
                not isinstance(seeds, list)
                or not seeds
                or not all(isinstance(seed, str) and seed for seed in seeds)
            ):
                errors.append(f"{prefix}.seeds must be a non-empty list of node ids")
                continue
            metadata = raw.get("metadata", {})
            if not isinstance(metadata, dict):
                errors.append(f"{prefix}.metadata must be an object")
                continue
            description = raw.get("description", "")
            if not isinstance(description, str):
                errors.append(f"{prefix}.description must be a string")
                continue
            changes[change_id] = Change(
                id=change_id,
                title=title,
                seeds=tuple(seeds),
                description=description,
                metadata=metadata,
            )

        for index, edge in enumerate(edges):
            if edge.source not in nodes:
                errors.append(
                    f"edges[{index}].source references unknown node: {edge.source}"
                )
            if edge.target not in nodes:
                errors.append(
                    f"edges[{index}].target references unknown node: {edge.target}"
                )

        for change in changes.values():
            for seed in change.seeds:
                if seed not in nodes:
                    errors.append(
                        f"change {change.id} references unknown seed node: {seed}"
                    )

        if errors:
            raise GraphValidationError(errors)

        return cls(nodes=nodes, edges=edges, changes=changes, version=version)
