# Comparator configurations

The configurations and drivers used for every third-party framework in
Table 2 (M1, M2) and Table 3 (M4) of the paper. Each directory holds the
configuration as run, plus the command that produced the reported figure.

Nothing here contains SCODA source. These are third-party tool
configurations over public question-answering data, released so the
reported comparisons and their measurement resolution can be checked.

## Measurement protocol, identical for every tool

| Parameter | Value |
|---|---|
| Functional workload | 500 cases, fixed across tools |
| Workers / parallelism | 16 |
| Endpoint | one base URL, same stack for every tool |
| Runs | 5 per tool (10 for SCODA), mean reported |
| Service limit | off for peak; `QPS_cap(1-u_prod)·alpha` when `--cap` is set |
| Warm-up | one discarded pass per run |

Peak throughput is measured without the service limit, which is the default
and what Table 2 reports. Passing `--cap` with an endpoint's own capacity and
utilization measures the rate a tool sustains inside production headroom
instead. The drivers carry no default capacity or utilization figures,
because those belong to the endpoint under test.

## Resolution

M1 and M2 for the tools in `selenium/`, `playwright/` and `deepeval/` were
recorded on a 5-unit grid, coarser than the SCODA and promptfoo figures.
Half-step uncertainty is therefore 0.8 to 7.1 percent across the 320 to 35
tests/min range. The raw per-run records are in each directory's
`runs.json` when a run has been recorded locally, so a reader can confirm
the grid rather than taking the footnote on trust.

## Directories

| Path | Tool | Oracle | Notes |
|---|---|---|---|
| `selenium/` | Selenium WebDriver | structural | browser-driven, one profile per tenant |
| `playwright/` | Playwright | structural | parallel browser contexts |
| `deepeval/` | DeepEval | semantic | model-graded assertions |
| `promptfoo/` | promptfoo | semantic | `--var` dispatch injection, M3 level 3 |

## Running them

Each directory has a `README.md` with the exact invocation. The SCODA side
of every comparison comes from `workloads/driver_throughput.py` with the
same workload file, so the two sides differ only in the tool under test.
