#!/bin/bash
# One-command eval battery against the real app model (gpt-5.4-mini via the forge).
#
#   ./eval/run_battery.sh              # all pages in pages.yaml, 1 run per case
#   ./eval/run_battery.sh bread        # one page only
#   ./eval/run_battery.sh bread 10     # one page, 10 runs per case (stability check)
#
# First-time setup: cp eval/env.example eval/.env  and fill in FORGE_PASSWORD.
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f eval/.env ]; then
  echo "Missing eval/.env — run: cp eval/env.example eval/.env  and fill in FORGE_PASSWORD"
  exit 1
fi
set -a; source eval/.env; set +a

PAGE_ARG=""
if [ "${1:-}" != "" ]; then PAGE_ARG="--pages $1"; fi
RUNS="${2:-1}"

python3 eval/runner.py --backend forge $PAGE_ARG --runs "$RUNS"
