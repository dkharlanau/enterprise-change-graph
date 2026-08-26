from pathlib import Path

from enterprise_change_graph.analysis import analyze_impact
from enterprise_change_graph.gating import evaluate_gate
from enterprise_change_graph.io import load_graph

EXAMPLE = Path(__file__).parents[1] / "examples" / "customer-country-change.yaml"


def test_gate_passes_when_required_coverage_exists():
    impact = analyze_impact(load_graph(EXAMPLE), change_id="CR-142")

    gate = evaluate_gate(
        impact,
        max_affected_nodes=20,
        min_tests=2,
        min_owners=2,
    )

    assert gate.passed is True
    assert gate.violations == ()


def test_gate_reports_all_policy_violations_deterministically():
    impact = analyze_impact(load_graph(EXAMPLE), change_id="CR-142")

    gate = evaluate_gate(
        impact,
        max_affected_nodes=5,
        min_tests=3,
        min_owners=3,
        fail_on_criticality="critical",
        forbid_node_ids=["system.sap-s4"],
        forbid_node_types=["control"],
    )

    assert gate.passed is False
    assert len(gate.violations) == 6
    assert gate.violations[0] == "affected nodes 12 exceeds maximum 5"
    assert "system.sap-s4" in gate.violations[4]
    assert "control" in gate.violations[5]


def test_gate_rejects_invalid_numeric_policy():
    impact = analyze_impact(load_graph(EXAMPLE), change_id="CR-142")

    import pytest

    with pytest.raises(ValueError):
        evaluate_gate(impact, min_tests=-1)
