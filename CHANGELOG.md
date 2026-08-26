# Changelog

## 0.3.0

- add deterministic CI governance gates over impact results
- support blast-radius, regression-test, owner, criticality, forbidden-node, and forbidden-type checks
- return distinct CI exit codes for policy failures and invalid input
- add JSON gate output, tests, documentation, and CI smoke coverage

## 0.2.0

- add deterministic graph-to-graph diff
- detect added, removed, and modified nodes, edges, and change declarations
- derive conservative impact seed candidates from structural changes
- add CLI coverage for `ecg diff`
- add diff examples and CI smoke test

## 0.1.0

- add canonical graph model and validation
- add deterministic impact traversal and explanation paths
- add regression-test and owner scope
- add JSON and Graphviz DOT outputs
- add CLI, schema, examples, tests, and CI
