# Enterprise Change Graph

**Deterministic impact analysis for enterprise changes.**

Enterprise Change Graph turns processes, systems, data objects, interfaces,
mappings, controls, tests, and owners into a versioned dependency graph. Start
from a concrete change and compute what can be affected, why it is affected,
which regression tests belong in scope, and who owns the impacted area.

The project is designed for SAP and other integration-heavy enterprise
landscapes, but the model and engine are vendor-neutral.

## Why

A change such as “adjust customer country mapping” rarely ends at the mapping.
It can propagate into master data fields, replication interfaces, S/4HANA
behavior, tax controls, order-to-cash processes, tests, and operating teams.

Impact analysis is often reconstructed manually from spreadsheets, tickets,
architecture diagrams, and specialist memory. Those artifacts are useful, but
they are difficult to traverse deterministically and hard to use in CI or agent
workflows.

Enterprise Change Graph makes the dependency model executable.

## What works now

- YAML or JSON graph documents
- schema and deterministic structural validation
- explicit impact propagation direction per relationship
- multi-seed breadth-first impact traversal
- cycle-safe deterministic shortest explanation paths
- graph-version diff with impact seed candidates
- deterministic CI governance gates
- criticality summary without opaque scoring
- automatic regression-test scope
- automatic owner scope
- depth-limited analysis
- JSON output for automation and agents
- Graphviz DOT output for visualization
- CLI and GitHub Actions CI

## 60-second example

```bash
python -m pip install -e .
ecg validate examples/customer-country-change.yaml
ecg impact examples/customer-country-change.yaml --change CR-142
```

Example output:

```text
Impact: CR-142 — Change customer country mapping
Seeds: mapping.customer-country
Affected nodes: 12
By type: control=1, data=1, interface=1, mapping=1, owner=2, process=2, system=2, test=2
By criticality: critical=4, high=6, low=2
Maximum criticality: critical
Regression tests: test.customer-replication, test.otc-tax
Owners: owner.integration, owner.master-data
```

Ask for explanation paths:

```bash
ecg impact examples/customer-country-change.yaml --change CR-142 --explain
```

Machine-readable output:

```bash
ecg impact examples/customer-country-change.yaml --change CR-142 --format json
```

Graphviz:

```bash
ecg dot examples/customer-country-change.yaml --change CR-142 > impact.dot
dot -Tsvg impact.dot > impact.svg
```

## Detect change between graph versions

The graph itself can be versioned in Git. `ecg diff` compares two valid graph
snapshots and reports added, removed, and modified nodes, edges, and declared
changes.

```bash
ecg diff examples/diff-before.yaml examples/diff-after.yaml
```

The output also derives conservative `impact_seeds_after` candidates from changed
nodes and changed edge endpoints. Those seed IDs can feed the normal impact
traversal in CI or a pull-request workflow. Removed nodes are reported separately
because they no longer exist in the after graph and need removal-impact handling.

Use JSON when another tool or agent will consume the result:

```bash
ecg diff examples/diff-before.yaml examples/diff-after.yaml --format json
```

## Turn impact into a CI gate

`ecg gate` converts the same deterministic impact set into a CI-friendly pass/fail
result. For example, require a bounded blast radius plus explicit test and owner
coverage:

```bash
ecg gate examples/customer-country-change.yaml \
  --change CR-142 \
  --max-affected 20 \
  --min-tests 2 \
  --min-owners 2
```

You can also fail on a criticality threshold or forbid specific nodes/types. A
policy failure exits with code `3`; invalid input exits with code `2`.

See [CI and governance gates](docs/ci.md).

## Minimal model

```yaml
version: 1

nodes:
  - id: mapping.customer-country
    type: mapping
    criticality: high

  - id: interface.mdg-to-s4-customer
    type: interface
    criticality: critical

edges:
  - source: mapping.customer-country
    target: interface.mdg-to-s4-customer
    relation: affects
    propagation: forward

changes:
  - id: CR-142
    title: Change customer country mapping
    seeds:
      - mapping.customer-country
```

`propagation` is the important part: architectural direction and impact direction
are not always the same. Use `forward`, `reverse`, `both`, or `none`.

See [the graph model](docs/model.md) and [use cases](docs/use-cases.md).

## Design principles

- deterministic first
- explanation before scoring
- versionable and Git-friendly
- machine-readable by default
- portable across enterprise tools
- vendor-neutral core
- no database required for the core workflow
- useful to both humans and agents

## Project direction

The next layers are removal-aware diff impact, policy files and reusable policy
packs, graph composition across repositories, richer evidence links, generated
impact reports, and connectors to adjacent “as code” projects.

See [ROADMAP.md](ROADMAP.md).

## Related projects

- [Mapping as Code](https://github.com/dkharlanau/mapping-as-code)
- [Transformation Graph](https://github.com/dkharlanau/transformation-graph)
- [Interface as Code](https://github.com/dkharlanau/interface-as-code)
- [Reconciliation as Code](https://github.com/dkharlanau/reconciliation-as-code)
- [Process as Code](https://github.com/dkharlanau/process-as-code)
- [Decision Tables as Code](https://github.com/dkharlanau/decision-tables-as-code)
- [Data Relationship Map](https://github.com/dkharlanau/data-relationship-map)
- [Cutover Graph](https://github.com/dkharlanau/cutover-graph)
- [Project Evidence Graph](https://github.com/dkharlanau/project-evidence-graph)

## Status

**Working core / early alpha (`0.3.0`).** The graph format may evolve before `1.0`.
