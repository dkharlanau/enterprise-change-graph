import pytest

from enterprise_change_graph.model import EnterpriseGraph, GraphValidationError


def test_rejects_unknown_edge_references():
    payload = {
        "version": 1,
        "nodes": [{"id": "a", "type": "data"}],
        "edges": [{"source": "a", "target": "missing", "relation": "uses"}],
    }

    with pytest.raises(GraphValidationError) as error:
        EnterpriseGraph.from_dict(payload)

    assert "references unknown node: missing" in str(error.value)


def test_rejects_unknown_change_seed():
    payload = {
        "version": 1,
        "nodes": [{"id": "a", "type": "data"}],
        "edges": [],
        "changes": [{"id": "CR-1", "title": "Test", "seeds": ["missing"]}],
    }

    with pytest.raises(GraphValidationError) as error:
        EnterpriseGraph.from_dict(payload)

    assert "references unknown seed node: missing" in str(error.value)


def test_reverse_propagation_can_model_dependency_direction():
    payload = {
        "version": 1,
        "nodes": [
            {"id": "consumer", "type": "process"},
            {"id": "provider", "type": "interface"},
        ],
        "edges": [
            {
                "source": "consumer",
                "target": "provider",
                "relation": "depends-on",
                "propagation": "reverse",
            }
        ],
        "changes": [{"id": "CR-1", "title": "Provider change", "seeds": ["provider"]}],
    }

    graph = EnterpriseGraph.from_dict(payload)

    from enterprise_change_graph.analysis import analyze_impact

    result = analyze_impact(graph, change_id="CR-1")
    assert {node.id for node in result.impacted} == {"provider", "consumer"}
