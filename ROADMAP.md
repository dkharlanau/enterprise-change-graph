# Roadmap

## Delivered in 0.9

- canonical versioned graph model and JSON Schema
- deterministic, explainable impact traversal
- change-kind relation semantics and bounded traversal filters
- graph diff plus removal-aware before/after review
- multi-file composition, namespaces, conflicts, and provenance
- CSV / Excel onboarding
- Interface-as-Code and Mapping-as-Code adapters
- regression-test and owner coverage diagnostics
- deterministic minimal regression scope
- reusable governance policy files and CI exit codes
- Markdown / HTML / JSON impact reports
- graph quality diagnostics
- release collision and approval-route analysis
- predicted-vs-observed evidence comparison
- similar historical change search
- agent/MCP-ready structured context
- synthetic 59-node SAP customer-master reference landscape

## Next: prove it on real work

1. Add more source adapters: Process as Code, reconciliation artifacts, OpenAPI/AsyncAPI, SAP interface inventories.
2. Add conformance fixtures for adapters so schema drift is caught automatically.
3. Improve coverage semantics for alternative paths and explicit test-to-requirement coverage.
4. Add reusable GitHub PR comment workflow and examples for GitLab/Azure DevOps.
5. Add ServiceNow/Jira wrapper examples without putting credentials or transport into core.
6. Add graph-version migration tooling when schema v2 becomes necessary.
7. Add large-graph performance benchmarks and deterministic snapshot suites.
8. Add optional interactive static HTML exploration, keeping CLI/JSON as source of truth.
9. Add optional semantic enrichment protocol with strict provenance between deterministic evidence and inferred suggestions.
