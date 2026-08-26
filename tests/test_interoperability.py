from pathlib import Path
import xml.etree.ElementTree as ET

from enterprise_change_graph.analysis import analyze_impact
from enterprise_change_graph.artifact_adapters import import_process_as_code, import_reconciliation_as_code
from enterprise_change_graph.explain import explain_non_impact
from enterprise_change_graph.explorer import render_explorer_html
from enterprise_change_graph.exports import render_cypher, render_graphml
from enterprise_change_graph.io import load_graph
from enterprise_change_graph.model import EnterpriseGraph

ROOT = Path(__file__).parents[1]


def test_process_as_code_adapter_matches_v02_shape():
    graph = import_process_as_code(ROOT / "examples" / "adapters" / "process-minimal.yaml")
    assert "process.order-release" in graph.nodes
    assert "process-step.order-release.validate" in graph.nodes
    flows = {(edge.source, edge.target) for edge in graph.edges if edge.relation == "flows-to"}
    assert ("process-step.order-release.validate", "process-step.order-release.release") in flows
    assert ("process-step.order-release.validate", "process-step.order-release.reject") in flows


def test_reconciliation_adapter_maps_checks_fields_policy_and_evidence():
    graph = import_reconciliation_as_code(ROOT / "examples" / "adapters" / "reconciliation.yaml")
    assert "reconciliation.customer-migration" in graph.nodes
    assert any(node.type == "reconciliation-check" for node in graph.nodes.values())
    assert any(node.type == "data-field" for node in graph.nodes.values())
    assert any(node.type == "exception-policy" for node in graph.nodes.values())
    assert any(node.type == "evidence" for node in graph.nodes.values())


def test_why_not_explains_propagation_direction():
    graph = EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": [{"id": "a", "type": "data"}, {"id": "b", "type": "process"}],
            "edges": [{"source": "a", "target": "b", "relation": "used-by", "propagation": "forward"}],
        }
    )
    impact = analyze_impact(graph, seeds=["b"])
    explanation = explain_non_impact(graph, impact, "a")
    assert not explanation.impacted
    assert explanation.reason == "propagation_direction"
    assert explanation.path == ("b", "a")


def test_why_not_explains_relation_filter():
    graph = EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": [{"id": "a", "type": "data"}, {"id": "b", "type": "process"}],
            "edges": [{"source": "a", "target": "b", "relation": "used-by"}],
        }
    )
    impact = analyze_impact(graph, seeds=["a"], exclude_relations=["used-by"])
    explanation = explain_non_impact(graph, impact, "b")
    assert explanation.reason == "relation_filter"


def test_graphml_export_is_valid_xml_and_preserves_nodes():
    graph = load_graph(ROOT / "examples" / "customer-country-change.yaml")
    text = render_graphml(graph)
    root = ET.fromstring(text)
    nodes = root.findall(".//{http://graphml.graphdrawing.org/xmlns}node")
    assert len(nodes) == len(graph.nodes)


def test_cypher_export_has_stable_node_and_relationship_statements():
    graph = load_graph(ROOT / "examples" / "customer-country-change.yaml")
    text = render_cypher(graph)
    assert "MERGE (n:ECGNode" in text
    assert "MERGE (a)-[r:TRANSFORMS]->(b)" in text


def test_static_explorer_embeds_graph_and_change_highlights():
    graph = load_graph(ROOT / "examples" / "customer-country-change.yaml")
    html = render_explorer_html(graph, change_id="CR-142")
    assert "Static, dependency-free explorer" in html
    assert "mapping.customer-country" in html
    assert '"change":"CR-142"' in html
