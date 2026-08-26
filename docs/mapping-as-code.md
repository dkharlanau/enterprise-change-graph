# Mapping as Code integration

[Mapping as Code](https://github.com/dkharlanau/mapping-as-code) can project field-level mapping lineage into the Enterprise Change Graph contract.

```bash
map-code project mapping.yaml \
  --target enterprise-change-graph \
  --output mapping.change-graph.json
```

The projection follows `schema/enterprise-change-graph.schema.json` and preserves:

- source and target systems, business objects, fields, and mapping-rule nodes;
- directed lineage relationships with forward propagation;
- `provenance: mapping-as-code` on imported nodes and edges;
- mapping ID and Mapping as Code schema version in graph metadata;
- mapping criticality when declared in business metadata.

The generated graph is an input surface, not a replacement for Enterprise Change Graph. Mapping as Code owns field-mapping intent; Enterprise Change Graph owns graph composition, change seeds, propagation policy, impact traversal, evidence, and governance.
