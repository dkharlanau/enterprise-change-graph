from pathlib import Path

from enterprise_change_graph.analysis import analyze_impact
from enterprise_change_graph.benchmark import generate_benchmark_graph, run_benchmark
from enterprise_change_graph.contract_adapters import import_asyncapi, import_openapi
from enterprise_change_graph.junit import load_junit

ROOT = Path(__file__).parents[1]


def test_openapi_adapter_creates_operations_and_contracts():
    graph = import_openapi(ROOT / "examples" / "adapters" / "openapi.yaml")
    assert "interface.openapi.createcustomer" in graph.nodes
    assert "interface.openapi.getcustomer" in graph.nodes
    assert "data-contract.openapi.customercreate" in graph.nodes
    assert "data-contract.openapi.customer" in graph.nodes
    assert any(edge.relation == "accepts-contract" for edge in graph.edges)
    assert any(edge.relation == "returns-contract" for edge in graph.edges)


def test_asyncapi_adapter_creates_channel_operation_and_contract():
    graph = import_asyncapi(ROOT / "examples" / "adapters" / "asyncapi.yaml")
    assert "interface.asyncapi.customerchanged" in graph.nodes
    assert "interface-operation.asyncapi.sendcustomerchanged" in graph.nodes
    assert "data-contract.asyncapi.customerchanged" in graph.nodes
    assert any(node.type == "message-broker" for node in graph.nodes.values())


def test_junit_evidence_preserves_explicit_ecg_test_ids():
    evidence = load_junit(ROOT / "examples" / "adapters" / "junit.xml")
    assert len(evidence.cases) == 3
    assert evidence.failed_test_ids == ("test.otc-tax",)
    record = evidence.observed_change("CR-142", ["mapping.customer-country"])
    assert record.failed_tests == ("test.otc-tax",)
    assert record.outcome == "failed-tests"


def test_indexed_traversal_reaches_synthetic_graph():
    graph = generate_benchmark_graph(2000, fanout=2)
    result = analyze_impact(graph, seeds=["n0000000"])
    assert len(result.impacted) == 2000
    assert result.impacted[-1].path[0] == "n0000000"


def test_benchmark_harness_returns_structured_measurement():
    result = run_benchmark(1000, fanout=2, repeats=2)
    assert result.nodes == 1000
    assert result.affected_nodes == 1000
    assert result.median_ms >= 0
