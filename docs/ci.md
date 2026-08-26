# CI and governance gates

Enterprise Change Graph can turn impact analysis into a deterministic CI exit code.

## Passing gate

```bash
ecg gate graph.yaml --change CR-142 \
  --max-affected 50 \
  --min-tests 1 \
  --min-owners 1
```

Exit code `0` means the configured gate passed.

## Failing conditions

Available checks can be combined:

- `--max-affected N` — cap blast-radius size
- `--min-tests N` — require a minimum number of impacted regression tests
- `--min-owners N` — require a minimum number of impacted owners
- `--fail-on-criticality LEVEL` — fail when any impacted node is at or above the threshold
- `--forbid-node ID` — fail when a specific node is impacted; repeatable
- `--forbid-type TYPE` — fail when a node type is impacted; repeatable

A policy failure exits with code `3`. Invalid input or an invalid graph exits with
code `2`, keeping policy failures distinct from tool/configuration errors.

## JSON output

```bash
ecg gate graph.yaml --change CR-142 --min-tests 1 --format json
```

The JSON result contains `passed`, `violations`, and the impact summary. This is
suitable for GitHub Actions, PR bots, evidence generation, or agent workflows.

## Design note

The gate intentionally evaluates explicit facts from the impact set. It does not
invent a risk score. Teams can encode the governance threshold that matches their
own landscape and change process.
