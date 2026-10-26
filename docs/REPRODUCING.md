# Reproducing the paper's claims

Every claim in the manuscript that this repository is responsible for, with
the command that produces it. Where a figure depends on the production
deployment, that is stated rather than approximated: the mechanism is
reproducible here, the absolute rates measured on one stack are not.

## What is reproducible here, and what is not

| Claim | Status | How |
|---|---|---|
| Four-level resolution with right-hand precedence, Eqs. (1a)-(1c) | Reproducible | `tests/test_config_resolver.py` |
| Namespace isolation invariant `M(i) ∩ M(j) = ∅`, Sec. V-A2 | Reproducible | `tests/test_isolation.py` |
| Shared tests execute once and fan out, Sec. V-C | Reproducible | `tests/test_orchestrator.py`, `driver_scaling.py` |
| Three-state release gate, empty set blocks, Sec. V-B | Reproducible | `tests/test_gate.py` |
| Service limit `QPS_cap(1-u_prod)·alpha`, Sec. V-B | Reproducible | `tests/test_http_client.py` |
| Occupancy saturation of Eq. (2b) | Reproducible | `driver_scaling.py`, states-occupied column |
| Model selection favours the mechanism form, Table S8 | Reproducible on your data | `driver_scaling.py` |
| Interval secants decline, Eq. (2d) | Reproducible on your data | `driver_scaling.py` |
| M1 throughput, Table 2 | Deployment-specific | `driver_throughput.py` against your endpoint |
| M2 reuse, Table 2 | Reproducible | `driver_onboarding.py` |
| M4 onboarding effort, Table 3 | Needs recorded hours | `driver_onboarding.py --effort-log` |
| Semantic F1, Table 5 | Needs a judge and labels | `driver_semantic.py` |
| 464 tests/min, 448 min at n=150 | Not reproducible here | measured on the production stack; its endpoint set is internal |

The last row is the honest boundary. Absolute throughput is bounded by
`W/(t̄ + Δ_net)`, and service time and network delay belong to the system
under test, so a different deployment yields a different rate. What
transfers is the shape: shared work executing once, occupancy saturating,
and incremental cost declining.

## Setup

```bash
git clone https://github.com/yeruva7/SCODA.git
cd SCODA
pip install -e .
python3 tenants/generate_tenants.py --count 150
python3 workloads/make_workloads.py
```

The drivers measure a service rather than replaying numbers, so the
commands below need an endpoint. Substitute your own host for
`http://127.0.0.1:8080`; the repository ships no service, because
service time and network delay belong to the system under test.

## Mechanism checks

```bash
python3 -m unittest discover -s tests -v
```

Fifty tests. The ones that carry paper claims are named for them:
`test_resolution_order_global_then_tenant_then_env_then_runtime`,
`test_isolation_invariant_holds_across_tenants`,
`test_shared_test_executes_for_every_tenant`,
`test_empty_evaluated_set_is_blocked`, `test_qps_max_matches_section_v_b`,
`test_mechanism_fit_recovers_known_parameters`.

## M1, throughput

```bash
python3 workloads/driver_throughput.py \
    --endpoint http://127.0.0.1:8080 \
    --workload workloads/functional_500.json \
    --runs 10 --workers 16
```

Reports per-run rates, the mean, and a 95 percent interval. With one run it
prints that no dispersion estimate exists instead of inventing an interval.
It also prints the implied `t̄ + Δ_net`, which is the sharpest check that a
quoted rate and a quoted worker count are mutually consistent.

Peak throughput is the default. To measure the rate sustained inside
production headroom instead, add `--cap` with your own endpoint's figures:

```bash
python3 workloads/driver_throughput.py --endpoint http://127.0.0.1:8080 \
    --workload workloads/functional_500.json --runs 10 --workers 16 \
    --cap --qps-cap <your capacity> --u-prod <your utilization>
```

`--cap` has no default capacity or utilization. Those are properties of the
endpoint under test, so the driver requires them rather than assuming any
deployment's values.

## Scaling, Eq. (2d) and (2e)

```bash
python3 workloads/driver_scaling.py \
    --endpoint http://127.0.0.1:8080 \
    --workload workloads/scaling_mixed.json \
    --counts 1,5,10,25,50,100,150 --workers 16 --capacity 28.89
```

`--capacity` is `B`, fixed from the deployed hierarchy
(`g1=1`, `g3=3`, mean `g4=9.63`); the driver never fits it. Output gives
`T(n)`, the interval secants, the four candidate fits ordered by AIC, and
the leave-one-out relative RMSE. AICc prints as `undefined` when
`n - k - 1 <= 0` rather than silently falling back to AIC.

The states-occupied column is the mechanism itself: it saturates at the
state catalog size while the shared-executed count stays flat and only
tenant-specific work grows.

## M2 and M4, reuse and effort

```bash
python3 workloads/driver_onboarding.py --counts 1,10,25,50,100,150
python3 workloads/driver_onboarding.py --counts 1,10 --effort-log effort.json
```

`effort.json` maps a tenant count to cumulative person-hours. Without it
the driver reports artifact counts and says M4 is unavailable; person-hours
are a human record and it will not synthesize them.

## Comparators

See `comparators/README.md` for the protocol and one directory per tool.
The promptfoo dispatch path is the M3 level 3 evidence:

```bash
cd comparators/promptfoo
SUT_ENDPOINT=http://127.0.0.1:8080 ./ci_dispatch.sh tenant-0001 staging 0.75
python3 parse_runs.py runs/
python3 reuse.py --tenants 10
```

Each comparator writes `runs.json` with per-run records, so the 5-unit
measurement grid noted in Table 2 can be confirmed from the raw numbers
rather than taken on trust.

## Semantic evaluation

```bash
python3 workloads/driver_semantic.py \
    --endpoint http://127.0.0.1:8080 \
    --judge-endpoint http://127.0.0.1:8080 \
    --workload workloads/semantic_2000.json --labels labels.json
```

`labels.json` maps a case id to a human meaning-compatibility label.
Without labels the driver reports judge scores and pass rates but no
precision, recall or F1, because those need ground truth. Swap the judge
with `--judge-model` to repeat the open-weight replication of Sec. VII-C1.
