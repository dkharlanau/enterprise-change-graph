from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from .io import load_payload
from .model import EnterpriseGraph, GraphValidationError

_HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace", "query"}


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return value.lower() or "unknown"


def _refs(value: Any) -> tuple[str, ...]:
    found: set[str] = set()
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            ref = current.get("$ref")
            if isinstance(ref, str) and ref:
                found.add(ref)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return tuple(sorted(found))


def _contract_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1] if "/" in ref else ref


def import_openapi(path: str | Path) -> EnterpriseGraph:
    source = Path(path)
    payload = load_payload(source)
    version = _clean(payload.get("openapi"))
    if not version.startswith("3."):
        raise GraphValidationError(["OpenAPI adapter supports OpenAPI 3.x documents"])
    info = payload.get("info")
    paths = payload.get("paths")
    if not isinstance(info, dict) or not isinstance(paths, dict):
        raise GraphValidationError(["OpenAPI document requires info and paths objects"])
    title = _clean(info.get("title")) or source.stem
    api_id = f"api.openapi.{_slug(title)}"
    provenance = [source.as_posix()]
    nodes: list[dict[str, Any]] = [
        {
            "id": api_id,
            "type": "api",
            "name": title,
            "metadata": {"openapi": version, "api_version": info.get("version")},
            "provenance": provenance,
        }
    ]
    edges: list[dict[str, Any]] = []
    node_ids = {api_id}

    servers = payload.get("servers", [])
    if isinstance(servers, list):
        for index, raw in enumerate(servers):
            if not isinstance(raw, dict) or not _clean(raw.get("url")):
                continue
            url = _clean(raw.get("url"))
            sid = f"endpoint.openapi.{_slug(url)}"
            if sid not in node_ids:
                nodes.append(
                    {
                        "id": sid,
                        "type": "endpoint",
                        "name": _clean(raw.get("description")) or url,
                        "metadata": {"url": url, "server_index": index},
                        "provenance": provenance,
                    }
                )
                node_ids.add(sid)
            edges.append({"source": sid, "target": api_id, "relation": "serves", "propagation": "both", "provenance": provenance})

    contract_nodes: set[str] = set()
    for route in sorted(paths):
        item = paths[route]
        if not isinstance(item, dict):
            continue
        for method in sorted(key for key in item if key.lower() in _HTTP_METHODS):
            operation = item[method]
            if not isinstance(operation, dict):
                continue
            operation_id = _clean(operation.get("operationId")) or f"{method}-{route}"
            oid = f"interface.openapi.{_slug(operation_id)}"
            nodes.append(
                {
                    "id": oid,
                    "type": "interface",
                    "name": _clean(operation.get("summary")) or operation_id,
                    "metadata": {
                        "method": method.upper(),
                        "path": route,
                        "operation_id": operation_id,
                        "tags": operation.get("tags", []),
                        "deprecated": bool(operation.get("deprecated", False)),
                    },
                    "provenance": provenance,
                }
            )
            edges.append({"source": api_id, "target": oid, "relation": "contains-operation", "provenance": provenance})

            request_refs = _refs(operation.get("requestBody"))
            response_refs = _refs(operation.get("responses"))
            for relation, refs, reverse in (("accepts-contract", request_refs, True), ("returns-contract", response_refs, False)):
                for ref in refs:
                    contract = _contract_name(ref)
                    cid = f"data-contract.openapi.{_slug(contract)}"
                    if cid not in contract_nodes:
                        nodes.append(
                            {
                                "id": cid,
                                "type": "data-contract",
                                "name": contract,
                                "metadata": {"ref": ref},
                                "provenance": provenance,
                            }
                        )
                        contract_nodes.add(cid)
                    if reverse:
                        edges.append({"source": cid, "target": oid, "relation": relation, "propagation": "both", "provenance": provenance})
                    else:
                        edges.append({"source": oid, "target": cid, "relation": relation, "propagation": "both", "provenance": provenance})

    if len(nodes) == 1 and not paths:
        raise GraphValidationError(["OpenAPI document contains no paths"])
    return EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": nodes,
            "edges": edges,
            "metadata": {"adapter": "openapi", "source": source.as_posix(), "source_version": version},
        }
    )


def _async_message_contracts(channel: dict[str, Any]) -> tuple[str, ...]:
    contracts: set[str] = set()
    messages = channel.get("messages")
    if isinstance(messages, dict):
        for name, message in messages.items():
            if isinstance(message, dict):
                ref = message.get("$ref")
                contracts.add(_contract_name(ref) if isinstance(ref, str) and ref else str(name))
    for action in ("publish", "subscribe"):
        operation = channel.get(action)
        if not isinstance(operation, dict):
            continue
        message = operation.get("message")
        if isinstance(message, dict):
            ref = message.get("$ref")
            if isinstance(ref, str) and ref:
                contracts.add(_contract_name(ref))
            elif _clean(message.get("name")):
                contracts.add(_clean(message.get("name")))
    return tuple(sorted(contracts))


def import_asyncapi(path: str | Path) -> EnterpriseGraph:
    source = Path(path)
    payload = load_payload(source)
    version = _clean(payload.get("asyncapi"))
    if not version or version.split(".", 1)[0] not in {"2", "3"}:
        raise GraphValidationError(["AsyncAPI adapter supports AsyncAPI 2.x and 3.x documents"])
    info = payload.get("info")
    channels = payload.get("channels")
    if not isinstance(info, dict) or not isinstance(channels, dict):
        raise GraphValidationError(["AsyncAPI document requires info and channels objects"])
    title = _clean(info.get("title")) or source.stem
    api_id = f"api.asyncapi.{_slug(title)}"
    provenance = [source.as_posix()]
    nodes: list[dict[str, Any]] = [
        {
            "id": api_id,
            "type": "api",
            "name": title,
            "metadata": {"asyncapi": version, "api_version": info.get("version")},
            "provenance": provenance,
        }
    ]
    edges: list[dict[str, Any]] = []
    channel_ids: dict[str, str] = {}
    contract_nodes: set[str] = set()

    servers = payload.get("servers", {})
    if isinstance(servers, dict):
        for name, raw in sorted(servers.items()):
            if not isinstance(raw, dict):
                continue
            address = _clean(raw.get("host")) or _clean(raw.get("url")) or str(name)
            sid = f"endpoint.asyncapi.{_slug(str(name))}"
            nodes.append(
                {
                    "id": sid,
                    "type": "message-broker",
                    "name": str(name),
                    "metadata": {"address": address, "protocol": raw.get("protocol")},
                    "provenance": provenance,
                }
            )
            edges.append({"source": sid, "target": api_id, "relation": "serves", "propagation": "both", "provenance": provenance})

    for key, raw in sorted(channels.items()):
        if not isinstance(raw, dict):
            continue
        address = _clean(raw.get("address")) or str(key)
        cid = f"interface.asyncapi.{_slug(str(key))}"
        channel_ids[str(key)] = cid
        nodes.append(
            {
                "id": cid,
                "type": "interface",
                "name": address,
                "metadata": {"channel": str(key), "address": address},
                "provenance": provenance,
            }
        )
        edges.append({"source": api_id, "target": cid, "relation": "contains-channel", "provenance": provenance})
        for contract in _async_message_contracts(raw):
            mid = f"data-contract.asyncapi.{_slug(contract)}"
            if mid not in contract_nodes:
                nodes.append(
                    {
                        "id": mid,
                        "type": "data-contract",
                        "name": contract,
                        "provenance": provenance,
                    }
                )
                contract_nodes.add(mid)
            edges.append({"source": cid, "target": mid, "relation": "carries-contract", "propagation": "both", "provenance": provenance})

        if version.startswith("2."):
            for action in ("publish", "subscribe"):
                operation = raw.get(action)
                if not isinstance(operation, dict):
                    continue
                operation_id = _clean(operation.get("operationId")) or f"{action}-{key}"
                oid = f"interface-operation.asyncapi.{_slug(operation_id)}"
                nodes.append(
                    {
                        "id": oid,
                        "type": "interface-operation",
                        "name": operation_id,
                        "metadata": {"action": "send" if action == "publish" else "receive", "channel": str(key)},
                        "provenance": provenance,
                    }
                )
                edges.append({"source": cid, "target": oid, "relation": "supports-operation", "provenance": provenance})

    operations = payload.get("operations", {})
    if isinstance(operations, dict):
        for name, raw in sorted(operations.items()):
            if not isinstance(raw, dict):
                continue
            action = _clean(raw.get("action")) or "unknown"
            channel_ref = raw.get("channel")
            channel_key = ""
            if isinstance(channel_ref, dict) and isinstance(channel_ref.get("$ref"), str):
                channel_key = channel_ref["$ref"].rsplit("/", 1)[-1]
            oid = f"interface-operation.asyncapi.{_slug(str(name))}"
            nodes.append(
                {
                    "id": oid,
                    "type": "interface-operation",
                    "name": str(name),
                    "metadata": {"action": action, "channel": channel_key},
                    "provenance": provenance,
                }
            )
            if channel_key in channel_ids:
                edges.append({"source": channel_ids[channel_key], "target": oid, "relation": "supports-operation", "provenance": provenance})
            else:
                edges.append({"source": api_id, "target": oid, "relation": "contains-operation", "provenance": provenance})

    return EnterpriseGraph.from_dict(
        {
            "version": 1,
            "nodes": nodes,
            "edges": edges,
            "metadata": {"adapter": "asyncapi", "source": source.as_posix(), "source_version": version},
        }
    )
