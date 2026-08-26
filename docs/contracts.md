# API contract adapters

Enterprise Change Graph can derive graph fragments from API contracts that already describe enterprise interfaces.

## OpenAPI

```bash
ecg import-openapi openapi.yaml --output openapi.graph.yaml
```

The adapter accepts OpenAPI 3.x documents. It creates:

- one `api` node for the contract;
- optional server `endpoint` nodes;
- one `interface` node per HTTP operation;
- `data-contract` nodes for request/response schema references;
- deterministic relations such as `contains-operation`, `accepts-contract`, and `returns-contract`.

The adapter deliberately does not invent upstream/downstream systems from URLs or tags. Those links should come from explicit enterprise inventory or composed fragments.

## AsyncAPI

```bash
ecg import-asyncapi asyncapi.yaml --output asyncapi.graph.yaml
```

The adapter supports AsyncAPI 2.x and 3.x common structures. It creates:

- one `api` node;
- message-broker/server nodes when present;
- channel `interface` nodes;
- `interface-operation` nodes for publish/subscribe or send/receive operations;
- message `data-contract` nodes.

For AsyncAPI 3.x, top-level operations can link to channels via `$ref`. For 2.x, publish/subscribe operations are read from the channel object.

## Composition

Contract-derived fragments become more useful when composed with business/process/test ownership fragments:

```bash
ecg compose openapi.graph.yaml process.graph.yaml assurance.graph.yaml --output enterprise.yaml
```

This keeps API schemas as evidence while preserving enterprise context separately.
