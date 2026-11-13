#!/usr/bin/env bash
# deploy-guard.sh — entry point of the deploy guard, the server-side barrier of the spec-driven
# workflow: a commit of the default branch deploys only when it is the merge of a pull request that
# meets the merge conditions, recomputed here (`merge_conditions.py deploy-guard`), never read from
# the `merge-conditions` status.
#
#   deploy-guard.sh <merged-sha> <before-sha>
#       A GitHub Actions deploy job (its first step) and the deploy-alert workflow. Exit 0 = deploy;
#       any other code = refused (1), cannot judge (2): the step fails, nothing after it runs. Pass
#       the values through the environment, never interpolated into `run:`:
#         env: { MERGED_SHA: ${{ github.sha }}, BEFORE_SHA: ${{ github.event.before }} }
#         run: bash .sdd/bin/deploy-guard.sh "$MERGED_SHA" "$BEFORE_SHA"
#
#   deploy-guard.sh --vercel [<glob>...]
#       Vercel's `ignoreCommand`, whose convention is inverted: exit 1 = build, exit 0 = skip. A
#       build that is not explicitly a preview (VERCEL_ENV=preview) is guarded: it builds only when
#       the guard says deploy and the push changed a path matching one of the globs (every path when
#       none is given); refused, cannot judge, nothing under the globs, a missing tool or a crash all
#       skip. Previews never reach production: they build, unguarded. Vercel is not given the push
#       event, so `before` is read from the repository activity.
#
# Repository: GITHUB_REPOSITORY, or VERCEL_GIT_REPO_OWNER/VERCEL_GIT_REPO_SLUG. Commit (Vercel):
# VERCEL_GIT_COMMIT_SHA. Token, read-only (Contents, Pull requests, Actions, Metadata):
# DEPLOY_GUARD_TOKEN, GH_TOKEN or GITHUB_TOKEN. Needs git and python3; without PyYAML, a private
# virtual environment is created with it (DEPLOY_GUARD_PYTHON overrides the interpreter).
# Copied verbatim by sdd-init (a local edit is overwritten by --refresh); tests:
# .sdd/bin/test_merge_conditions.py (DeployGuardScriptTest).
set -u

here=$(cd "$(dirname "$0")" && pwd)
python=${DEPLOY_GUARD_PYTHON:-python3}
repository=${GITHUB_REPOSITORY:-}
if [ -z "$repository" ] && [ -n "${VERCEL_GIT_REPO_OWNER:-}" ] && [ -n "${VERCEL_GIT_REPO_SLUG:-}" ]; then
  repository="$VERCEL_GIT_REPO_OWNER/$VERCEL_GIT_REPO_SLUG"
fi

# Runs `merge_conditions.py deploy-guard <arguments>`: prints its one line, returns its exit code
# (0 deploy, 1 refused, 2 cannot judge, 3 nothing under the globs; anything else is a crash).
guard() {
  local top venv
  if [ -z "$repository" ]; then
    echo "deploy-guard: cannot judge: repository unknown (GITHUB_REPOSITORY or VERCEL_GIT_REPO_OWNER/SLUG)"
    return 2
  fi
  if ! top=$(git -C "$here" rev-parse --show-toplevel 2>/dev/null); then
    echo "deploy-guard: cannot judge: $here is not inside a git repository"
    return 2
  fi
  if ! "$python" -c 'import yaml' >/dev/null 2>&1; then
    venv="${TMPDIR:-/tmp}/sdd-deploy-guard-venv"
    if ! { "$python" -m venv "$venv" >/dev/null 2>&1 \
           && "$venv/bin/python" -m pip install --quiet --disable-pip-version-check pyyaml==6.0.2 >/dev/null 2>&1; }; then
      echo "deploy-guard: cannot judge: PyYAML is missing and could not be installed"
      return 2
    fi
    python="$venv/bin/python"
  fi
  "$python" "$here/merge_conditions.py" -C "$top" deploy-guard --repo "$repository" "$@"
}

if [ "${1:-}" = "--vercel" ]; then
  shift
  if [ "${VERCEL_ENV:-}" = "preview" ]; then
    echo "deploy-guard: preview build, not guarded (it never reaches production): build"
    exit 1
  fi
  if [ -z "${VERCEL_GIT_COMMIT_SHA:-}" ]; then
    echo "deploy-guard: cannot judge: VERCEL_GIT_COMMIT_SHA is not set (system environment variables exposed?): skip"
    exit 0
  fi
  arguments=(--sha "$VERCEL_GIT_COMMIT_SHA" --before-from-push)
  [ $# -gt 0 ] && arguments+=(--paths "$@")
  guard "${arguments[@]}"
  code=$?
  if [ "$code" -eq 0 ]; then
    echo "deploy-guard: Vercel: build"
    exit 1
  fi
  echo "deploy-guard: Vercel: skip (guard exit $code)"
  exit 0
fi

if [ $# -ne 2 ] || [ -z "$1" ] || [ -z "$2" ]; then
  echo "usage: deploy-guard.sh <merged-sha> <before-sha> | deploy-guard.sh --vercel [<glob>...]" >&2
  exit 2
fi
guard --sha "$1" --before "$2"
code=$?
[ "$code" -eq 0 ] && exit 0
[ "$code" -eq 3 ] && exit 1   # never "nothing to deploy" here: no globs are passed in this mode
exit "$code"
