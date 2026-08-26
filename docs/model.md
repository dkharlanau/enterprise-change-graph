# Graph model

Enterprise Change Graph models impact propagation, not merely architecture.

## Node

A node is any enterprise artifact that may be changed or affected:

- `process`
- `system`
- `data`
- `interface`
- `mapping`
- `decision`
- `control`
- `test`
- `owner`

Custom node types are allowed. Every node has a stable `id`, a `type`, an optional
human-readable `name`, a `criticality`, and arbitrary `metadata`.

## Edge

An edge records a relationship and explicitly states how change impact propagates.

```yaml
- source: data.customer.country
  target: interface.mdg-to-s4-customer
  relation: replicated-by
  propagation: forward
```

`propagation` can be:

- `forward` — a change in `source` may affect `target` (default)
- `reverse` — a change in `target` may affect `source`
- `both` — impact may propagate in either direction
- `none` — relationship is visible but excluded from impact traversal

This keeps architectural relationship direction separate from impact direction.

## Change

A declared change points to one or more seed nodes.

```yaml
changes:
  - id: CR-142
    title: Change customer country mapping
    seeds:
      - mapping.customer-country
```

The analyzer performs breadth-first traversal over propagation-enabled edges. For
every affected node it retains a deterministic shortest explanation path. Cycles
are safe because each node is visited once.

## Criticality

`low`, `medium`, `high`, and `critical` are intentionally simple. The engine does
not invent an opaque risk score. It reports the maximum criticality and the
criticality distribution of the actual impact set.
