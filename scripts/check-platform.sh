#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$repo_dir"
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) { console.error("Use Node 22.13 or newer (mobile/.nvmrc)"); process.exit(1); }'
export PATH="$(dirname "$(node -p 'process.execPath')"):$PATH"
node scripts/sync-brand.mjs --check
node --test packages/api-client/test/*.test.js mobile/test/*.test.js
"$repo_dir/backend/.venv/bin/python" -m unittest discover -s backend/tests
(cd frontend && CI=true ./node_modules/.bin/craco test --watchAll=false --runInBand)
(cd mobile && ./node_modules/.bin/tsc --noEmit)
if [[ "${1:-}" == "--build" ]]; then
  (cd frontend && GENERATE_SOURCEMAP=false ./node_modules/.bin/craco build)
  (cd mobile && CI=1 EXPO_NO_TELEMETRY=1 ./node_modules/.bin/expo export --platform all --clear)
fi
