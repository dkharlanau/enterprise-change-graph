from __future__ import annotations

from .analysis import ImpactResult
from .model import EnterpriseGraph


def render_text(result: ImpactResult, *, explain: bool = False) -> str:
    heading = (
        f"{result.change_id} — {result.change_title}"
        if result.change_id
        else "Ad-hoc impact analysis"
    )
    lines = [
        f"Impact: {heading}",
        f"Seeds: {', '.join(result.seeds)}",
        f"Affected nodes: {len(result.impacted)}",
        "By type: "
        + (
            ", ".join(f"{key}={value}" for key, value in result.by_type.items())
            or "none"
        ),
        "By criticality: "
        + (
            ", ".join(
                f"{key}={value}" for key, value in result.by_criticality.items()
            )
            or "none"
        ),
        f"Maximum criticality: {result.max_criticality or 'none'}",
        "Regression tests: "
        + (", ".join(node.id for node in result.regression_tests) or "none"),
        "Owners: " + (", ".join(node.id for node in result.owners) or "none"),
    ]
    if result.truncated:
        lines.append("Traversal: truncated by max depth")

    if explain:
        lines.append("")
        lines.append("Explanation paths:")
        for node in result.impacted:
            if node.depth == 0:
                detail = "(seed)"
            else:
                segments = [node.path[0]]
                for relation, target in zip(node.relations, node.path[1:]):
                    segments.append(f"-[{relation}]-> {target}")
                detail = " ".join(segments)
            lines.append(
                f"- {node.id} [{node.type}, {node.criticality}, depth={node.depth}]: "
                f"{detail}"
            )

    return "\n".join(lines)


def render_dot(graph: EnterpriseGraph, *, highlighted: set[str] | None = None) -> str:
    highlighted = highlighted or set()
    lines = [
        "digraph enterprise_change_graph {",
        '  rankdir="LR";',
        '  graph [fontname="Arial"];',
        '  node [shape="box", fontname="Arial"];',
        '  edge [fontname="Arial"];',
    ]

    for node in sorted(graph.nodes.values(), key=lambda item: item.id):
        label = f"{node.name}\\n[{node.type}]"
        attrs = [f'label="{_escape(label)}"']
        if node.id in highlighted:
            attrs.extend(['style="bold"', 'penwidth="2"'])
        lines.append(f'  "{_escape(node.id)}" [{", ".join(attrs)}];')

    for edge in sorted(
        graph.edges,
        key=lambda item: (item.source, item.target, item.relation, item.propagation),
    ):
        if edge.propagation == "none":
            continue
        attrs = [f'label="{_escape(edge.relation)}"']
        if edge.propagation == "reverse":
            attrs.append('dir="back"')
        elif edge.propagation == "both":
            attrs.append('dir="both"')
        lines.append(
            f'  "{_escape(edge.source)}" -> "{_escape(edge.target)}" '
            f'[{", ".join(attrs)}];'
        )

    lines.append("}")
    return "\n".join(lines)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
