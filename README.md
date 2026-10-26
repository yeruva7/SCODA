# SCODA — Scalable Configuration-Driven Automation

SCODA is a four-layer, multi-tenant test automation architecture for
services with nondeterministic, LLM-backed outputs and per-tenant
configuration requirements.

It demonstrates the mechanism that lets per-tenant onboarding cost decline
as the number of tenants grows, instead of scaling linearly: shared tests
execute once and the result is distributed to every tenant, while only
genuinely tenant-specific tests execute per tenant.

## Architecture

Four layers, each with a single responsibility:

1. **Configuration aggregation** (`scoda.config`) — resolves four
   configuration layers into one effective configuration per
   (tenant, environment) pair, with strict precedence:

   ```
   C1 (global defaults) → C2 (tenant base) → C3 (environment) → C4 (runtime)
   ```

   Each layer deep-merges onto the previous one; later layers win on
   conflicting scalar values, and `C4` is supplied at dispatch time rather
   than loaded from a file (e.g. CI/CD job variables).

2. **Namespace isolation** (`scoda.isolation`) — every tenant gets a frozen
   copy of its resolved configuration and a private result queue. No two
   tenants share a mutable storage location, so one tenant's test run
   cannot affect another's results.

3. **Parallel dispatch** (`scoda.dispatcher`) — a test is *shared* if it
   declares no tenant-specific binding, and *tenant-specific* if it is
   gated behind a feature flag present only in some tenants' resolved
   configuration. Shared tests run once; tenant-specific tests run per
   tenant, in parallel across tenants.

4. **Response analysis** (`scoda.evaluation`) — deterministic responses are
   checked with structural assertions (status, field presence, schema
   shape). Nondeterministic responses are scored by a pluggable judge
   function against a threshold `tau`, optionally with hard per-dimension
   minima (e.g. a safety dimension that must never be averaged away). A
   dependency-free `EchoJudge` (lexical similarity) is included for local
   testing; swap in a model-backed judge for production use.

A `scoda.gate.evaluate_gate` turns a tenant's pass rate into a release
decision (`PASS` / `BLOCK` / `ALERT`), blocking when the evaluated set is
empty because no pass can be established from it, and `scoda.reporting`
keeps each tenant's report strictly separate from every other tenant's.

## Installation

```bash
git clone https://github.com/yeruva7/SCODA.git
cd SCODA
pip install -e .
```

No third-party dependencies are required for the framework, the drivers or
the tests; SCODA uses only the Python standard library. The comparator
directories need their own tools installed (`selenium`, `@playwright/test`,
`deepeval`, `promptfoo`) and are not needed to run anything above.

## Quick start

```bash
python3 examples/run_example.py
```

This onboards two tenants with different configuration states from
`examples/`, runs a shared health check plus a tenant-gated semantic
equivalence check, and prints each tenant's gate decision:

```
[catalog-search] PASS (pass_rate=100.0%, 2/2 passed, 0 skipped)
[docs-search] PASS (pass_rate=100.0%, 1/1 passed, 0 skipped)
```

### Minimal usage

```python
from scoda import ConfigResolver, Orchestrator, TestCase, Priority

resolver = ConfigResolver(
    global_dir="examples/global",
    tenants_dir="examples/tenants",
    environments_dir="examples/environments",
)
orchestrator = Orchestrator(resolver)
orchestrator.onboard_tenant("catalog-search", env="staging")

suite = [
    TestCase(
        name="health_check",
        level="shared",
        kind="structural",
        assertions=[{"path": "status", "equals": 200}],
    ),
]
reports = orchestrator.run(suite, theta=0.95, priority=Priority.STANDARD)
print(reports["catalog-search"].summary())
```

## Running the tests

```bash
python3 -m unittest discover -s tests -v
```

Fifty tests. The ones that carry paper claims are named for them:
`test_resolution_order_global_then_tenant_then_env_then_runtime`,
`test_isolation_invariant_holds_across_tenants`,
`test_shared_test_executes_for_every_tenant`,
`test_empty_evaluated_set_is_blocked`, `test_qps_max_matches_section_v_b`,
`test_mechanism_fit_recovers_known_parameters`.

## Measuring a deployment

The drivers measure a real endpoint rather than replaying numbers.
Prepare the tenant parameters and the workload specs, then point the
drivers at the endpoint under test:

```bash
python3 tenants/generate_tenants.py --count 150
python3 workloads/make_workloads.py
```

```bash
# M1, throughput, with per-run dispersion
python3 workloads/driver_throughput.py --endpoint http://127.0.0.1:8080 \
    --workload workloads/functional_500.json --runs 10 --workers 16

# scaling: T(n), interval secants, and the four candidate model fits
python3 workloads/driver_scaling.py --endpoint http://127.0.0.1:8080 \
    --workload workloads/scaling_mixed.json --counts 1,5,10,25,50,100,150 \
    --workers 16

# M2 reuse, and M4 when person-hours are supplied
python3 workloads/driver_onboarding.py --counts 1,10,25,50,100,150

# semantic accuracy; precision/recall/F1 only when labels are supplied
python3 workloads/driver_semantic.py --endpoint http://127.0.0.1:8080 \
    --judge-endpoint http://127.0.0.1:8080 \
    --workload workloads/semantic_2000.json --labels labels.json
```

Absolute throughput is bounded by `W/(t̄ + Δ_net)`, and service
time and network delay belong to the system under test, so a different
deployment yields a different rate. What transfers across deployments is
the shape: shared work executing once, state occupancy saturating, and
incremental per-tenant cost declining.

See [docs/REPRODUCING.md](docs/REPRODUCING.md) for the claim-by-claim map
of what is reproducible here and what is deployment-specific.

## Configuration format

A tenant configuration file (`examples/tenants/<tenant>.json`) overrides
only what differs from the global defaults:

```json
{
  "tenant": "catalog-search",
  "flags": { "semantic_validation_v1": true },
  "validation": {
    "semantic": { "enabled": true, "threshold_tau": 0.75 }
  }
}
```

Everything not explicitly overridden is inherited from
`examples/global/defaults.json`, which is what keeps per-tenant onboarding
cheap: most tenants need only a handful of override keys.

## Project layout

```
scoda/
  config.py        # four-layer configuration resolver (deep merge)
  isolation.py     # tenant namespace isolation
  dispatcher.py    # shared/specific test selection + parallel execution
  evaluation.py    # structural validation + semantic (judge-based) evaluation
  gate.py          # pass-rate -> release-gate decision
  reporting.py     # per-tenant report collection
  datasets.py      # loaders for the four public QA datasets
  http_client.py   # transport with the service-limit cap applied
  judges.py        # pluggable judges, including open-weight replication
  metrics.py       # M1-M5, Psi, Phi, FPR, secants, model selection
examples/          # configuration layers and a runnable example
tenants/           # per-tenant parameter files and their generator
workloads/         # workload specs and drivers
comparators/       # third-party tool configurations and their drivers
docs/              # claim-by-claim reproduction guide
tests/             # resolver, isolation, gate, dispatch, limit, metrics
```

## License

MIT — see [LICENSE](LICENSE).
