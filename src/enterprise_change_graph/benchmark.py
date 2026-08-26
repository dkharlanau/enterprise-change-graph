from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

from .analysis import analyze_impact
from .model import EnterpriseGraph


@dataclass(frozen=True)
class BenchmarkResult:
    nodes: int
    edges: int
    repeats: int
    affected_nodes: int
    median_ms: float
    min_ms: float
    max_ms: float

    def to_dict(self) -> dict:
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "repeats": self.repeats,
            "affected_nodes": self.affected_nodes,
            "median_ms": round(self.median_ms, 3),
            "min_ms": round(self.min_ms, 3),
            "max_ms": round(self.max_ms, 3),
        }


def generate_benchmark_graph(node_count: int, *, fanout: int = 2) -> EnterpriseGraph:
    if node_count < 1:
        raise ValueError("node_count must be >= 1")
    if fanout < 1:
        raise ValueError("fanout must be >= 1")
    types = ("system", "data", "interface", "mapping", "process", "control", "test", "owner")
    nodes = [
        {"id": f"n{i:07d}", "type": types[i % len(types)], "name": f"Node {i}"}
        for i in range(node_count)
    ]
    edges = []
    for i in range(node_count - 1):
        for offset in range(1, fanout + 1):
            target = i + offset
            if target >= node_count:
                break
            edges.append({"source": f"n{i:07d}", "target": f"n{target:07d}", "relation": "depends-on"})
    return EnterpriseGraph.from_dict({"version": 1, "nodes": nodes, "edges": edges})


def run_benchmark(node_count: int, *, fanout: int = 2, repeats: int = 3) -> BenchmarkResult:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    graph = generate_benchmark_graph(node_count, fanout=fanout)
    timings: list[float] = []
    affected = 0
    for _ in range(repeats):
        started = time.perf_counter()
        result = analyze_impact(graph, seeds=["n0000000"])
        timings.append((time.perf_counter() - started) * 1000)
        affected = len(result.impacted)
    return BenchmarkResult(
        nodes=len(graph.nodes),
        edges=len(graph.edges),
        repeats=repeats,
        affected_nodes=affected,
        median_ms=statistics.median(timings),
        min_ms=min(timings),
        max_ms=max(timings),
    )
