# SAP starter pack

ECG core remains vendor-neutral. SAP concepts are ordinary node types and explicit relationships.

The reference landscape under `examples/sap-customer-master/` demonstrates SAP MDG, Integration Suite/CPI, S/4HANA, customer data, mappings, replication interfaces, tax/credit controls, processes, regression tests, and accountable teams.

Recommended change kinds: `mapping-change`, `schema-change`, `config-change`, `logic-change`, `owner-change`, `decommission`.

Recommended relations: `transforms`, `published-by`, `delivers-to`, `provides`, `used-by`, `supports`, `depends-on`, `governed-by`, `verified-by`, `owned-by`. Projects may extend the vocabulary; propagation semantics should stay explicit.
