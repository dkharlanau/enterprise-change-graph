# Enterprise Change Graph

**Deterministic change-impact analysis for enterprise systems.**

Enterprise Change Graph (ECG) answers a practical release question:

> I am changing this mapping, interface, field, API contract, system, or process. What can be affected, why, what must be tested, who must review it, and is the change safe to release?

ECG is Git-native, vendor-neutral, explainable, and automation-first. The deterministic core does not invent risk scores or require an LLM.

## Choose this graph when

Use **Enterprise Change Graph** when the durable object you are analyzing is a **specific change, release, decommission, schema change, or mapping change**. ECG is optimized for propagation rules, inclusion/exclusion explanations, regression scope, ownership review, release collisions, and predicted-vs-observed impact.

Use [Transformation Graph](https://github.com/dkharlanau/transformation-graph) instead when you need a **materialized transformation project model** that continuously normalizes and connects process, interface, mapping, data, tests, ownership and evidence across a project/revision.

| Question | Enterprise Change Graph | Transformation Graph |
| --- | --- | --- |
| What does change `CR-142` affect and why? | **Primary** | General traversal |
| Why is a target excluded from impact? | **Primary (`why-not`)** | Not the main abstraction |
| What tests/owners are required for this release? | **Primary** | Coverage/governance view |
| Are two planned changes colliding? | **Primary** | Not the main abstraction |
| What is the connected transformation model for this project? | Supporting input | **Primary** |
| Where are durable project-wide traceability gaps? | Change-specific view | **Primary** |
| Should Mapping/Interface/Process semantics be authored here? | **No** | **No** |

Both products consume independently owned domain semantics and retain provenance. Neither should become a second source of truth for process, mapping, or interface contracts.

## What it does

- traces impact through processes, systems, data, mappings, interfaces, API contracts, controls, tests, and owners;
- explains **why an object is impacted** and **why a target is not impacted**;
- supports change-specific propagation such as `schema-change`, `mapping-change`, and `decommission`;
- compares graph versions and analyzes removals against the **before** graph;
- finds regression-test and ownership gaps and derives a minimal deterministic regression set;
- gates CI with reusable YAML governance policies;
- composes independently owned graph fragments while retaining provenance;
- imports CSV, Excel, Interface-as-Code, Mapping-as-Code, Process-as-Code, Reconciliation-as-Code, OpenAPI, and AsyncAPI artifacts;
- ingests JUnit test evidence and converts it to historical change evidence;
- detects collisions across changes in a release;
- compares predicted impact with observed production evidence;
- exports GraphML/Cypher and builds a dependency-free static HTML explorer;
- emits compact JSON context suitable for agents and MCP wrappers;
- includes a reproducible synthetic benchmark and optional performance budgets.

## Quick start

```bash
python -m pip install -e ".[dev]"
ecg validate examples/customer-country-change.yaml
ecg impact examples/customer-country-change.yaml --change CR-142 --explain
ecg report examples/customer-country-change.yaml --change CR-142
ecg gate examples/customer-country-change.yaml --change CR-142 --policy policies/baseline.yaml
```

## Import existing artifacts

```bash
ecg import-interface interface.yaml --output interface.graph.yaml
ecg import-mapping mapping.yaml --output mapping.graph.yaml
ecg import-process process.yaml --output process.graph.yaml
ecg import-reconciliation reconciliation.yaml --output reconciliation.graph.yaml
ecg import-openapi openapi.yaml --output openapi.graph.yaml
ecg import-asyncapi asyncapi.yaml --output asyncapi.graph.yaml
ecg compose interface.graph.yaml process.graph.yaml openapi.graph.yaml --output enterprise.yaml
```

The project is intended to consume artifacts teams already maintain, rather than require another manually curated CMDB.

## Explain exclusion

```bash
ecg why-not graph.yaml --change CR-142 --target process.some-process
```

The answer identifies deterministic barriers such as propagation direction, active filters, max depth, or physical disconnection.

## Test evidence loop

```bash
ecg junit junit.xml --format json
ecg junit-history junit.xml --change CR-142 --output history-fragment.json
```

JUnit test cases can carry an explicit `ecg.test_id` property so execution evidence maps back to graph test nodes without fuzzy matching.

## Realistic SAP demo

`examples/sap-customer-master/` is a synthetic but realistic multi-team landscape with **59 nodes, 61 relationships, and 3 change scenarios** covering SAP MDG, Integration Suite/CPI, S/4HANA, CRM, tax, commerce, DWH/BW, mappings, processes, controls, tests, and owners.

```bash
ecg report examples/sap-customer-master/golden-graph.yaml --change SAP-CR-001 --output /tmp/impact.md
ecg release examples/sap-customer-master/golden-graph.yaml --change SAP-CR-001 --change SAP-CR-002
```

## Interoperability and exploration

```bash
ecg export graph.yaml --format graphml --output graph.graphml
ecg export graph.yaml --format cypher --output graph.cypher
ecg explore graph.yaml --change CR-142 --output explorer.html
```

The static explorer has no CDN, backend, database, or runtime dependency.

## Performance

Impact analysis builds one adjacency index per run and stores explanation traces as parent links instead of copying complete paths during traversal.

```bash
ecg benchmark --nodes 10000 --fanout 2 --repeats 3
ecg benchmark --nodes 10000 --max-median-ms 500
```

A performance-budget breach returns exit code `4`. No universal millisecond target is claimed because execution environments differ.

## Core commands

| Command | Purpose |
|---|---|
| `ecg validate` | Validate a graph document |
| `ecg impact` | Explain downstream impact from a change or seed |
| `ecg why-not` | Explain why a target is excluded |
| `ecg diff` | Compare graph versions and derive before/after seeds |
| `ecg review` | Removal-aware before/after impact analysis |
| `ecg report` | Produce Markdown/HTML/JSON decision artifacts |
| `ecg gate` | Enforce governance policy in CI |
| `ecg compose` | Combine graph fragments with provenance |
| `ecg import-*` | Onboard catalogs, as-code artifacts, and API contracts |
| `ecg junit` | Normalize JUnit XML execution evidence |
| `ecg junit-history` | Convert execution evidence to ECG history |
| `ecg quality` | Find orphans and missing tests/owners |
| `ecg release` | Union regression scope and detect collisions |
| `ecg observe` | Compare predicted impact with observed results |
| `ecg similar` | Find similar historical change subgraphs |
| `ecg context` | Emit compact agent/MCP-ready JSON |
| `ecg export` | Produce GraphML or Cypher |
| `ecg explore` | Build a static interactive HTML explorer |
| `ecg benchmark` | Measure deterministic traversal on a reproducible graph |
| `ecg dot` | Render Graphviz DOT |

## Deterministic-first

The core separates evidence from inference: no LLM is required; no opaque risk score decides a release; every affected node has a path explaining why it is in scope; explicit exclusion barriers can be inspected; incomplete traversal can be forbidden by policy.

## CI and agents

The root `action.yml` generates a removal-aware review in GitHub Job Summary and can optionally maintain one persistent PR comment. `ecg context ...` returns a stable JSON boundary for MCP/tool wrappers.

## Status

**0.11.0 — usable alpha.** Core impact, exclusion explanation, diff/review, governance, composition, artifact/API imports, test evidence, quality, release, reporting, evidence, export, exploration, and performance workflows are executable and tested.

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)

Portfolio map: https://dkharlanau.github.io/products/
