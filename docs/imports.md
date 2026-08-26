# Imports and composition

ECG is designed to consume existing project artifacts instead of creating a second manually maintained CMDB.

## CSV

`ecg import-csv nodes.csv --edges edges.csv --changes changes.csv --output graph.yaml`

Nodes columns: `id,type,name,criticality,metadata`. Edges: `source,target,relation,propagation,metadata`. Changes: `id,title,seeds,description,kind,metadata`. `metadata` is JSON text.

## Excel

Install `enterprise-change-graph[excel]`. The workbook uses `Nodes`, `Edges`, and `Changes` sheets with the same columns as CSV.

## Interface as Code

`ecg import-interface interface.yaml --output interface.graph.yaml`

The adapter maps the concrete v1 shape into systems, interface, source/target data, mapping profile, owners, tests, and relationships.

## Mapping as Code

`ecg import-mapping mapping.yaml --output mapping.graph.yaml`

The adapter accepts `mapping.id`, source/target system/object, optional fields/rules. Unsupported fields remain metadata rather than guessed semantics.

## Composition

`ecg compose team-a.yaml team-b.yaml --output enterprise.yaml`

Cross-file edges are allowed. Identical duplicates merge provenance. Conflicting definitions fail. Use `--namespace path.yaml=team2` for intentional ID overlap.
