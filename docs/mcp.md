# Agent and MCP integration

The deterministic engine stays independent from model runtimes.

```bash
ecg context graph.yaml --change CR-142
```

The JSON contains change identity, seeds, impact counts, material high/critical nodes with explanation paths, coverage, minimal regression scope, owners, gaps, and gate decision.

An MCP server or enterprise agent can expose this as a read-only tool: `get_change_impact(graph, change_id) -> ECG context JSON`.

Keep AI inference separate from ECG evidence. Inferred risks should be labeled as inferred rather than merged into deterministic traversal.
