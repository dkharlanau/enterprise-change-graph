# Performance and scale

The impact engine builds a deterministic adjacency index once per analysis. Traversal itself is linear in the reachable graph size (`O(V + E)`) rather than rescanning all relationships for every visited node.

Explanation traces are stored internally as parent-linked paths. This avoids copying the complete path tuple for every visited node. Full explanation paths are materialized only when a caller requests or serializes them.

## Synthetic benchmark

```bash
ecg benchmark --nodes 10000 --fanout 2 --repeats 3
```

JSON output is available with `--format json`.

A local performance budget can be enforced:

```bash
ecg benchmark --nodes 10000 --max-median-ms 500
```

Exit code `4` means the measured median exceeded the caller's budget. ECG does not ship one universal timing threshold because GitHub-hosted runners, laptops, containers, and enterprise CI agents have different performance characteristics.

The benchmark is deliberately synthetic and reproducible. It measures graph construction plus impact traversal behavior; it is not presented as a substitute for customer-landscape benchmarks.
