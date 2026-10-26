# promptfoo, the closest prior art

promptfoo reaches M3 level 3: a value passed with `--var` at dispatch
reaches the running test with no file authored for it. See
`ci_dispatch.sh`, which is the invocation used for the reported figures.

What it does not document is tenant-level inheritance with override
precedence (R4). `tenants/` shows why: each tenant needs its own file, and
a shared default changes only by editing every file or by templating
outside the tool. That is the M2 reuse difference in Table 3, not a claim
about speed.

## Reproducing the reported figures

M1, throughput on the 500-case functional workload:

```bash
export SUT_ENDPOINT=http://127.0.0.1:8080
export JUDGE_ENDPOINT=http://127.0.0.1:8080
./ci_dispatch.sh tenant-0001 staging 0.75
python3 parse_runs.py runs/            # tests/min per run, mean, 95% CI
```

M2, file reuse at a tenant count:

```bash
python3 reuse.py --tenants 10          # inherited vs authored artifacts
```

M4, onboarding effort, needs recorded person-hours; `reuse.py` reports the
artifact counts only and will not synthesize an effort figure.

## Protocol parity

Same workload file, same endpoint, same 16-way concurrency, five runs, mean
reported, one warm-up pass discarded. The only difference from the SCODA
side is the tool under test.
