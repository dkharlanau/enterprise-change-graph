# Use cases

## Change request impact analysis

Attach a change request to the exact mappings, fields, interfaces, rules, or
process steps being modified. The graph expands those seeds into a reviewable
impact set before implementation starts.

## Regression scope generation

Model tests as ordinary graph nodes connected to what they verify. Impact
analysis then returns the regression tests reached by the change instead of
relying on a manually maintained test list.

## Ownership routing

Connect enterprise artifacts to owner nodes. The impact result identifies teams
or roles that should review, approve, test, or operate the change.

## SAP transformation programs

Useful graph nodes include business processes, S/4HANA objects, MDG entities,
IDocs/APIs, CPI mappings, value mappings, custom code, controls, cutover objects,
and end-to-end tests. The core engine remains vendor-neutral.

## CI change gates

Store the graph in Git. A pipeline can validate it and produce JSON impact output
for downstream policy checks, pull-request comments, evidence packs, or custom
approval gates.

## AI and agent tooling

The JSON output is deterministic and machine-readable, so an agent can consume a
bounded impact set and its explanation paths rather than infer dependencies from
unstructured project documentation.
