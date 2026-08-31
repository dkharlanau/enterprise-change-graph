# Roadmap

## Delivered through 0.11

- canonical versioned graph model and JSON Schema
- deterministic, explainable impact traversal
- adjacency-indexed impact traversal and parent-linked explanation traces
- deterministic explanation of non-impact barriers
- change-kind relation semantics and bounded traversal filters
- graph diff plus removal-aware before/after review
- multi-file composition, namespaces, conflicts, and provenance
- CSV / Excel onboarding
- Interface-as-Code, Mapping-as-Code, Process-as-Code, and Reconciliation-as-Code adapters
- OpenAPI 3.x and AsyncAPI 2.x/3.x contract adapters
- regression-test and owner coverage diagnostics
- deterministic minimal regression scope
- JUnit test evidence ingestion and history conversion
- reusable governance policy files and CI exit codes
- Markdown / HTML / JSON impact reports
- graph quality diagnostics
- release collision and approval-route analysis
- predicted-vs-observed evidence comparison
- similar historical change search
- agent/MCP-ready structured context
- GraphML and Cypher export
- dependency-free static HTML explorer
- GitHub Action with Job Summary and optional persistent PR comment
- synthetic performance benchmark and caller-defined budgets
- synthetic 59-node SAP customer-master reference landscape
- generated public impact report, machine-readable result, and interactive explorer for the SAP reference landscape

## Next: harden what is now useful

1. Add adapter conformance suites pinned to upstream fixture versions so source-schema drift is visible.
2. Add exact alternative-path barrier analysis to `why-not`, not only the deterministic shortest physical path.
3. Add graph schema migration tooling before introducing a schema v2.
4. Add generic test-plan import/export and only then tool-specific SAP Cloud ALM / Tricentis adapters when verified API/export contracts are available.
5. Add reusable GitLab and Azure DevOps review workflow examples.
6. Add benchmark scenarios for 10k/100k enterprise-style sparse graphs and track regressions by environment class rather than one universal threshold.
7. Add an optional semantic enrichment protocol that keeps deterministic evidence and inferred suggestions strictly separate.
