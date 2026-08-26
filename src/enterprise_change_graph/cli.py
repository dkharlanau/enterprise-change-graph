from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent import build_agent_context
from .analysis import analyze_impact
from .composition import compose_graphs
from .coverage import assess_coverage
from .diffing import compare_graphs
from .evidence import compare_prediction, find_similar_changes, load_history
from .gating import evaluate_gate
from .importers import import_catalog_csv, import_catalog_workbook, import_interface_as_code, import_mapping_as_code
from .io import dump_graph, load_graph
from .model import GraphValidationError
from .policy import GatePolicy, load_policy
from .quality import analyze_quality
from .release import analyze_release
from .render import render_dot, render_text
from .report import render_html, render_impact_report, render_review_report
from .review import analyze_diff_impact


def _add_selector(parser: argparse.ArgumentParser) -> None:
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--change", help="Change id declared in the graph document.")
    selector.add_argument("--seed", action="append", dest="seeds", help="Seed node id. Repeat for multiple seeds.")
    parser.add_argument("--change-kind", default=None, help="Override semantic change kind for traversal rules.")


def _add_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-depth", type=int, default=None)
    parser.add_argument("--include-relation", action="append", default=[])
    parser.add_argument("--exclude-relation", action="append", default=[])
    parser.add_argument("--include-type", action="append", default=[])
    parser.add_argument("--exclude-type", action="append", default=[])


def _impact(graph, args):
    return analyze_impact(graph, change_id=getattr(args, "change", None), seeds=getattr(args, "seeds", None), change_kind=getattr(args, "change_kind", None), max_depth=getattr(args, "max_depth", None), include_relations=getattr(args, "include_relation", []), exclude_relations=getattr(args, "exclude_relation", []), include_node_types=getattr(args, "include_type", []), exclude_node_types=getattr(args, "exclude_type", []))


def _write_or_print(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def _policy_from_args(args) -> GatePolicy:
    policy = load_policy(args.policy) if getattr(args, "policy", None) else GatePolicy()
    overrides = {}
    mapping = {"max_affected": "max_affected_nodes", "min_tests": "min_tests", "min_owners": "min_owners", "fail_on_criticality": "fail_on_criticality", "max_untested": "max_untested_nodes", "max_unowned": "max_unowned_nodes"}
    for arg_name, field_name in mapping.items():
        value = getattr(args, arg_name, None)
        if value is not None: overrides[field_name] = value
    if getattr(args, "forbid_node", None) is not None: overrides["forbid_node_ids"] = tuple(sorted(set(args.forbid_node)))
    if getattr(args, "forbid_type", None) is not None: overrides["forbid_node_types"] = tuple(sorted(set(args.forbid_type)))
    if getattr(args, "require_complete", False): overrides["require_complete_traversal"] = True
    return policy.with_overrides(**overrides)


def _add_gate_policy_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--policy", help="Reusable YAML/JSON governance policy.")
    parser.add_argument("--max-affected", type=int, default=None)
    parser.add_argument("--min-tests", type=int, default=None)
    parser.add_argument("--min-owners", type=int, default=None)
    parser.add_argument("--max-untested", type=int, default=None)
    parser.add_argument("--max-unowned", type=int, default=None)
    parser.add_argument("--fail-on-criticality", choices=("low", "medium", "high", "critical"), default=None)
    parser.add_argument("--forbid-node", action="append", default=None)
    parser.add_argument("--forbid-type", action="append", default=None)
    parser.add_argument("--require-complete", action="store_true")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ecg", description="Deterministic enterprise change impact analysis and governance.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="Validate a graph document."); validate.add_argument("graph")
    impact = subparsers.add_parser("impact", help="Traverse impact from a declared change or seed nodes."); impact.add_argument("graph"); _add_selector(impact); _add_filters(impact); impact.add_argument("--format", choices=("text", "json"), default="text"); impact.add_argument("--explain", action="store_true")
    gate = subparsers.add_parser("gate", help="Evaluate deterministic governance checks against impact."); gate.add_argument("graph"); _add_selector(gate); _add_filters(gate); _add_gate_policy_args(gate); gate.add_argument("--format", choices=("text", "json"), default="text")
    dot = subparsers.add_parser("dot", help="Render Graphviz DOT."); dot.add_argument("graph"); dot.add_argument("--change")
    diff = subparsers.add_parser("diff", help="Compare graph documents and derive change seed candidates."); diff.add_argument("before"); diff.add_argument("after"); diff.add_argument("--format", choices=("text", "json"), default="text")
    review = subparsers.add_parser("review", help="Removal-aware before/after impact review."); review.add_argument("before"); review.add_argument("after"); _add_filters(review); review.add_argument("--format", choices=("text", "json", "markdown"), default="text"); review.add_argument("--output")
    compose = subparsers.add_parser("compose", help="Compose multiple graph fragments with provenance."); compose.add_argument("graphs", nargs="+"); compose.add_argument("--namespace", action="append", default=[], metavar="PATH=PREFIX"); compose.add_argument("--output", required=True)
    csv_cmd = subparsers.add_parser("import-csv", help="Import Nodes/Edges/Changes CSV catalogs."); csv_cmd.add_argument("nodes"); csv_cmd.add_argument("--edges"); csv_cmd.add_argument("--changes"); csv_cmd.add_argument("--output", required=True)
    xlsx_cmd = subparsers.add_parser("import-xlsx", help="Import an Excel workbook with Nodes/Edges/Changes sheets."); xlsx_cmd.add_argument("workbook"); xlsx_cmd.add_argument("--output", required=True)
    interface_cmd = subparsers.add_parser("import-interface", help="Import an Interface-as-Code document."); interface_cmd.add_argument("source"); interface_cmd.add_argument("--output", required=True)
    mapping_cmd = subparsers.add_parser("import-mapping", help="Import a Mapping-as-Code document."); mapping_cmd.add_argument("source"); mapping_cmd.add_argument("--output", required=True)
    quality = subparsers.add_parser("quality", help="Diagnose graph coverage and maintainability gaps."); quality.add_argument("graph"); quality.add_argument("--format", choices=("text", "json"), default="text")
    report = subparsers.add_parser("report", help="Generate a deterministic impact report."); report.add_argument("graph"); _add_selector(report); _add_filters(report); _add_gate_policy_args(report); report.add_argument("--format", choices=("markdown", "html", "json"), default="markdown"); report.add_argument("--output")
    release = subparsers.add_parser("release", help="Analyze a bundle of changes and detect collisions."); release.add_argument("graph"); release.add_argument("--change", action="append", required=True); release.add_argument("--max-depth", type=int, default=None); release.add_argument("--format", choices=("text", "json"), default="text")
    observe = subparsers.add_parser("observe", help="Compare predicted impact with an observed historical record."); observe.add_argument("graph"); observe.add_argument("--change", required=True); observe.add_argument("--history", required=True); observe.add_argument("--record", help="History record change id; defaults to --change.")
    similar = subparsers.add_parser("similar", help="Find previous changes with overlapping affected subgraphs."); similar.add_argument("graph"); similar.add_argument("--change", required=True); similar.add_argument("--history", required=True); similar.add_argument("--limit", type=int, default=5)
    context = subparsers.add_parser("context", help="Emit compact agent/MCP-ready change context as JSON."); context.add_argument("graph"); _add_selector(context); _add_filters(context); _add_gate_policy_args(context)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "diff":
            before = load_graph(args.before); after = load_graph(args.after); diff = compare_graphs(before, after)
            if args.format == "json": print(json.dumps(diff.to_dict(), indent=2, sort_keys=True))
            else:
                summary = diff.to_dict()["summary"]; print("Graph diff"); print(f"Nodes: added={summary['added_nodes']}, removed={summary['removed_nodes']}, modified={summary['modified_nodes']}"); print(f"Edges: added={summary['added_edges']}, removed={summary['removed_edges']}, modified={summary['modified_edges']}"); print(f"Changes: added={summary['added_changes']}, removed={summary['removed_changes']}, modified={summary['modified_changes']}"); print(f"Impact seeds in before graph: {', '.join(diff.impact_seeds_before) or 'none'}"); print(f"Impact seeds in after graph: {', '.join(diff.impact_seeds_after) or 'none'}"); print(f"Removed-node seed candidates: {', '.join(diff.removed_seed_candidates) or 'none'}")
            return 0
        if args.command == "review":
            review = analyze_diff_impact(load_graph(args.before), load_graph(args.after), max_depth=args.max_depth, include_relations=args.include_relation, exclude_relations=args.exclude_relation, include_node_types=args.include_type, exclude_node_types=args.exclude_type)
            if args.format == "json": text = json.dumps(review.to_dict(), indent=2, sort_keys=True) + "\n"
            elif args.format == "markdown": text = render_review_report(review)
            else: text = f"Diff impact: affected={len(review.affected_node_ids)}, tests={len(review.regression_tests)}, owners={len(review.owners)}, max-criticality={review.max_criticality or 'none'}\nBefore seeds: {', '.join(review.diff.impact_seeds_before) or 'none'}\nAfter seeds: {', '.join(review.diff.impact_seeds_after) or 'none'}\n"
            _write_or_print(text, args.output); return 0
        if args.command == "compose":
            namespaces: dict[str, str] = {}
            for raw in args.namespace:
                if "=" not in raw: raise ValueError("--namespace must use PATH=PREFIX")
                path, prefix = raw.split("=", 1)
                if not path or not prefix: raise ValueError("--namespace must use non-empty PATH=PREFIX")
                namespaces[path] = prefix
            graph = compose_graphs(args.graphs, namespaces=namespaces); dump_graph(graph, args.output); print(f"OK: composed nodes={len(graph.nodes)}, edges={len(graph.edges)}, changes={len(graph.changes)} -> {args.output}"); return 0
        if args.command == "import-csv":
            graph = import_catalog_csv(args.nodes, edges_path=args.edges, changes_path=args.changes); dump_graph(graph, args.output); print(f"OK: imported nodes={len(graph.nodes)}, edges={len(graph.edges)}, changes={len(graph.changes)} -> {args.output}"); return 0
        if args.command == "import-xlsx":
            graph = import_catalog_workbook(args.workbook); dump_graph(graph, args.output); print(f"OK: imported nodes={len(graph.nodes)}, edges={len(graph.edges)}, changes={len(graph.changes)} -> {args.output}"); return 0
        if args.command == "import-interface":
            graph = import_interface_as_code(args.source); dump_graph(graph, args.output); print(f"OK: interface adapter produced nodes={len(graph.nodes)}, edges={len(graph.edges)} -> {args.output}"); return 0
        if args.command == "import-mapping":
            graph = import_mapping_as_code(args.source); dump_graph(graph, args.output); print(f"OK: mapping adapter produced nodes={len(graph.nodes)}, edges={len(graph.edges)} -> {args.output}"); return 0

        graph = load_graph(args.graph)
        if args.command == "validate": print(f"OK: version={graph.version}, nodes={len(graph.nodes)}, edges={len(graph.edges)}, changes={len(graph.changes)}, relation-rules={len(graph.relation_rules)}"); return 0
        if args.command == "impact":
            result = _impact(graph, args); print(json.dumps(result.to_dict(), indent=2, sort_keys=True) if args.format == "json" else render_text(result, explain=args.explain)); return 0
        if args.command == "gate":
            impact = _impact(graph, args); coverage = assess_coverage(graph, impact); policy = _policy_from_args(args); gate = evaluate_gate(impact, coverage=coverage, **policy.to_dict())
            if args.format == "json": print(json.dumps({"policy": policy.to_dict(), **gate.to_dict()}, indent=2, sort_keys=True))
            elif gate.passed: print(f"PASS: affected={len(impact.impacted)}, tests={len(impact.regression_tests)}, owners={len(impact.owners)}, untested={len(coverage.untested_nodes)}, unowned={len(coverage.unowned_nodes)}, max-criticality={impact.max_criticality or 'none'}")
            else:
                print(f"FAIL: {len(gate.violations)} gate violation(s)")
                for violation in gate.violations: print(f"- {violation}")
            return 0 if gate.passed else 3
        if args.command == "dot":
            highlighted: set[str] = set()
            if args.change: highlighted = {node.id for node in analyze_impact(graph, change_id=args.change).impacted}
            print(render_dot(graph, highlighted=highlighted)); return 0
        if args.command == "quality":
            quality = analyze_quality(graph)
            if args.format == "json": print(json.dumps(quality.to_dict(), indent=2, sort_keys=True))
            else:
                print("Graph quality diagnostics")
                for key, value in quality.to_dict()["summary"].items(): print(f"- {key}: {value}")
                if quality.high_criticality_without_tests: print("High/critical without tests: " + ", ".join(quality.high_criticality_without_tests))
                if quality.high_criticality_without_owners: print("High/critical without owners: " + ", ".join(quality.high_criticality_without_owners))
            return 0
        if args.command == "report":
            impact = _impact(graph, args); coverage = assess_coverage(graph, impact); gate = None; policy = None
            if args.policy or any(getattr(args, name, None) is not None for name in ("max_affected", "min_tests", "min_owners", "max_untested", "max_unowned", "fail_on_criticality")) or args.forbid_node is not None or args.forbid_type is not None or args.require_complete:
                policy = _policy_from_args(args); gate = evaluate_gate(impact, coverage=coverage, **policy.to_dict())
            if args.format == "json":
                payload = {"impact": impact.to_dict(), "coverage": coverage.to_dict()}
                if policy: payload["policy"] = policy.to_dict()
                if gate: payload["gate"] = gate.to_dict()
                text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
            else:
                markdown = render_impact_report(impact, coverage=coverage, gate=gate); text = render_html(markdown) if args.format == "html" else markdown
            _write_or_print(text, args.output); return 0 if not gate or gate.passed else 3
        if args.command == "release":
            release = analyze_release(graph, args.change, max_depth=args.max_depth)
            if args.format == "json": print(json.dumps(release.to_dict(), indent=2, sort_keys=True))
            else:
                print(f"Release changes: {len(release.change_ids)}"); print(f"Collision nodes: {len(release.collisions)}")
                for node, changes in release.collisions.items(): print(f"- {node}: {', '.join(changes)}")
                print("Regression tests: " + (", ".join(release.regression_tests) or "none")); print("Approval owners: " + (", ".join(release.owners) or "none"))
            return 0
        if args.command == "observe":
            impact = analyze_impact(graph, change_id=args.change); records = load_history(args.history); record_id = args.record or args.change; record = next((item for item in records if item.change_id == record_id), None)
            if record is None: raise KeyError(f"history record not found: {record_id}")
            print(json.dumps(compare_prediction(impact, record.affected_nodes).to_dict(), indent=2, sort_keys=True)); return 0
        if args.command == "similar":
            impact = analyze_impact(graph, change_id=args.change); matches = find_similar_changes(impact, load_history(args.history), limit=args.limit); print(json.dumps({"matches": [match.to_dict() for match in matches]}, indent=2, sort_keys=True)); return 0
        if args.command == "context":
            impact = _impact(graph, args); coverage = assess_coverage(graph, impact); policy = _policy_from_args(args); gate = evaluate_gate(impact, coverage=coverage, **policy.to_dict()); print(json.dumps(build_agent_context(impact, coverage=coverage, gate=gate), indent=2, sort_keys=True)); return 0
    except (GraphValidationError, KeyError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
