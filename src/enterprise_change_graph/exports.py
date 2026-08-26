from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

from .model import EnterpriseGraph


def render_graphml(graph: EnterpriseGraph) -> str:
    ns = "http://graphml.graphdrawing.org/xmlns"
    ET.register_namespace("", ns)
    root = ET.Element(f"{{{ns}}}graphml")
    for key_id, name in (("type", "type"), ("name", "name"), ("criticality", "criticality"), ("metadata", "metadata"), ("provenance", "provenance")):
        ET.SubElement(root, f"{{{ns}}}key", id=key_id, **{"for": "node"}, attr_name=name, attr_type="string")
    ET.SubElement(root, f"{{{ns}}}key", id="relation", **{"for": "edge"}, attr_name="relation", attr_type="string")
    ET.SubElement(root, f"{{{ns}}}key", id="propagation", **{"for": "edge"}, attr_name="propagation", attr_type="string")
    graph_el = ET.SubElement(root, f"{{{ns}}}graph", id="enterprise-change-graph", edgedefault="directed")
    for node in sorted(graph.nodes.values(), key=lambda item: item.id):
        node_el = ET.SubElement(graph_el, f"{{{ns}}}node", id=node.id)
        values = {
            "type": node.type,
            "name": node.name,
            "criticality": node.criticality,
            "metadata": json.dumps(node.metadata, sort_keys=True, separators=(",", ":")),
            "provenance": json.dumps(list(node.provenance), separators=(",", ":")),
        }
        for key, value in values.items():
            data_el = ET.SubElement(node_el, f"{{{ns}}}data", key=key)
            data_el.text = value
    for index, edge in enumerate(sorted(graph.edges, key=lambda item: (item.source, item.target, item.relation))):
        edge_el = ET.SubElement(graph_el, f"{{{ns}}}edge", id=f"e{index}", source=edge.source, target=edge.target)
        relation_el = ET.SubElement(edge_el, f"{{{ns}}}data", key="relation")
        relation_el.text = edge.relation
        propagation_el = ET.SubElement(edge_el, f"{{{ns}}}data", key="propagation")
        propagation_el.text = edge.propagation
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def _cypher_literal(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _relationship_type(relation: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]+", "_", relation.upper()).strip("_")
    return normalized or "RELATED_TO"


def render_cypher(graph: EnterpriseGraph) -> str:
    lines = ["// Enterprise Change Graph deterministic Cypher export"]
    for node in sorted(graph.nodes.values(), key=lambda item: item.id):
        metadata = json.dumps(node.metadata, sort_keys=True, separators=(",", ":"))
        provenance = json.dumps(list(node.provenance), separators=(",", ":"))
        lines.append(
            "MERGE (n:ECGNode {id: " + _cypher_literal(node.id) + "}) "
            "SET n.type = " + _cypher_literal(node.type) + ", n.name = " + _cypher_literal(node.name) +
            ", n.criticality = " + _cypher_literal(node.criticality) + ", n.metadata_json = " + _cypher_literal(metadata) +
            ", n.provenance_json = " + _cypher_literal(provenance) + ";"
        )
    for edge in sorted(graph.edges, key=lambda item: (item.source, item.target, item.relation)):
        rel_type = _relationship_type(edge.relation)
        lines.append(
            "MATCH (a:ECGNode {id: " + _cypher_literal(edge.source) + "}), (b:ECGNode {id: " + _cypher_literal(edge.target) + "}) "
            f"MERGE (a)-[r:{rel_type}]->(b) SET r.relation = " + _cypher_literal(edge.relation) +
            ", r.propagation = " + _cypher_literal(edge.propagation) + ";"
        )
    return "\n".join(lines) + "\n"
