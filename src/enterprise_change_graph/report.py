from __future__ import annotations

from html import escape

from .analysis import ImpactResult, ImpactedNode
from .coverage import CoverageAssessment
from .gating import GateResult
from .review import DiffImpactReview


def _path(node: ImpactedNode) -> str:
    if node.depth == 0:
        return node.id + " (seed)"
    parts = [node.path[0]]
    for relation, target in zip(node.relations, node.path[1:]):
        parts.append(f"-[{relation}]-> {target}")
    return " ".join(parts)


def render_impact_report(impact: ImpactResult, *, coverage: CoverageAssessment | None = None, gate: GateResult | None = None) -> str:
    title = impact.change_id or "Ad-hoc impact analysis"
    if impact.change_title:
        title += f" — {impact.change_title}"
    lines = [f"# Enterprise Change Impact — {title}", "", "## Decision summary", "", f"- Change kind: `{impact.change_kind or 'unspecified'}`", f"- Seeds: {', '.join(f'`{seed}`' for seed in impact.seeds)}", f"- Affected nodes: **{len(impact.impacted)}**", f"- Maximum criticality: **{impact.max_criticality or 'none'}**", f"- Regression tests discovered: **{len(impact.regression_tests)}**", f"- Owners discovered: **{len(impact.owners)}**"]
    if impact.truncated:
        lines.append("- Traversal: **TRUNCATED by max depth**")
    if impact.filtered:
        lines.append("- Traversal: **FILTERED**")
    if gate:
        lines.append(f"- Governance gate: **{'PASS' if gate.passed else 'FAIL'}**")
    lines += ["", "## Impact by type", ""]
    if impact.by_type:
        for key, value in impact.by_type.items(): lines.append(f"- `{key}`: {value}")
    else: lines.append("- none")
    material = [node for node in impact.impacted if node.criticality in {"critical", "high"}]
    lines += ["", "## Critical and high impact", ""]
    if material:
        lines += ["| Node | Type | Criticality | Why impacted |", "|---|---|---|---|"]
        for node in material: lines.append(f"| `{node.id}` | {node.type} | {node.criticality} | `{_path(node)}` |")
    else: lines.append("No critical or high nodes are impacted.")
    lines += ["", "## Regression scope", ""]
    if coverage:
        tests = coverage.minimal_regression_tests or tuple(node.id for node in impact.regression_tests)
        lines.append("Minimal deterministic test set:")
        if tests: lines.extend(f"- `{test}`" for test in tests)
        else: lines.append("- none")
        lines += ["", f"Test coverage: **{coverage.test_coverage_ratio:.1%}** of eligible impacted nodes"]
        if coverage.untested_nodes:
            lines += ["", "Untested impact gaps:"]
            lines.extend(f"- `{node}`" for node in coverage.untested_nodes)
    else:
        tests = [node.id for node in impact.regression_tests]
        lines.extend(f"- `{test}`" for test in tests)
        if not tests: lines.append("- none")
    lines += ["", "## Ownership and approvals", ""]
    if coverage:
        owners = coverage.minimal_owners or tuple(node.id for node in impact.owners)
        if owners: lines.extend(f"- `{owner}`" for owner in owners)
        else: lines.append("- none")
        lines += ["", f"Owner coverage: **{coverage.owner_coverage_ratio:.1%}** of eligible impacted nodes"]
        if coverage.unowned_nodes:
            lines += ["", "Unowned impact gaps:"]
            lines.extend(f"- `{node}`" for node in coverage.unowned_nodes)
    else:
        owners = [node.id for node in impact.owners]
        if owners: lines.extend(f"- `{owner}`" for owner in owners)
        else: lines.append("- none")
    if gate:
        lines += ["", "## Governance gate", ""]
        if gate.passed: lines.append("**PASS** — no policy violations.")
        else:
            lines.append(f"**FAIL** — {len(gate.violations)} violation(s):")
            lines.extend(f"- {violation}" for violation in gate.violations)
    lines += ["", "## Explanation paths", ""]
    for node in impact.impacted: lines.append(f"- `{node.id}`: `{_path(node)}`")
    return "\n".join(lines) + "\n"


def render_review_report(review: DiffImpactReview) -> str:
    diff = review.diff; summary = diff.to_dict()["summary"]
    lines = ["# Enterprise Change Graph — Diff Impact Review", "", "## Change surface", "", f"- Nodes: +{summary['added_nodes']} / -{summary['removed_nodes']} / ~{summary['modified_nodes']}", f"- Edges: +{summary['added_edges']} / -{summary['removed_edges']} / ~{summary['modified_edges']}", f"- Declared changes: +{summary['added_changes']} / -{summary['removed_changes']} / ~{summary['modified_changes']}", f"- Before-side seeds: {', '.join(f'`{x}`' for x in diff.impact_seeds_before) or 'none'}", f"- After-side seeds: {', '.join(f'`{x}`' for x in diff.impact_seeds_after) or 'none'}", "", "## Combined impact", "", f"- Affected nodes: **{len(review.affected_node_ids)}**", f"- Maximum criticality: **{review.max_criticality or 'none'}**", f"- Regression tests: {', '.join(f'`{x}`' for x in review.regression_tests) or 'none'}", f"- Owners: {', '.join(f'`{x}`' for x in review.owners) or 'none'}"]
    if review.before_impact:
        lines += ["", "## Before-side impact (deletions/removals)", ""]
        lines.extend(f"- `{node.id}` — {node.type}, {node.criticality}: `{_path(node)}`" for node in review.before_impact.impacted)
    if review.after_impact:
        lines += ["", "## After-side impact (additions/modifications)", ""]
        lines.extend(f"- `{node.id}` — {node.type}, {node.criticality}: `{_path(node)}`" for node in review.after_impact.impacted)
    return "\n".join(lines) + "\n"


def render_html(markdown_report: str) -> str:
    return "<!doctype html><html><head><meta charset='utf-8'><title>Enterprise Change Impact</title><style>body{font-family:system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 24px;}pre{white-space:pre-wrap;line-height:1.45}</style></head><body><pre>" + escape(markdown_report) + "</pre></body></html>"
