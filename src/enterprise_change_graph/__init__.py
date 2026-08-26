"""Enterprise Change Graph public API."""

from .agent import build_agent_context
from .analysis import ImpactResult, analyze_impact
from .composition import compose_graphs
from .coverage import CoverageAssessment, assess_coverage
from .diffing import GraphDiff, compare_graphs
from .evidence import compare_prediction, find_similar_changes, load_history
from .gating import GateResult, evaluate_gate
from .importers import import_catalog_csv, import_catalog_workbook, import_interface_as_code, import_mapping_as_code
from .io import dump_graph, load_graph
from .model import Change, Edge, EnterpriseGraph, GraphValidationError, Node, RelationRule
from .policy import GatePolicy, load_policy
from .quality import QualityReport, analyze_quality
from .release import ReleaseAnalysis, analyze_release
from .report import render_impact_report, render_review_report
from .review import DiffImpactReview, analyze_diff_impact

__all__ = ["Change", "CoverageAssessment", "DiffImpactReview", "Edge", "EnterpriseGraph", "GatePolicy", "GateResult", "GraphDiff", "GraphValidationError", "ImpactResult", "Node", "QualityReport", "RelationRule", "ReleaseAnalysis", "analyze_diff_impact", "analyze_impact", "analyze_quality", "analyze_release", "assess_coverage", "build_agent_context", "compare_graphs", "compare_prediction", "compose_graphs", "dump_graph", "evaluate_gate", "find_similar_changes", "import_catalog_csv", "import_catalog_workbook", "import_interface_as_code", "import_mapping_as_code", "load_graph", "load_history", "load_policy", "render_impact_report", "render_review_report"]

__version__ = "0.9.0"
