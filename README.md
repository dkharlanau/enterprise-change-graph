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

## Status

Planning.
