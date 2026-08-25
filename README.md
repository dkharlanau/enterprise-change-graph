# Enterprise Change Graph

Trace enterprise changes across processes, systems, data, mappings, interfaces, owners, and regression tests.

## Problem

A seemingly small SAP or enterprise change can affect business processes, integrations, mappings, downstream systems, tests, and operations, but impact analysis is often manual.

## Core idea

Traverse a project dependency graph from a structured change definition to compute affected processes, systems, data, mappings, interfaces, owners, and tests.

## Example

```yaml
change:
  id: CR-142
  description: Change customer country mapping
```

```text
Possible output:

Affected processes: 3
Affected interfaces: 2
Affected mappings: 17
Affected tests: 6
Affected systems: 4
Affected owners: 3
```

## Initial scope

- change definition
- graph-based dependency traversal
- process impact
- system impact
- data impact
- interface impact
- mapping impact
- test impact
- owner impact
- generated regression scope

## Long-term direction

Model-backed enterprise impact analysis for transformation and operations.

## Design principles

- versionable
- portable
- machine-readable
- deterministic-first
- visual where useful
- Git-friendly
- vendor-neutral where practical
- interoperable with enterprise tools

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

Planning.
