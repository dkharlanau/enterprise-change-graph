"""Enterprise Change Graph public API."""

from .agent import build_agent_context
from .analysis import ImpactResult, analyze_impact
from .artifact_adapters import import_process_as_code, import_reconciliation_as_code
from .composition import compose_graphs
from .coverage import CoverageAssessment, assess_coverage
from .diffing import GraphDiff, compare_graphs
from .evidence import compare_prediction, find_similar_changes, load_history
from .explain import NonImpactExplanation, explain_non_impact
from .explorer import render_explorer_html
from .exports import render_cypher, render_graphml
from .gating import GateResult, evaluate_gate
from .importers import import_catalog_csv, import_catalog_workbook, import_interface_as_code, import_mapping_as_code
from .io import dump_graph, load_graph
from .model import Change, Edge, EnterpriseGraph, GraphValidationError, Node, RelationRule
from .policy import GatePolicy, load_policy
from .quality import QualityReport, analyze_quality
from .release import ReleaseAnalysis, analyze_release
from .report import render_impact_report, render_review_report
from .review import DiffImpactReview, analyze_diff_impact

__all__ = [
    "Change", "CoverageAssessment", "DiffImpactReview", "Edge", "EnterpriseGraph",
    "GatePolicy", "GateResult", "GraphDiff", "GraphValidationError", "ImpactResult",
    "Node", "NonImpactExplanation", "QualityReport", "RelationRule", "ReleaseAnalysis",
    "analyze_diff_impact", "analyze_impact", "analyze_quality", "analyze_release",
    "assess_coverage", "build_agent_context", "compare_graphs", "compare_prediction",
    "compose_graphs", "dump_graph", "evaluate_gate", "explain_non_impact",
    "find_similar_changes", "import_catalog_csv", "import_catalog_workbook",
    "import_interface_as_code", "import_mapping_as_code", "import_process_as_code",
    "import_reconciliation_as_code", "load_graph", "load_history", "load_policy",
    "render_cypher", "render_explorer_html", "render_graphml", "render_impact_report",
    "render_review_report",
]

__version__ = "0.10.0"
