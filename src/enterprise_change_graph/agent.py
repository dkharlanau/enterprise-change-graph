from __future__ import annotations

from .analysis import ImpactResult
from .coverage import CoverageAssessment
from .gating import GateResult


def build_agent_context(impact: ImpactResult, *, coverage: CoverageAssessment | None = None, gate: GateResult | None = None) -> dict:
    payload = {
        "change": {"id": impact.change_id, "title": impact.change_title, "kind": impact.change_kind, "seeds": list(impact.seeds)},
        "impact": impact.to_dict()["summary"],
        "material_nodes": [{"id": node.id, "type": node.type, "criticality": node.criticality, "path": list(node.path), "relations": list(node.relations)} for node in impact.impacted if node.criticality in {"high", "critical"}],
    }
    if coverage:
        payload["coverage"] = {"test_coverage_ratio": round(coverage.test_coverage_ratio, 4), "owner_coverage_ratio": round(coverage.owner_coverage_ratio, 4), "minimal_regression_tests": list(coverage.minimal_regression_tests), "minimal_owners": list(coverage.minimal_owners), "untested_nodes": list(coverage.untested_nodes), "unowned_nodes": list(coverage.unowned_nodes)}
    if gate:
        payload["gate"] = {"passed": gate.passed, "violations": list(gate.violations)}
    return payload
