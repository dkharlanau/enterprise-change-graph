from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .analysis import ImpactResult
from .io import load_payload
from .model import GraphValidationError


@dataclass(frozen=True)
class ObservedChange:
    change_id: str
    affected_nodes: tuple[str, ...]
    incidents: tuple[str, ...] = ()
    failed_tests: tuple[str, ...] = ()
    outcome: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "change_id": self.change_id,
            "affected_nodes": list(self.affected_nodes),
            "incidents": list(self.incidents),
            "failed_tests": list(self.failed_tests),
            "outcome": self.outcome,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PredictionComparison:
    predicted_nodes: tuple[str, ...]
    observed_nodes: tuple[str, ...]
    matched_nodes: tuple[str, ...]
    missed_nodes: tuple[str, ...]
    unexpected_nodes: tuple[str, ...]

    @property
    def precision(self) -> float:
        if not self.predicted_nodes:
            return 1.0 if not self.observed_nodes else 0.0
        return len(self.matched_nodes) / len(self.predicted_nodes)

    @property
    def recall(self) -> float:
        if not self.observed_nodes:
            return 1.0
        return len(self.matched_nodes) / len(self.observed_nodes)

    def to_dict(self) -> dict:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "predicted_nodes": list(self.predicted_nodes),
            "observed_nodes": list(self.observed_nodes),
            "matched_nodes": list(self.matched_nodes),
            "missed_nodes": list(self.missed_nodes),
            "unexpected_nodes": list(self.unexpected_nodes),
        }


@dataclass(frozen=True)
class SimilarChange:
    change_id: str
    similarity: float
    shared_nodes: tuple[str, ...]
    outcome: str
    incidents: tuple[str, ...]
    failed_tests: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "change_id": self.change_id,
            "similarity": round(self.similarity, 4),
            "shared_nodes": list(self.shared_nodes),
            "outcome": self.outcome,
            "incidents": list(self.incidents),
            "failed_tests": list(self.failed_tests),
        }


def _strings(raw: object, field_name: str, errors: list[str]) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) and item for item in raw):
        errors.append(f"{field_name} must be a list of non-empty strings")
        return ()
    return tuple(sorted(set(raw)))


def load_history(path: str | Path) -> tuple[ObservedChange, ...]:
    payload = load_payload(path)
    raw_records = payload.get("records", payload.get("changes", []))
    if not isinstance(raw_records, list):
        raise GraphValidationError(["history.records must be a list"])
    errors: list[str] = []
    records: list[ObservedChange] = []
    for index, raw in enumerate(raw_records):
        prefix = f"records[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"{prefix} must be an object")
            continue
        change_id = raw.get("change_id")
        if not isinstance(change_id, str) or not change_id:
            errors.append(f"{prefix}.change_id must be a non-empty string")
            continue
        metadata = raw.get("metadata", {})
        if not isinstance(metadata, dict):
            errors.append(f"{prefix}.metadata must be an object")
            metadata = {}
        outcome = raw.get("outcome", "unknown")
        if not isinstance(outcome, str):
            errors.append(f"{prefix}.outcome must be a string")
            outcome = "unknown"
        records.append(
            ObservedChange(
                change_id=change_id,
                affected_nodes=_strings(raw.get("affected_nodes", []), f"{prefix}.affected_nodes", errors),
                incidents=_strings(raw.get("incidents", []), f"{prefix}.incidents", errors),
                failed_tests=_strings(raw.get("failed_tests", []), f"{prefix}.failed_tests", errors),
                outcome=outcome,
                metadata=metadata,
            )
        )
    if errors:
        raise GraphValidationError(errors)
    return tuple(sorted(records, key=lambda item: item.change_id))


def compare_prediction(impact: ImpactResult, observed_nodes: Iterable[str]) -> PredictionComparison:
    predicted = {node.id for node in impact.impacted}
    observed = set(observed_nodes)
    matched = predicted & observed
    return PredictionComparison(
        predicted_nodes=tuple(sorted(predicted)),
        observed_nodes=tuple(sorted(observed)),
        matched_nodes=tuple(sorted(matched)),
        missed_nodes=tuple(sorted(observed - predicted)),
        unexpected_nodes=tuple(sorted(predicted - observed)),
    )


def find_similar_changes(
    impact: ImpactResult,
    records: Iterable[ObservedChange],
    *,
    limit: int = 5,
) -> tuple[SimilarChange, ...]:
    if limit < 1:
        raise ValueError("limit must be >= 1")
    query = {node.id for node in impact.impacted}
    ranked: list[SimilarChange] = []
    for record in records:
        candidate = set(record.affected_nodes)
        union = query | candidate
        similarity = len(query & candidate) / len(union) if union else 1.0
        if similarity <= 0:
            continue
        ranked.append(
            SimilarChange(
                change_id=record.change_id,
                similarity=similarity,
                shared_nodes=tuple(sorted(query & candidate)),
                outcome=record.outcome,
                incidents=record.incidents,
                failed_tests=record.failed_tests,
            )
        )
    ranked.sort(key=lambda item: (-item.similarity, item.change_id))
    return tuple(ranked[:limit])
