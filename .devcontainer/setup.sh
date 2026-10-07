#!/usr/bin/env bash
set -euo pipefail
psychomark_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$psychomark_root"
uv sync --frozen --extra dev
.venv/bin/python -m psychomark --help > /dev/null
printf '%s\n' 'PsychoMark installé. Le serveur de développement démarrera automatiquement.'
