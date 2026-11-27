#!/usr/bin/env bash
# Quality gates for one Python package. CI runs exactly this; run it locally too.
#
#   scripts/ci/python-checks.sh <package-dir> [unit|audit|all]
#
#   unit   lock check, ruff lint, ruff format check, pyright strict, pytest with
#          the coverage floor from [tool.coverage.report] (default)
#   audit  known-vulnerability scan of the locked runtime dependencies
#   all    unit, then audit
#
# ruff, pyright and pytest come from the package's uv.lock, so this script, the
# package Makefile and the git hooks always run the same versions. pip-audit is
# pinned here.

set -euo pipefail

PIP_AUDIT_VERSION="2.10.0"

# Advisories with no fix we can install yet. Each entry says why and when to
# re-check; remove it as soon as the blocker is gone.
AUDIT_IGNORES=()

package_dir="${1:?usage: $0 <package-dir> [unit|audit|all]}"
gate="${2:-unit}"

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$repo_root/$package_dir"

step() { printf '\n==> %s: %s\n' "$package_dir" "$1"; }

unit() {
  step "install (locked)"
  uv sync --locked --quiet
  step "ruff check"
  uv run --locked ruff check .
  step "ruff format --check"
  uv run --locked ruff format --check .
  step "pyright (strict)"
  uv run --locked pyright
  step "pytest (with coverage floor)"
  uv run --locked pytest -q --cov --cov-report=term
}

audit() {
  step "pip-audit (locked runtime dependencies)"
  local requirements
  requirements="$(mktemp)"
  # Runtime dependencies only: what ships in the image.
  uv export --locked --no-dev --no-emit-project --no-hashes --quiet \
    | grep -v -E '^(-e |\.|/)' >"$requirements"
  local ignore_args=()
  # The +-guard keeps an empty list working under `set -u` on bash 3.2 (macOS).
  for id in ${AUDIT_IGNORES[@]+"${AUDIT_IGNORES[@]}"}; do
    ignore_args+=(--ignore-vuln "$id")
  done
  uvx "pip-audit@$PIP_AUDIT_VERSION" --strict --disable-pip --no-deps \
    ${ignore_args[@]+"${ignore_args[@]}"} -r "$requirements"
  rm -f "$requirements"
}

case "$gate" in
  unit) unit ;;
  audit) audit ;;
  # Sequential, not `unit && audit`: bash ignores `set -e` inside a function that is
  # part of an && list, so a failing step would not stop the run.
  all)
    unit
    audit
    ;;
  *)
    echo "unknown gate: $gate (expected unit, audit or all)" >&2
    exit 2
    ;;
esac
