# Governance and release decisions

`ecg gate` evaluates deterministic rules over the calculated impact set and coverage assessment.

Rules include maximum blast radius, minimum tests/owners, criticality threshold, forbidden IDs/types, maximum untested/unowned nodes, complete-traversal requirement, and mandatory change kind.

Policy failure returns exit code `3`; invalid data/configuration returns `2`.

`policies/baseline.yaml` is permissive for onboarding. `policies/strict.yaml` requires complete test and ownership coverage and is a target state for mature landscapes.

No heuristic risk score is used. Every violation names the deterministic evidence.
