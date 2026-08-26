# Interoperability

Enterprise Change Graph is designed to sit between existing artifacts rather than replace them.

## Process as Code

`ecg import-process process.yaml --output process.graph.yaml`

The adapter follows the current Process-as-Code v0.2 shape: `process`, `steps`, and `transitions`. It creates a process node, granular process-step nodes, `contains-step`, `starts-with`, and `flows-to` relationships. Invalid transition targets fail deterministically.

## Reconciliation as Code

`ecg import-reconciliation reconciliation.yaml --output reconciliation.graph.yaml`

The adapter maps source/target datasets, reconciliation checks, field-level checks, exception policy, and evidence output into the canonical graph. It is compatible with the current Reconciliation-as-Code example structure.

## GraphML

`ecg export graph.yaml --format graphml --output graph.graphml`

Use GraphML for tooling that accepts a neutral graph interchange format.

## Cypher

`ecg export graph.yaml --format cypher --output graph.cypher`

The generated statements create `ECGNode` nodes and typed relationships suitable for Neo4j-style exploration. The canonical YAML/JSON graph remains the source of truth.

## Static explorer

`ecg explore graph.yaml --change CR-142 --output explorer.html`

The generated HTML has no runtime dependencies, CDN calls, backend, or database. It embeds the graph, lays out nodes by type, supports search/type filtering and node details, and highlights the selected deterministic impact set.
