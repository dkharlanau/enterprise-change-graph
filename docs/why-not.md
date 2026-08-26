# Why is this object not impacted?

A useful impact engine must explain both inclusion and exclusion.

```bash
ecg why-not graph.yaml --change CR-142 --target process.some-process
```

The command first computes the normal deterministic impact result. If the target is absent, it finds a shortest physical graph path from the seed set and reports the first deterministic barrier it can prove:

- `disconnected` — there is no graph path at all;
- `propagation_direction` — a relation exists but does not propagate in that direction for this change kind;
- `relation_filter` — the active relation filters stop the path;
- `node_type_filter` — the next node type is an explicit traversal barrier;
- `max_depth` — traversal depth stops before the target.

The explanation is evidence, not an AI-generated guess. A graph can contain several alternate physical paths; the command reports a deterministic shortest candidate path and its first barrier.
