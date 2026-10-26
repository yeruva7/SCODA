#!/usr/bin/env bash
# Dispatch-time injection for promptfoo, the M3 level 3 evidence of Table 1.
#
# Every tenant parameter arrives as a --var on the command line. No file or
# named profile is authored for the injected value, which is what separates
# level 3 from selecting a pre-authored profile (level 2).
#
#   SUT_ENDPOINT=http://127.0.0.1:8080 ./ci_dispatch.sh tenant-0001 staging 0.75

set -euo pipefail

TENANT="${1:?usage: ci_dispatch.sh <tenant> <tier> <tau>}"
TIER="${2:-staging}"
TAU="${3:-0.75}"
: "${SUT_ENDPOINT:?set SUT_ENDPOINT to the base URL of the system under test}"
: "${JUDGE_ENDPOINT:=http://127.0.0.1:8080}"

export SUT_ENDPOINT JUDGE_ENDPOINT

mkdir -p runs

npx --yes promptfoo@latest eval \
  --config promptfooconfig.yaml \
  --var "tenant=${TENANT}" \
  --var "tier=${TIER}" \
  --var "tau=${TAU}" \
  --max-concurrency 16 \
  --output "runs/${TENANT}.json"

echo "wrote runs/${TENANT}.json"
