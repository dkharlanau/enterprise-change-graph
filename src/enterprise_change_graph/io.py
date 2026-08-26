from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from .model import EnterpriseGraph, GraphValidationError


def load_payload(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise GraphValidationError([f"graph file does not exist: {source}"])
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise GraphValidationError([f"cannot read graph file {source}: {exc}"]) from exc
    try:
        payload = json.loads(text) if source.suffix.lower() == ".json" else yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise GraphValidationError([f"cannot parse {source}: {exc}"]) from exc
    if payload is None:
        raise GraphValidationError([f"graph file is empty: {source}"])
    if not isinstance(payload, dict):
        raise GraphValidationError(["graph document must be an object"])
    return payload


def load_graph(path: str | Path) -> EnterpriseGraph:
    return EnterpriseGraph.from_dict(load_payload(path))


def dump_graph(graph: EnterpriseGraph, path: str | Path) -> None:
    target = Path(path)
    payload = graph.to_dict()
    if target.suffix.lower() == ".json":
        target.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    else:
        target.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")
