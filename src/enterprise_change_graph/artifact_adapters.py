from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .io import load_payload
from .model import EnterpriseGraph, GraphValidationError


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return value.lower() or "unknown"


def import_process_as_code(path: str | Path) -> EnterpriseGraph:
    source = Path(path)
    payload = load_payload(source)
    process = payload.get("process")
    steps = payload.get("steps", [])
    if not isinstance(process, dict):
        raise GraphValidationError(["Process-as-Code document must contain a 'process' object"])
    if not isinstance(steps, list):
        raise GraphValidationError(["Process-as-Code steps must be a list"])
    process_id = _clean(process.get("id"))
    if not process_id:
        raise GraphValidationError(["process.id must be a non-empty string"])
    name = _clean(process.get("name")) or process_id
    criticality = _clean(process.get("criticality")) or "medium"
    pid = f"process.{_slug(process_id)}"
    provenance = [source.as_posix()]
    nodes: list[dict[str, Any]] = [
        {
            "id": pid,
            "type": "process",
            "name": name,
            "criticality": criticality,
            "metadata": {"source_version": payload.get("version")},
            "provenance": provenance,
        }
    ]
    edges: list[dict[str, Any]] = []
    step_ids: set[str] = set()
    raw_by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(steps):
        if not isinstance(raw, dict):
            raise GraphValidationError([f"steps[{index}] must be an object"])
        step_id = _clean(raw.get("id"))
        if not step_id:
            raise GraphValidationError([f"steps[{index}].id must be a non-empty string"])
        if step_id in step_ids:
            raise GraphValidationError([f"duplicate process step id: {step_id}"])
        step_ids.add(step_id)
        raw_by_id[step_id] = raw
        sid = f"process-step.{_slug(process_id)}.{_slug(step_id)}"
        nodes.append(
            {
                "id": sid,
                "type": "process-step",
                "name": _clean(raw.get("name")) or step_id,
                "criticality": criticality,
                "metadata": {"step_type": _clean(raw.get("type")) or "task"},
                "provenance": provenance,
            }
        )
        edges.append(
            {
                "source": pid,
                "target": sid,
                "relation": "contains-step",
                "propagation": "forward",
                "provenance": provenance,
            }
        )
    start = _clean(process.get("start"))
    if start:
        if start not in step_ids:
            raise GraphValidationError([f"process.start references unknown step: {start}"])
        edges.append(
            {
                "source": pid,
                "target": f"process-step.{_slug(process_id)}.{_slug(start)}",
                "relation": "starts-with",
                "provenance": provenance,
            }
        )
    for step_id in sorted(step_ids):
        raw = raw_by_id[step_id]
        transitions = raw.get("transitions", [])
        if transitions is None:
            transitions = []
        if not isinstance(transitions, list):
            raise GraphValidationError([f"step {step_id} transitions must be a list"])
        for index, transition in enumerate(transitions):
            if not isinstance(transition, dict):
                raise GraphValidationError([f"step {step_id} transition[{index}] must be an object"])
            target = _clean(transition.get("to"))
            if target not in step_ids:
                raise GraphValidationError([f"step {step_id} transition references unknown step: {target}"])
            metadata = {key: value for key, value in transition.items() if key != "to"}
            edge: dict[str, Any] = {
                "source": f"process-step.{_slug(process_id)}.{_slug(step_id)}",
                "target": f"process-step.{_slug(process_id)}.{_slug(target)}",
                "relation": "flows-to",
                "provenance": provenance,
            }
            if metadata:
                edge["metadata"] = metadata
            edges.append(edge)
    return EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": nodes,
            "edges": edges,
            "relation_rules": {
                "contains-step": {"default": "forward", "change_kinds": {"decommission": "both"}},
                "flows-to": {"default": "forward", "change_kinds": {"decommission": "both"}},
            },
            "metadata": {"adapter": "process-as-code", "source": source.as_posix()},
        }
    )


def _endpoint_label(endpoint: dict[str, Any], fallback: str) -> str:
    if _clean(endpoint.get("file")):
        return _clean(endpoint.get("file"))
    if _clean(endpoint.get("table")):
        return _clean(endpoint.get("table"))
    system = _clean(endpoint.get("system"))
    obj = _clean(endpoint.get("object"))
    if system and obj:
        return f"{system}/{obj}"
    return _clean(endpoint.get("name")) or system or fallback


def import_reconciliation_as_code(path: str | Path) -> EnterpriseGraph:
    source = Path(path)
    payload = load_payload(source)
    reconciliation = payload.get("reconciliation")
    if not isinstance(reconciliation, dict):
        raise GraphValidationError(["Reconciliation-as-Code document must contain a 'reconciliation' object"])
    name = _clean(reconciliation.get("name")) or _clean(reconciliation.get("id")) or source.stem
    recon_id = _clean(reconciliation.get("id")) or _slug(name)
    criticality = _clean(reconciliation.get("criticality")) or "medium"
    rid = f"reconciliation.{_slug(recon_id)}"
    provenance = [source.as_posix()]
    nodes: list[dict[str, Any]] = [
        {"id": rid, "type": "reconciliation", "name": name, "criticality": criticality, "provenance": provenance}
    ]
    edges: list[dict[str, Any]] = []
    endpoints: dict[str, tuple[str, dict[str, Any]]] = {}
    for side in ("source", "target"):
        raw = payload.get(side, {})
        if not isinstance(raw, dict):
            raise GraphValidationError([f"{side} must be an object"])
        label = _endpoint_label(raw, side)
        eid = f"data-{side}.{_slug(label)}"
        endpoints[side] = (eid, raw)
        nodes.append(
            {
                "id": eid,
                "type": f"data-{side}",
                "name": label,
                "criticality": criticality,
                "metadata": {key: value for key, value in raw.items() if key != "key"},
                "provenance": provenance,
            }
        )
    edges.extend(
        [
            {"source": endpoints["source"][0], "target": rid, "relation": "compared-by", "propagation": "both", "provenance": provenance},
            {"source": rid, "target": endpoints["target"][0], "relation": "compares-to", "propagation": "both", "provenance": provenance},
        ]
    )
    checks = payload.get("checks", [])
    if not isinstance(checks, list):
        raise GraphValidationError(["checks must be a list"])
    for index, raw in enumerate(checks):
        if not isinstance(raw, dict):
            raise GraphValidationError([f"checks[{index}] must be an object"])
        check_id = _clean(raw.get("id")) or f"check-{index + 1}"
        cid = f"reconciliation-check.{_slug(recon_id)}.{_slug(check_id)}"
        nodes.append(
            {
                "id": cid,
                "type": "reconciliation-check",
                "name": check_id,
                "criticality": criticality,
                "metadata": {key: value for key, value in raw.items() if key not in {"id", "source", "target"}},
                "provenance": provenance,
            }
        )
        edges.append({"source": rid, "target": cid, "relation": "contains-check", "provenance": provenance})
        for side in ("source", "target"):
            field_name = _clean(raw.get(side))
            if not field_name:
                continue
            fid = f"data-field.{side}.{_slug(field_name)}"
            if not any(node["id"] == fid for node in nodes):
                nodes.append(
                    {
                        "id": fid,
                        "type": "data-field",
                        "name": f"{side}: {field_name}",
                        "criticality": criticality,
                        "metadata": {"side": side, "field": field_name},
                        "provenance": provenance,
                    }
                )
                endpoint_id = endpoints[side][0]
                relation = "contains-field"
                edges.append({"source": endpoint_id, "target": fid, "relation": relation, "propagation": "none", "provenance": provenance})
            if side == "source":
                edges.append({"source": fid, "target": cid, "relation": "checked-by", "propagation": "both", "provenance": provenance})
            else:
                edges.append({"source": cid, "target": fid, "relation": "compares-to", "propagation": "both", "provenance": provenance})
    exceptions = payload.get("exceptions")
    if isinstance(exceptions, dict) and _clean(exceptions.get("file")):
        xid = f"exception-policy.{_slug(_clean(exceptions.get('file')))}"
        nodes.append(
            {
                "id": xid,
                "type": "exception-policy",
                "name": _clean(exceptions.get("file")),
                "criticality": criticality,
                "metadata": {key: value for key, value in exceptions.items() if key != "file"},
                "provenance": provenance,
            }
        )
        edges.append({"source": rid, "target": xid, "relation": "governed-by", "provenance": provenance})
    evidence = payload.get("evidence")
    if isinstance(evidence, dict):
        eid = f"evidence.{_slug(recon_id)}"
        nodes.append(
            {
                "id": eid,
                "type": "evidence",
                "name": f"{name} evidence",
                "criticality": "low",
                "metadata": evidence,
                "provenance": provenance,
            }
        )
        edges.append({"source": rid, "target": eid, "relation": "produces-evidence", "provenance": provenance})
    return EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": nodes,
            "edges": edges,
            "metadata": {"adapter": "reconciliation-as-code", "source": source.as_posix()},
        }
    )
