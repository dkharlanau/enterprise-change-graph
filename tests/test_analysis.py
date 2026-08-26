from pathlib import Path

from enterprise_change_graph.analysis import analyze_impact
from enterprise_change_graph.io import load_graph

EXAMPLE = Path(__file__).parents[1] / "examples" / "customer-country-change.yaml"


def test_change_impact_reaches_regression_scope_and_owners():
    graph = load_graph(EXAMPLE)
    result = analyze_impact(graph, change_id="CR-142")

    ids = {node.id for node in result.impacted}

    assert len(ids) == 12
    assert "mapping.customer-country" in ids
    assert "interface.mdg-to-s4-customer" in ids
    assert "process.order-to-cash" in ids
    assert {node.id for node in result.regression_tests} == {
        "test.customer-replication",
        "test.otc-tax",
    }
    assert {node.id for node in result.owners} == {
        "owner.integration",
        "owner.master-data",
    }
    assert result.max_criticality == "critical"


def test_impact_paths_are_deterministic_and_explainable():
    graph = load_graph(EXAMPLE)
    result = analyze_impact(graph, change_id="CR-142")

    target = next(node for node in result.impacted if node.id == "test.otc-tax")

    assert target.path == (
        "mapping.customer-country",
        "data.customer.country",
        "interface.mdg-to-s4-customer",
        "system.sap-s4",
        "process.order-to-cash",
        "control.tax-determination",
        "test.otc-tax",
    )
    assert target.relations[-1] == "verified-by"


def test_max_depth_marks_result_as_truncated():
    graph = load_graph(EXAMPLE)
    result = analyze_impact(graph, change_id="CR-142", max_depth=1)

    assert {node.id for node in result.impacted} == {
        "mapping.customer-country",
        "data.customer.country",
        "system.sap-mdg",
    }
    assert result.truncated is True
