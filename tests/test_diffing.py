from enterprise_change_graph.diffing import compare_graphs
from enterprise_change_graph.model import EnterpriseGraph


def _graph(nodes, edges=None, changes=None):
    return EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": nodes,
            "edges": edges or [],
            "changes": changes or [],
        }
    )


def test_diff_derives_added_and_modified_nodes_as_after_seeds():
    before = _graph(
        [
            {"id": "a", "type": "data", "criticality": "medium"},
            {"id": "old", "type": "system"},
        ]
    )
    after = _graph(
        [
            {"id": "a", "type": "data", "criticality": "high"},
            {"id": "new", "type": "interface"},
        ]
    )

    diff = compare_graphs(before, after)

    assert diff.impact_seeds_after == ("a", "new")
    assert diff.removed_seed_candidates == ("old",)
    assert [item.id for item in diff.modified_nodes] == ["a"]


def test_diff_detects_edge_semantic_change_without_treating_it_as_add_remove():
    nodes = [{"id": "a", "type": "data"}, {"id": "b", "type": "process"}]
    before = _graph(
        nodes,
        [{"source": "a", "target": "b", "relation": "used-by", "propagation": "forward"}],
    )
    after = _graph(
        nodes,
        [{"source": "a", "target": "b", "relation": "used-by", "propagation": "both"}],
    )

    diff = compare_graphs(before, after)

    assert len(diff.modified_edges) == 1
    assert not diff.added_edges
    assert not diff.removed_edges
    assert diff.impact_seeds_after == ("a", "b")


def test_identical_graphs_have_empty_diff():
    graph = _graph([{"id": "a", "type": "data"}])

    assert compare_graphs(graph, graph).is_empty is True
