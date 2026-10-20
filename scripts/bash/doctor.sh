#!/usr/bin/env bash
# Read-only Spec Kit diagnostic. Usage: doctor.sh [--json] [--help]
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_command="${PYTHON:-python3}"
if ! command -v "$python_command" >/dev/null 2>&1; then
    echo 'Project Health Check requires Python 3; set PYTHON to its executable.' >&2
    exit 2
fi
exec "$python_command" -B "$script_dir/../doctor.py" "$@"
