from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

ALLOWED_PROPAGATION = {"forward", "reverse", "both", "none"}
ALLOWED_CRITICALITY = {"low", "medium", "high", "critical"}


class GraphValidationError(ValueError):
    """Raised when a graph or policy document is structurally invalid."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _provenance(raw: Any, prefix: str, errors: list[str]) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str) and raw:
        return (raw,)
    if isinstance(raw, list) and all(isinstance(item, str) and item for item in raw):
        return tuple(dict.fromkeys(raw))
    errors.append(f"{prefix}.provenance must be a string or list of non-empty strings")
    return ()


@dataclass(frozen=True)
class Node:
    id: str
    type: str
    name: str
    criticality: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": self.id, "type": self.type, "name": self.name}
        if self.criticality != "medium":
            payload["criticality"] = self.criticality
        if self.metadata:
            payload["metadata"] = self.metadata
        if self.provenance:
            payload["provenance"] = list(self.provenance)
        return payload


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    relation: str
    propagation: str = "forward"
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
        }
        if self.propagation != "forward":
            payload["propagation"] = self.propagation
        if self.metadata:
            payload["metadata"] = self.metadata
        if self.provenance:
            payload["provenance"] = list(self.provenance)
        return payload


@dataclass(frozen=True)
class Change:
    id: str
    title: str
    seeds: tuple[str, ...]
    description: str = ""
    kind: str = "change"
    metadata: dict[str, Any] = field(default_factory=dict)
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "seeds": list(self.seeds),
        }
        if self.description:
            payload["description"] = self.description
        if self.kind != "change":
            payload["kind"] = self.kind
        if self.metadata:
            payload["metadata"] = self.metadata
        if self.provenance:
            payload["provenance"] = list(self.provenance)
        return payload


@dataclass(frozen=True)
class RelationRule:
    default: str = "forward"
    change_kinds: dict[str, str] = field(default_factory=dict)

    def direction_for(self, change_kind: str | None, edge_default: str) -> str:
        if change_kind and change_kind in self.change_kinds:
            return self.change_kinds[change_kind]
        return self.default if self.default else edge_default

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"default": self.default}
        if self.change_kinds:
            payload["change_kinds"] = dict(sorted(self.change_kinds.items()))
        return payload


@dataclass
class EnterpriseGraph:
    nodes: dict[str, Node]
    edges: list[Edge]
    changes: dict[str, Change]
    version: int = 1
    relation_rules: dict[str, RelationRule] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, validate_references: bool = True) -> "EnterpriseGraph":
        if not isinstance(payload, dict):
            raise GraphValidationError(["graph document must be an object"])

        errors: list[str] = []
        version = payload.get("version", 1)
        if version != 1:
            errors.append(f"unsupported version: {version!r}; expected 1")

        raw_nodes = payload.get("nodes", [])
        raw_edges = payload.get("edges", [])
        raw_changes = payload.get("changes", [])
        raw_rules = payload.get("relation_rules", {})
        metadata = payload.get("metadata", {})

        if not isinstance(raw_nodes, list):
            errors.append("nodes must be a list")
            raw_nodes = []
        if not isinstance(raw_edges, list):
            errors.append("edges must be a list")
            raw_edges = []
        if not isinstance(raw_changes, list):
            errors.append("changes must be a list")
            raw_changes = []
        if not isinstance(raw_rules, dict):
            errors.append("relation_rules must be an object")
            raw_rules = {}
        if not isinstance(metadata, dict):
            errors.append("metadata must be an object")
            metadata = {}

        relation_rules: dict[str, RelationRule] = {}
        for relation, raw in sorted(raw_rules.items()):
            prefix = f"relation_rules.{relation}"
            if not isinstance(relation, str) or not relation:
                errors.append("relation rule keys must be non-empty strings")
                continue
            if isinstance(raw, str):
                raw = {"default": raw}
            if not isinstance(raw, dict):
                errors.append(f"{prefix} must be an object or propagation string")
                continue
            default = raw.get("default", "forward")
            if default not in ALLOWED_PROPAGATION:
                errors.append(f"{prefix}.default must be one of {sorted(ALLOWED_PROPAGATION)}")
                continue
            by_kind = raw.get("change_kinds", {})
            if not isinstance(by_kind, dict):
                errors.append(f"{prefix}.change_kinds must be an object")
                continue
            clean: dict[str, str] = {}
            for kind, direction in sorted(by_kind.items()):
                if not isinstance(kind, str) or not kind:
                    errors.append(f"{prefix}.change_kinds keys must be non-empty strings")
                    continue
                if direction not in ALLOWED_PROPAGATION:
                    errors.append(
                        f"{prefix}.change_kinds.{kind} must be one of {sorted(ALLOWED_PROPAGATION)}"
                    )
                    continue
                clean[kind] = direction
            relation_rules[relation] = RelationRule(default=default, change_kinds=clean)

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
                errors.append(f"{prefix}.criticality must be one of {sorted(ALLOWED_CRITICALITY)}")
                continue
            name = raw.get("name", node_id)
            if not isinstance(name, str) or not name.strip():
                errors.append(f"{prefix}.name must be a non-empty string")
                continue
            node_metadata = raw.get("metadata", {})
            if not isinstance(node_metadata, dict):
                errors.append(f"{prefix}.metadata must be an object")
                continue
            nodes[node_id] = Node(
                id=node_id,
                type=node_type,
                name=name,
                criticality=criticality,
                metadata=node_metadata,
                provenance=_provenance(raw.get("provenance"), prefix, errors),
            )

        edges: list[Edge] = []
        seen_edges: set[tuple[str, str, str]] = set()
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
                errors.append(f"{prefix}.propagation must be one of {sorted(ALLOWED_PROPAGATION)}")
                continue
            key = (source, target, relation)
            if key in seen_edges:
                errors.append(f"duplicate edge: {source} -> {target} [{relation}]")
                continue
            seen_edges.add(key)
            edge_metadata = raw.get("metadata", {})
            if not isinstance(edge_metadata, dict):
                errors.append(f"{prefix}.metadata must be an object")
                continue
            edges.append(
                Edge(
                    source=source,
                    target=target,
                    relation=relation,
                    propagation=propagation,
                    metadata=edge_metadata,
                    provenance=_provenance(raw.get("provenance"), prefix, errors),
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
            if not isinstance(seeds, list) or not seeds or not all(isinstance(seed, str) and seed for seed in seeds):
                errors.append(f"{prefix}.seeds must be a non-empty list of node ids")
                continue
            description = raw.get("description", "")
            if not isinstance(description, str):
                errors.append(f"{prefix}.description must be a string")
                continue
            kind = raw.get("kind", "change")
            if not isinstance(kind, str) or not kind:
                errors.append(f"{prefix}.kind must be a non-empty string")
                continue
            change_metadata = raw.get("metadata", {})
            if not isinstance(change_metadata, dict):
                errors.append(f"{prefix}.metadata must be an object")
                continue
            changes[change_id] = Change(
                id=change_id,
                title=title,
                seeds=tuple(seeds),
                description=description,
                kind=kind,
                metadata=change_metadata,
                provenance=_provenance(raw.get("provenance"), prefix, errors),
            )

        if validate_references:
            for index, edge in enumerate(edges):
                if edge.source not in nodes:
                    errors.append(f"edges[{index}].source references unknown node: {edge.source}")
                if edge.target not in nodes:
                    errors.append(f"edges[{index}].target references unknown node: {edge.target}")
            for change in changes.values():
                for seed in change.seeds:
                    if seed not in nodes:
                        errors.append(f"change {change.id} references unknown seed node: {seed}")

        if errors:
            raise GraphValidationError(errors)
        return cls(
            nodes=nodes,
            edges=edges,
            changes=changes,
            version=version,
            relation_rules=relation_rules,
            metadata=metadata,
        )

    def effective_propagation(self, edge: Edge, change_kind: str | None = None) -> str:
        rule = self.relation_rules.get(edge.relation)
        if not rule:
            return edge.propagation
        if change_kind and change_kind in rule.change_kinds:
            return rule.change_kinds[change_kind]
        if edge.propagation != "forward":
            return edge.propagation
        return rule.default

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version": self.version,
            "nodes": [node.to_dict() for node in sorted(self.nodes.values(), key=lambda n: n.id)],
            "edges": [
                edge.to_dict()
                for edge in sorted(self.edges, key=lambda e: (e.source, e.target, e.relation))
            ],
        }
        if self.changes:
            payload["changes"] = [
                change.to_dict() for change in sorted(self.changes.values(), key=lambda c: c.id)
            ]
        if self.relation_rules:
            payload["relation_rules"] = {
                name: rule.to_dict() for name, rule in sorted(self.relation_rules.items())
            }
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload
