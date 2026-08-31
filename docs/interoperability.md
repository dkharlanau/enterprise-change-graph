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

## Product-suite handoff boundary

GraphML and Cypher are structural interchange exports for graph tools. They are not signed evidence, Project Evidence Graph fragments, Transformation Graph project manifests, or proof that another product has accepted the semantics.

The implemented semantic inbound adapters are the source of truth for supported handoffs:

- Mapping as Code via `ecg import-mapping`;
- Interface as Code via `ecg import-interface`;
- Process as Code via `ecg import-process`;
- Reconciliation as Code via `ecg import-reconciliation`;
- OpenAPI and AsyncAPI via `ecg import-openapi` and `ecg import-asyncapi`;
- JUnit evidence via `ecg junit` and `ecg junit-history`.

Transformation Graph and Project Evidence Graph are related analysis products, but their native outputs are not accepted by a direct ECG adapter today. Use the canonical ECG model or one of the adapters above, and preserve the original producer provenance.

## Static explorer

`ecg explore graph.yaml --change CR-142 --output explorer.html`

The generated HTML has no runtime dependencies, CDN calls, backend, or database. It embeds the graph, lays out nodes by type, supports search/type filtering and node details, and highlights the selected deterministic impact set.
