from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Iterable, Mapping

from .io import load_payload
from .model import Change, Edge, EnterpriseGraph, GraphValidationError, Node, RelationRule


def _merge_provenance(*groups: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({item for group in groups for item in group}))


def _with_source(graph: EnterpriseGraph, source: str, namespace: str | None) -> EnterpriseGraph:
    def ident(value: str) -> str:
        return f"{namespace}.{value}" if namespace else value

    nodes = {
        ident(node.id): replace(
            node,
            id=ident(node.id),
            provenance=_merge_provenance(node.provenance, (source,)),
        )
        for node in graph.nodes.values()
    }
    edges = [
        replace(
            edge,
            source=ident(edge.source),
            target=ident(edge.target),
            provenance=_merge_provenance(edge.provenance, (source,)),
        )
        for edge in graph.edges
    ]
    changes = {
        ident(change.id): replace(
            change,
            id=ident(change.id),
            seeds=tuple(ident(seed) for seed in change.seeds),
            provenance=_merge_provenance(change.provenance, (source,)),
        )
        for change in graph.changes.values()
    }
    return EnterpriseGraph(
        nodes=nodes,
        edges=edges,
        changes=changes,
        version=graph.version,
        relation_rules=graph.relation_rules,
        metadata=graph.metadata,
    )


def _same_node(a: Node, b: Node) -> bool:
    return replace(a, provenance=()) == replace(b, provenance=())


def _same_edge(a: Edge, b: Edge) -> bool:
    return replace(a, provenance=()) == replace(b, provenance=())


def _same_change(a: Change, b: Change) -> bool:
    return replace(a, provenance=()) == replace(b, provenance=())


def compose_graphs(
    paths: Iterable[str | Path],
    *,
    namespaces: Mapping[str, str] | None = None,
) -> EnterpriseGraph:
    source_paths = [Path(path) for path in paths]
    if not source_paths:
        raise GraphValidationError(["at least one graph file is required for composition"])

    namespaces = namespaces or {}
    nodes: dict[str, Node] = {}
    edges: dict[tuple[str, str, str], Edge] = {}
    changes: dict[str, Change] = {}
    relation_rules: dict[str, RelationRule] = {}
    errors: list[str] = []

    for path in source_paths:
        source = path.as_posix()
        namespace = namespaces.get(str(path)) or namespaces.get(source)
        fragment = _with_source(
            EnterpriseGraph.from_dict(load_payload(path), validate_references=False), source, namespace
        )

        for relation, rule in sorted(fragment.relation_rules.items()):
            existing = relation_rules.get(relation)
            if existing is None:
                relation_rules[relation] = rule
            elif existing != rule:
                errors.append(f"relation rule conflict for {relation!r} between composed fragments")

        for node in sorted(fragment.nodes.values(), key=lambda item: item.id):
            existing = nodes.get(node.id)
            if existing is None:
                nodes[node.id] = node
            elif _same_node(existing, node):
                nodes[node.id] = replace(
                    existing,
                    provenance=_merge_provenance(existing.provenance, node.provenance),
                )
            else:
                errors.append(f"node conflict for {node.id!r}; use a namespace or align definitions")

        for edge in sorted(fragment.edges, key=lambda item: (item.source, item.target, item.relation)):
            key = (edge.source, edge.target, edge.relation)
            existing = edges.get(key)
            if existing is None:
                edges[key] = edge
            elif _same_edge(existing, edge):
                edges[key] = replace(
                    existing,
                    provenance=_merge_provenance(existing.provenance, edge.provenance),
                )
            else:
                errors.append(
                    "edge conflict for "
                    f"{edge.source!r} -> {edge.target!r} [{edge.relation!r}]"
                )

        for change in sorted(fragment.changes.values(), key=lambda item: item.id):
            existing = changes.get(change.id)
            if existing is None:
                changes[change.id] = change
            elif _same_change(existing, change):
                changes[change.id] = replace(
                    existing,
                    provenance=_merge_provenance(existing.provenance, change.provenance),
                )
            else:
                errors.append(f"change conflict for {change.id!r}; use a namespace or align definitions")

    if errors:
        raise GraphValidationError(errors)

    merged = EnterpriseGraph(
        nodes=dict(sorted(nodes.items())),
        edges=[edges[key] for key in sorted(edges)],
        changes=dict(sorted(changes.items())),
        version=1,
        relation_rules=dict(sorted(relation_rules.items())),
        metadata={"composed_from": [path.as_posix() for path in source_paths]},
    )
    return EnterpriseGraph.from_dict(merged.to_dict())
