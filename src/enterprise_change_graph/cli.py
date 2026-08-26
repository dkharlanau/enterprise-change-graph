from __future__ import annotations

import argparse
import json
import sys

from .analysis import analyze_impact
from .diffing import compare_graphs
from .gating import evaluate_gate
from .io import load_graph
from .model import GraphValidationError
from .render import render_dot, render_text


def _add_selector(parser: argparse.ArgumentParser) -> None:
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--change", help="Change id declared in the graph document.")
    selector.add_argument(
        "--seed",
        action="append",
        dest="seeds",
        help="Seed node id. Repeat for multiple seeds.",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecg",
        description="Deterministic impact analysis for enterprise change graphs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a graph document.")
    validate.add_argument("graph")

    impact = subparsers.add_parser(
        "impact",
        help="Traverse propagation edges from a change or explicit seed nodes.",
    )
    impact.add_argument("graph")
    _add_selector(impact)
    impact.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Limit traversal depth. Seeds are depth 0.",
    )
    impact.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    impact.add_argument(
        "--explain",
        action="store_true",
        help="Include a shortest deterministic explanation path for every affected node.",
    )

    gate = subparsers.add_parser(
        "gate",
        help="Evaluate deterministic CI policy checks against an impact set.",
    )
    gate.add_argument("graph")
    _add_selector(gate)
    gate.add_argument("--max-depth", type=int, default=None)
    gate.add_argument("--max-affected", type=int, default=None)
    gate.add_argument("--min-tests", type=int, default=0)
    gate.add_argument("--min-owners", type=int, default=0)
    gate.add_argument(
        "--fail-on-criticality",
        choices=("low", "medium", "high", "critical"),
        default=None,
        help="Fail if any impacted node is at or above this criticality.",
    )
    gate.add_argument(
        "--forbid-node",
        action="append",
        default=[],
        help="Fail if this node id is impacted. Repeatable.",
    )
    gate.add_argument(
        "--forbid-type",
        action="append",
        default=[],
        help="Fail if this node type is impacted. Repeatable.",
    )
    gate.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )

    dot = subparsers.add_parser(
        "dot",
        help="Render Graphviz DOT. Optionally highlight a change impact set.",
    )
    dot.add_argument("graph")
    dot.add_argument("--change", help="Change id to highlight.")

    diff = subparsers.add_parser(
        "diff",
        help="Compare two graph documents and derive impact seed candidates.",
    )
    diff.add_argument("before")
    diff.add_argument("after")
    diff.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    try:
        if args.command == "diff":
            before = load_graph(args.before)
            after = load_graph(args.after)
            diff = compare_graphs(before, after)
            if args.format == "json":
                print(json.dumps(diff.to_dict(), indent=2, sort_keys=True))
            else:
                summary = diff.to_dict()["summary"]
                print("Graph diff")
                print(
                    "Nodes: "
                    f"added={summary['added_nodes']}, "
                    f"removed={summary['removed_nodes']}, "
                    f"modified={summary['modified_nodes']}"
                )
                print(
                    "Edges: "
                    f"added={summary['added_edges']}, "
                    f"removed={summary['removed_edges']}, "
                    f"modified={summary['modified_edges']}"
                )
                print(
                    "Changes: "
                    f"added={summary['added_changes']}, "
                    f"removed={summary['removed_changes']}, "
                    f"modified={summary['modified_changes']}"
                )
                seeds = ", ".join(diff.impact_seeds_after) or "none"
                removed = ", ".join(diff.removed_seed_candidates) or "none"
                print(f"Impact seeds in after graph: {seeds}")
                print(f"Removed-node seed candidates: {removed}")
            return 0

        graph = load_graph(args.graph)

        if args.command == "validate":
            print(
                f"OK: version={graph.version}, nodes={len(graph.nodes)}, "
                f"edges={len(graph.edges)}, changes={len(graph.changes)}"
            )
            return 0

        if args.command == "impact":
            result = analyze_impact(
                graph,
                change_id=args.change,
                seeds=args.seeds,
                max_depth=args.max_depth,
            )
            if args.format == "json":
                print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            else:
                print(render_text(result, explain=args.explain))
            return 0

        if args.command == "gate":
            impact = analyze_impact(
                graph,
                change_id=args.change,
                seeds=args.seeds,
                max_depth=args.max_depth,
            )
            gate = evaluate_gate(
                impact,
                max_affected_nodes=args.max_affected,
                min_tests=args.min_tests,
                min_owners=args.min_owners,
                fail_on_criticality=args.fail_on_criticality,
                forbid_node_ids=args.forbid_node,
                forbid_node_types=args.forbid_type,
            )
            if args.format == "json":
                print(json.dumps(gate.to_dict(), indent=2, sort_keys=True))
            elif gate.passed:
                print(
                    f"PASS: affected={len(impact.impacted)}, "
                    f"tests={len(impact.regression_tests)}, "
                    f"owners={len(impact.owners)}, "
                    f"max-criticality={impact.max_criticality or 'none'}"
                )
            else:
                print(f"FAIL: {len(gate.violations)} gate violation(s)")
                for violation in gate.violations:
                    print(f"- {violation}")
            return 0 if gate.passed else 3

        if args.command == "dot":
            highlighted: set[str] = set()
            if args.change:
                result = analyze_impact(graph, change_id=args.change)
                highlighted = {node.id for node in result.impacted}
            print(render_dot(graph, highlighted=highlighted))
            return 0

    except (GraphValidationError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
