from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .analysis import CRITICALITY_ORDER, ImpactResult, analyze_impact
from .diffing import GraphDiff, compare_graphs
from .model import EnterpriseGraph


@dataclass(frozen=True)
class DiffImpactReview:
    diff: GraphDiff
    before_impact: ImpactResult | None
    after_impact: ImpactResult | None

    @property
    def affected_node_ids(self) -> tuple[str, ...]:
        ids: set[str] = set()
        if self.before_impact:
            ids.update(node.id for node in self.before_impact.impacted)
        if self.after_impact:
            ids.update(node.id for node in self.after_impact.impacted)
        return tuple(sorted(ids))

    @property
    def regression_tests(self) -> tuple[str, ...]:
        ids: set[str] = set()
        for result in (self.before_impact, self.after_impact):
            if result:
                ids.update(node.id for node in result.regression_tests)
        return tuple(sorted(ids))

    @property
    def owners(self) -> tuple[str, ...]:
        ids: set[str] = set()
        for result in (self.before_impact, self.after_impact):
            if result:
                ids.update(node.id for node in result.owners)
        return tuple(sorted(ids))

    @property
    def max_criticality(self) -> str | None:
        levels = [
            result.max_criticality
            for result in (self.before_impact, self.after_impact)
            if result and result.max_criticality
        ]
        if not levels:
            return None
        return max(levels, key=lambda level: CRITICALITY_ORDER[level])

    def to_dict(self) -> dict:
        return {
            "summary": {
                "affected_nodes": len(self.affected_node_ids),
                "affected_node_ids": list(self.affected_node_ids),
                "regression_tests": list(self.regression_tests),
                "owners": list(self.owners),
                "max_criticality": self.max_criticality,
                "before_seeds": list(self.diff.impact_seeds_before),
                "after_seeds": list(self.diff.impact_seeds_after),
            },
            "diff": self.diff.to_dict(),
            "before_impact": self.before_impact.to_dict() if self.before_impact else None,
            "after_impact": self.after_impact.to_dict() if self.after_impact else None,
        }


def analyze_diff_impact(
    before: EnterpriseGraph,
    after: EnterpriseGraph,
    *,
    max_depth: int | None = None,
    include_relations: Iterable[str] = (),
    exclude_relations: Iterable[str] = (),
    include_node_types: Iterable[str] = (),
    exclude_node_types: Iterable[str] = (),
) -> DiffImpactReview:
    diff = compare_graphs(before, after)
    common = dict(
        max_depth=max_depth,
        include_relations=include_relations,
        exclude_relations=exclude_relations,
        include_node_types=include_node_types,
        exclude_node_types=exclude_node_types,
    )
    before_impact = (
        analyze_impact(before, seeds=diff.impact_seeds_before, change_kind="decommission", **common)
        if diff.impact_seeds_before
        else None
    )
    after_impact = (
        analyze_impact(after, seeds=diff.impact_seeds_after, change_kind="graph-change", **common)
        if diff.impact_seeds_after
        else None
    )
    return DiffImpactReview(diff=diff, before_impact=before_impact, after_impact=after_impact)
