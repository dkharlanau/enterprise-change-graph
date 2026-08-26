# Test evidence

ECG distinguishes predicted impact from observed evidence.

## JUnit XML

```bash
ecg junit junit.xml --format json
```

JUnit results are normalized into deterministic test evidence: total tests, pass/fail/error/skipped counts, duration, and failed ECG test IDs.

To preserve an existing graph test identity, add this testcase property:

```xml
<properties>
  <property name="ecg.test_id" value="test.customer-replication"/>
</properties>
```

Without it ECG creates a stable fallback ID from classname and test name.

## Convert execution to historical change evidence

```bash
ecg junit-history junit.xml \
  --change CR-142 \
  --affected-node mapping.customer-country \
  --output history-fragment.json
```

The output uses the same history-record format consumed by `ecg observe` and `ecg similar`. Failed tests become observed evidence; they are not silently interpreted as additional graph impact.

A CI pipeline can therefore perform a closed loop:

1. predict impacted tests;
2. execute them in the existing test runner;
3. ingest JUnit evidence;
4. compare predicted and observed outcomes over time.
