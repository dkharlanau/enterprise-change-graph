# Contributing

Enterprise Change Graph is intentionally small and deterministic at the core.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ecg validate examples/customer-country-change.yaml
```

## Contribution principles

1. Keep impact propagation semantics explicit.
2. Prefer deterministic results over heuristic scoring.
3. Preserve machine-readable output and explanation paths.
4. Keep the core vendor-neutral; put vendor-specific conventions in adapters or examples.
5. Add tests for graph semantics and validation changes.

For format changes, update the JSON Schema, model documentation, examples, and
tests in the same pull request.
