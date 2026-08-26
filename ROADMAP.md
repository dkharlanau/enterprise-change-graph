# Roadmap

## Delivered through 0.10

- canonical versioned graph model and JSON Schema
- deterministic, explainable impact traversal
- deterministic explanation of non-impact barriers
- change-kind relation semantics and bounded traversal filters
- graph diff plus removal-aware before/after review
- multi-file composition, namespaces, conflicts, and provenance
- CSV / Excel onboarding
- Interface-as-Code, Mapping-as-Code, Process-as-Code, and Reconciliation-as-Code adapters
- regression-test and owner coverage diagnostics
- deterministic minimal regression scope
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
- synthetic 59-node SAP customer-master reference landscape

## Next: prove and harden it

1. Add adapter conformance suites tied to upstream fixture versions.
2. Add OpenAPI / AsyncAPI import for interfaces that are already machine-described.
3. Add test-management adapters (generic JUnit first; SAP Cloud ALM/Tricentis when real export formats are available).
4. Add benchmark graphs (1k/10k/100k nodes) with performance budgets.
5. Add exact alternative-path analysis for `why-not`, beyond the deterministic shortest physical path.
6. Add versioned graph migrations when schema v2 becomes necessary.
7. Add reusable GitLab/Azure DevOps review examples.
8. Add an optional semantic enrichment protocol with strict provenance between deterministic evidence and inferred suggestions.
