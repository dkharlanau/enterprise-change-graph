# Enterprise Change Graph

**Deterministic change-impact analysis for enterprise systems.**

Enterprise Change Graph (ECG) answers a practical release question:

> I am changing this mapping, interface, field, system, or process. What can be affected, why, what must be tested, who must review it, and is the change safe to release?

ECG is Git-native, vendor-neutral, explainable, and automation-first. The deterministic core does not invent risk scores or require an LLM.

## What it does

- traces impact through processes, systems, data, mappings, interfaces, controls, tests, and owners;
- explains **why an object is impacted** and **why a target is not impacted**;
- supports change-specific propagation such as `schema-change`, `mapping-change`, and `decommission`;
- compares graph versions and analyzes removals against the **before** graph;
- finds regression-test and ownership gaps and derives a minimal deterministic regression set;
- gates CI with reusable YAML governance policies;
- composes independently owned graph fragments while retaining provenance;
- imports CSV, Excel, Interface-as-Code, Mapping-as-Code, Process-as-Code, and Reconciliation-as-Code artifacts;
- detects collisions across changes in a release;
- compares predicted impact with observed production evidence;
- exports GraphML/Cypher and builds a dependency-free static HTML explorer;
- emits compact JSON context suitable for agents and MCP wrappers.

## Quick start

```bash
python -m pip install -e ".[dev]"
ecg validate examples/customer-country-change.yaml
ecg impact examples/customer-country-change.yaml --change CR-142 --explain
ecg report examples/customer-country-change.yaml --change CR-142
ecg gate examples/customer-country-change.yaml --change CR-142 --policy policies/baseline.yaml
```

## Explain exclusion

```bash
ecg why-not graph.yaml --change CR-142 --target process.some-process
```

The answer identifies deterministic barriers such as propagation direction, active filters, max depth, or physical disconnection.

## Import existing artifacts

```bash
ecg import-interface interface.yaml --output interface.graph.yaml
ecg import-mapping mapping.yaml --output mapping.graph.yaml
ecg import-process process.yaml --output process.graph.yaml
ecg import-reconciliation reconciliation.yaml --output reconciliation.graph.yaml
ecg compose interface.graph.yaml process.graph.yaml --output enterprise.yaml
```

## Realistic SAP demo

`examples/sap-customer-master/` is a synthetic but realistic multi-team landscape with **59 nodes, 61 relationships, and 3 change scenarios** covering SAP MDG, Integration Suite/CPI, S/4HANA, CRM, tax, commerce, DWH/BW, mappings, processes, controls, tests, and owners.

```bash
ecg report examples/sap-customer-master/golden-graph.yaml --change SAP-CR-001 --output /tmp/impact.md
ecg release examples/sap-customer-master/golden-graph.yaml --change SAP-CR-001 --change SAP-CR-002
```

## Interoperability

```bash
ecg export graph.yaml --format graphml --output graph.graphml
ecg export graph.yaml --format cypher --output graph.cypher
ecg explore graph.yaml --change CR-142 --output explorer.html
```

The static explorer has no CDN, backend, database, or runtime dependency.

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
| `ecg import-*` | Onboard catalogs and adjacent as-code artifacts |
| `ecg quality` | Find orphans and missing tests/owners |
| `ecg release` | Union regression scope and detect collisions |
| `ecg observe` | Compare predicted impact with observed results |
| `ecg similar` | Find similar historical change subgraphs |
| `ecg context` | Emit compact agent/MCP-ready JSON |
| `ecg export` | Produce GraphML or Cypher |
| `ecg explore` | Build a static interactive HTML explorer |
| `ecg dot` | Render Graphviz DOT |

## Governance as code

Policies are versionable YAML. CLI values explicitly supplied by the caller override file values. Gate exit code `3` means policy failure; exit code `2` means invalid input or execution error.

## Why a graph, not another CMDB?

ECG is intended to **consume existing project artifacts**, not require teams to maintain another central inventory. Fragments can live with teams that own mappings, interfaces, processes, tests, reconciliations, or systems and be composed during CI. Conflicting duplicate definitions fail loudly instead of being silently merged.

## Deterministic-first

The core separates evidence from inference: no LLM is required; no opaque risk score decides a release; every affected node has a path explaining why it is in scope; explicit exclusion barriers can be inspected; incomplete traversal can be forbidden by policy.

## CI and agents

The root `action.yml` generates a removal-aware review in GitHub Job Summary and can optionally maintain one persistent PR comment. `ecg context ...` returns a stable JSON boundary for MCP/tool wrappers. Transport-neutral helpers remain available for GitHub comments, ServiceNow work notes, and Jira Cloud ADF.

## Status

**0.10.0 — usable alpha.** Core impact, exclusion explanation, diff/review, governance, composition, imports, quality, release, reporting, evidence, export, and exploration workflows are executable and tested.

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)
