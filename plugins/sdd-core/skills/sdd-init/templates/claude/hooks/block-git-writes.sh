#!/bin/bash
# PreToolUse hook (Bash): git guardrail for agents. The rules it enforces: docs/CONTRIBUTING.md §2.
# Agents commit and push feature branches; main only moves through a merged PR.
# Blocked: commit/merge/revert/cherry-pick on main; pushing main (also through HEAD, @ or a
# $-expanded ref), pushing without an explicit remote and branch, force-push (--force-with-lease
# only when ALLOW_FORCE_WITH_LEASE=1, never to main); a branch set to track main (-u,
# --set-upstream-to, --track, or a branch created from origin/main without --no-track); pull without
# --ff-only, with rebase, or (on main) of another branch; history rewriting (rebase, amend, am,
# commit-tree, filter-branch, update-ref, reset to a revision, branch -f); sweeping stages (add
# -A/./*/-u, commit -a); discarding work; --no-verify and commit -n; merging, auto-merging or writing
# a branch through `gh api` (REST merge endpoint, /merges, refs and contents writes, GraphQL merge
# mutations).
# The single merge route: `gh pr merge <n> --<MERGE_METHOD>` (plus --delete-branch, --subject, --body,
# --match-head-commit). Before allowing it the hook asks GitHub itself, never the command line:
# the pull request is open, into the default branch; the `merge-conditions` status of its head
# commit is success with `gates: none`; the `base <sha7>` the check judged against is the default
# branch's current head; no other pull request carries the `in-flight` label. Any failed query,
# or no gh, blocks (fail closed).
# The branch is the one checked out where the command really runs: the tool call's cwd, then each
# `cd`/`pushd`/`popd` and `git -C <dir>` (subshells restore the directory), and a
# `git switch|checkout <branch>` earlier in the same command — to main at once, to another branch
# only when the next command is chained with && (a failed switch stops the chain). A directory or
# branch that cannot be resolved ($-expanded, `cd -`, a directory that does not exist) counts as main.
# Before the checks, the command is read the way the shell reads it (block-git-writes.pl): only
# what the shell runs is left, commit messages and PR bodies are never read as flags or commands.
# Adapted from mattpocock/skills (misc/git-guardrails-claude-code, MIT).
# A guardrail against mistakes, not a sandbox: deliberate evasions (sh -c "...", eval,
# `git --git-dir x commit`) are out of scope.
# Exit 2 = block the tool call and show stderr to the agent. Exit 1 = non-blocking error shown to the user.

INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  if printf '%s' "$INPUT" | grep -qE '(^|[^[:alnum:]_-]|\\[nt])(git|gh)[[:space:]]'; then
    echo "block-git-writes: jq not found — git and gh commands stay blocked until jq is installed (brew install jq)." >&2
    exit 2
  fi
  exit 0
fi

COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
[ -z "$COMMAND" ] && exit 0
set -f

# Read the command the way the shell does (block-git-writes.pl, see its header). Without perl,
# only backslash-continued lines are joined. If the reader fails, git and gh commands are blocked.
HOOK_DIR=$(cd "$(dirname "$0")" && pwd)
if command -v perl >/dev/null 2>&1; then
  if ! NEUTRAL=$(printf "%s" "$COMMAND" | perl "$HOOK_DIR/block-git-writes.pl"); then
    if printf "%s" "$COMMAND" | grep -qE "(^|[^[:alnum:]_-])(git|gh)[[:space:]]"; then
      echo "block-git-writes: the shell reader (block-git-writes.pl) failed — git and gh commands are blocked." >&2
      exit 2
    fi
    exit 0
  fi
else
  NEUTRAL=${COMMAND//$'\\\n'/ }
fi

# Where a command starts: line start, after ; & | ( { ! or $(, after a shell keyword
# (if/then/do/else/while/until) or a wrapper (env, command, exec, nohup, time, sudo, xargs,
# timeout N), or after a VAR=value assignment.
START='(^|[;&|({!]|\$\(|(^|[[:space:]])((if|then|do|else|while|until|env|command|exec|nohup|time|sudo|xargs)|timeout[[:space:]]+[0-9]+[smhd]?|[A-Za-z_][A-Za-z0-9_]*=("[^"]*"|'"'"'[^'"'"']*'"'"'|[^[:space:]]*))[[:space:]])'
# A path or option value: double-quoted, single-quoted, or a word with backslash escapes.
VALUE='("([^"\\]|\\.)*"|'"'"'[^'"'"']*'"'"'|(\\.|[^[:space:]\\])+)'
# Global options before the subcommand: -C dir, -c key=value, --long[=value], -p/-P.
GOPT="[[:space:]]+(-[cC][[:space:]]+${VALUE}|--[a-z-]+(=[^[:space:]]+)?|-[pP])"
# A git invocation at a command position, optionally via a wrapper binary (rtk) or an absolute path.
GIT="${START}[[:space:]]*(rtk[[:space:]]+)?([^[:space:];&|()]*/)?git(${GOPT})*[[:space:]]+"
GH="${START}[[:space:]]*([^[:space:];&|()]*/)?gh[[:space:]]+"
# End of a subcommand word: whitespace, an operator, a redirection, or end of line.
END='([[:space:]]|[;&|)<>]|$)'
# Project settings: block-git-writes.conf next to this script, plain KEY=value lines, never sourced.
#   PROTECTED_BRANCHES  regex alternation of the branches that only move through a merged PR (main|master)
#   ALLOW_PUSH              1 = agents push their branch; 0 = every git push is blocked (a human pushes,
#                           e.g. no remote the agent may push to)
#   MERGE_METHOD            squash | merge: the method of the merge route (default merge). Any other
#                           value, rebase included, blocks every agent merge: the deploy guard needs
#                           the default branch before the merge as one commit, which a rebase merge
#                           does not leave.
#   ALLOW_FORCE_WITH_LEASE  1 = `git push --force-with-lease` allowed to a non-protected branch;
#                           0 (default) = blocked like any force-push
#   A former ALLOW_PR_MERGE line is ignored: whether the agent merges is decided per pull request.
conf() {
  local v
  [ -f "$HOOK_DIR/block-git-writes.conf" ] || return 0
  v=$(grep -E "^$1=" "$HOOK_DIR/block-git-writes.conf" | tail -n 1 | cut -d= -f2- | sed -E 's/[[:space:]]+#.*$//; s/[[:space:]]*$//; s/^["'"'"']//; s/["'"'"']$//')
  printf '%s' "$v"
}
PROTECTED_BRANCHES=$(conf PROTECTED_BRANCHES); ALLOW_PUSH=$(conf ALLOW_PUSH)
MERGE_METHOD=$(conf MERGE_METHOD); ALLOW_FORCE_WITH_LEASE=$(conf ALLOW_FORCE_WITH_LEASE)
[[ "$PROTECTED_BRANCHES" =~ ^[A-Za-z0-9._/|-]+$ ]] || PROTECTED_BRANCHES='main|master'
[ "$ALLOW_PUSH" = 0 ] || ALLOW_PUSH=1
[ "$ALLOW_FORCE_WITH_LEASE" = 1 ] || ALLOW_FORCE_WITH_LEASE=0
[ -n "$MERGE_METHOD" ] || MERGE_METHOD=merge
[[ "$MERGE_METHOD" =~ ^[a-z]{1,16}$ ]] || MERGE_METHOD=invalid
# The labels and statuses the merge route reads (dev-factory: merge-conditions.yml, delivery steps).
STATUS_CONTEXT=merge-conditions
IN_FLIGHT_LABEL=in-flight
# Seconds each GitHub query may take before the merge is blocked.
GH_TIMEOUT=20
# Branches that only move through a merged PR.
PROTECTED="^(${PROTECTED_BRANCHES})$"
# Inside one command segment: git's global options, its subcommand, the rest.
GITCMD_RE="(^|[[:space:]/])git((${GOPT})*)[[:space:]]+([a-z][a-z-]*)(.*)"
C_RE="-C[[:space:]]+${VALUE}(.*)"
KEYWORDS='^[[:space:]]*((if|then|do|else|while|until|!)[[:space:]]+)*'
CD_RE="${KEYWORDS}(cd|pushd)(([[:space:]]+-[LPe@]+)*)([[:space:]]+${VALUE})?([[:space:]]|$)"
POPD_RE="${KEYWORDS}popd([[:space:]]|$)"

# `git [-C dir] merge|rebase|cherry-pick|revert|am --abort|--quit` only leaves an operation in
# progress (e.g. a conflict the user opened): it is neutralised before the checks, the rest of the
# command is still checked (`git rebase --abort && git push` stays blocked).
CHECKED=$(printf '%s' "$NEUTRAL" | sed -E 's/(^|[^[:alnum:]_.\/-])git([[:space:]]+-[cC][[:space:]]+[^[:space:]]+)*[[:space:]]+(merge|rebase|cherry-pick|revert|am)[[:space:]]+--(abort|quit)([[:space:]]|[;&|)]|$)/\1true\5/g')

block() {
  echo "BLOCKED by .claude/hooks/block-git-writes.sh: '$COMMAND' — $1. Project git rules: docs/CONTRIBUTING.md §2." >&2
  exit 2
}

# check <pattern> <reason>: blocks when the pattern matches anywhere in the command.
check() {
  printf '%s' "$CHECKED" | grep -qE -- "$1"
  local rc=$?
  [ "$rc" -eq 0 ] && block "$2"
  if [ "$rc" -ne 1 ]; then
    echo "block-git-writes: pattern error (grep exit $rc) on '$1' — the guardrail is degraded." >&2
    exit 1
  fi
}

# matches <segment> <pattern>
matches() {
  printf '%s' "$1" | grep -qE -- "$2"
}

unquote() {
  local w=${1//\"/}
  printf '%s' "${w//\'/}"
}

# resolve_dir <base> <path>: the directory a cd/pushd/-C lands in, or "?" when it cannot be known.
resolve_dir() {
  local base=$1 p=$2
  [ "$base" = "?" ] && { echo "?"; return; }
  case "$p" in
    \"*\") p=${p#\"}; p=${p%\"} ;;
    \'*\') p=${p#\'}; p=${p%\'} ;;
    *) p=$(printf '%s' "$p" | sed -E 's/\\(.)/\1/g') ;;
  esac
  case "$p" in *'$'*|*'`'*|-|'') echo "?"; return ;; esac
  case "$p" in '~') p=$HOME ;; '~/'*) p="$HOME/${p#\~/}" ;; esac
  case "$p" in /*) ;; *) p="$base/$p" ;; esac
  [ -d "$p" ] || { echo "?"; return; }
  echo "$p"
}

top_of() {
  [ "$1" = "?" ] && { echo "?"; return; }
  git -C "$1" rev-parse --show-toplevel 2>/dev/null || echo "$1"
}

# A `git switch|checkout` earlier in the same command overrides the checked-out branch of its repo.
OV_TOP=
OV_BRANCH=
branch_of() {
  local top
  top=$(top_of "$1")
  [ "$top" = "?" ] && { echo "?"; return; }
  if [ -n "$OV_TOP" ] && [ "$top" = "$OV_TOP" ]; then
    echo "$OV_BRANCH"
    return
  fi
  git -C "$top" symbolic-ref --quiet --short HEAD 2>/dev/null
}

protected() {
  [ "$1" = "?" ] || [[ "$1" =~ $PROTECTED ]]
}

describe() {
  if [ "$1" = "?" ]; then echo "an unresolvable directory or branch (counts as main)"; else echo "$1"; fi
}

# track_switch <dir> <words...>
track_switch() {
  local dir=$1 w new= orphan=0 target= pos=0 top track=default
  shift
  while [ $# -gt 0 ]; do
    w=$(unquote "$1")
    shift
    case "$w" in
      '>'|'>>'|[0-9]'>'|[0-9]'>>'|'<') shift ;;
      [0-9]'>'*|'>'*|'<'*) ;;
      -) pos=$((pos + 1)); [ -z "$target" ] && target=- ;;
      -c|-b|--create) new=$(unquote "$1"); shift ;;
      --orphan) new=$(unquote "$1"); orphan=1; shift ;;
      -t|--track|--track=direct) track=direct ;;
      --track=inherit) track=inherit ;;
      --no-track) track=no ;;
      --detach|-d) target=DETACHED ;;
      --) return ;;
      -*) ;;
      *) pos=$((pos + 1)); [ -z "$target" ] && target=$w ;;
    esac
  done
  top=$(top_of "$dir")
  if [ -n "$new" ] && [ "$orphan" = 0 ] && ! [[ "$new" =~ $PROTECTED ]] && tracks_protected "$dir" "$track" "$target"; then
    block "$new would track a protected branch: create it with --no-track (git switch -c $new --no-track <start>)"
  fi
  # `switch --track <remote>/<branch>` creates and switches to <branch>.
  if [ -z "$new" ] && [ "$track" != default ] && [ "$track" != no ] && [ -n "$target" ]; then
    set -- $(ref_branch "$top" "$target")
    [ "$1" = remote ] && target=$2
  fi
  if [ -n "$new" ]; then
    case "$new" in *'$'*) new="?" ;; esac
    switch_to "$top" "$new"
    return
  fi
  # `checkout <tree-ish> <paths>` restores files, it does not switch.
  [ "$pos" -ge 2 ] && return
  case "$target" in
    '') return ;;
    DETACHED) switch_to "$top" "" ;;
    -|*'$'*) switch_to "$top" "?" ;;
    *)
      if [[ "$target" =~ $PROTECTED ]] \
        || git -C "$top" show-ref --verify --quiet "refs/heads/$target" 2>/dev/null \
        || [ -n "$(git -C "$top" for-each-ref --count=1 --format='%(refname)' "refs/remotes/*/$target" 2>/dev/null)" ]; then
        switch_to "$top" "$target"
      fi
      ;;
  esac
}

# ref_branch <top> <ref>: "local <branch>" or "remote <branch>" for a start point or an upstream:
# refs/heads/x, refs/remotes/<r>/x, and <r>/x when <r> is a remote of the repository (any <r>/x when
# the repository cannot be resolved).
ref_branch() {
  local top=$1 r=$2
  case "$r" in
    refs/heads/*) echo "local ${r#refs/heads/}"; return ;;
    refs/remotes/*/*) r=${r#refs/remotes/}; echo "remote ${r#*/}"; return ;;
    */*)
      if [ "$top" = "?" ] || git -C "$top" remote 2>/dev/null | grep -qxF -- "${r%%/*}" \
        || git -C "$top" show-ref --verify --quiet "refs/remotes/$r" 2>/dev/null; then
        echo "remote ${r#*/}"
        return
      fi
      ;;
  esac
  echo "local $r"
}

# tracks_protected <dir> <track> <start point>: whether a branch created from <start point> gets a
# protected branch as its upstream. <track>: direct (--track), inherit (--track=inherit), no
# (--no-track) or default, which follows the repository's branch.autoSetupMerge as git does (true,
# git's default: only a remote-tracking start point is tracked). An unresolvable start point counts
# as main.
tracks_protected() {
  local dir=$1 track=$2 start=$3 top setup up
  [ "$track" = no ] && return 1
  top=$(top_of "$dir")
  if [ "$track" = default ]; then
    setup=
    [ "$top" = "?" ] || setup=$(git -C "$top" config --get branch.autoSetupMerge 2>/dev/null)
    case "$setup" in
      false|simple) return 1 ;;
      always) track=direct ;;
      inherit) track=inherit ;;
      *) track=remote ;;
    esac
  fi
  if [ -z "$start" ]; then
    [ "$track" = inherit ] || return 1
    start=$(branch_of "$dir")
    [ -n "$start" ] || return 1
  fi
  case "$start" in *'$'*|'?'|-) return 0 ;; esac
  set -- $(ref_branch "$top" "$start")
  if [ "$track" = remote ]; then
    [ "$1" = remote ] || return 1
  elif [ "$track" = inherit ] && [ "$1" = local ]; then
    up=
    [ "$top" = "?" ] || up=$(git -C "$top" config --get "branch.$2.merge" 2>/dev/null)
    up=${up#refs/heads/}
    [ -n "$up" ] && [[ "$up" =~ $PROTECTED ]]
    return
  fi
  [[ "$2" =~ $PROTECTED ]]
}

# check_branch <dir> <words...>: `git branch` never sets a protected branch as the upstream of
# another branch (-u, --set-upstream-to, or creating a branch that tracks it).
check_branch() {
  local dir=$1 w upstream= set_up=0 track=default other=0 target first= second= count=0
  shift
  while [ $# -gt 0 ]; do
    w=$(unquote "$1")
    shift
    case "$w" in
      -u|--set-upstream-to) set_up=1; upstream=$(unquote "$1"); shift ;;
      --set-upstream-to=*) set_up=1; upstream=${w#*=} ;;
      -u?*) set_up=1; upstream=${w#-u} ;;
      -t|--track|--track=direct) track=direct ;;
      --track=inherit) track=inherit ;;
      --no-track) track=no ;;
      '>'|'>>'|[0-9]'>'|[0-9]'>>'|'<') shift ;;
      [0-9]'>'*|'>'*|'<'*) ;;
      --) ;;
      --create-reflog|--recurse-submodules|-q|--quiet) ;;
      -*) other=1 ;;
      *)
        count=$((count + 1))
        [ "$count" = 1 ] && first=$w
        [ "$count" = 2 ] && second=$w
        ;;
    esac
  done
  if [ "$set_up" = 1 ]; then
    target=${first:-$(branch_of "$dir")}
    [ -n "$target" ] && [ "$target" != "?" ] && [[ "$target" =~ $PROTECTED ]] && return
    case "$upstream" in *'$'*|'') block "the upstream cannot be resolved: name it literally, never a protected branch" ;; esac
    set -- $(ref_branch "$(top_of "$dir")" "$upstream")
    [[ "$2" =~ $PROTECTED ]] && block "never let a branch track $2: it would pull and push the protected branch (git branch --unset-upstream)"
    return
  fi
  # Listing, deleting, renaming, copying: no new upstream.
  [ "$other" = 0 ] && [ "$count" -ge 1 ] && [ "$count" -le 2 ] || return
  [[ "$first" =~ $PROTECTED ]] && return
  tracks_protected "$dir" "$track" "$second" \
    && block "$first would track a protected branch: create it with --no-track (git branch --no-track $first <start>)"
}

# check_worktree <dir> <words...>: `worktree add -b <new> <path> <start>` follows the same rule.
check_worktree() {
  local dir=$1 w new= track=default pos=0 start=
  shift
  [ "$(unquote "$1")" = add ] || return
  shift
  while [ $# -gt 0 ]; do
    w=$(unquote "$1")
    shift
    case "$w" in
      -b|-B) new=$(unquote "$1"); shift ;;
      --track) track=direct ;;
      --no-track) track=no ;;
      --reason) shift ;;
      '>'|'>>'|[0-9]'>'|[0-9]'>>'|'<') shift ;;
      [0-9]'>'*|'>'*|'<'*) ;;
      -*) ;;
      *) pos=$((pos + 1)); [ "$pos" = 2 ] && start=$w ;;
    esac
  done
  [ -n "$new" ] || return
  [[ "$new" =~ $PROTECTED ]] && return
  tracks_protected "$dir" "$track" "$start" \
    && block "$new would track a protected branch: add --no-track (git worktree add --no-track -b $new <dir> <start>)"
}

# switch_to <top> <branch>: a switch to main (or to an unknown branch) counts at once; to another
# branch it stays pending until the next command is chained with &&.
PEND=0
PEND_TOP=
PEND_BRANCH=
switch_to() {
  if protected "$2"; then
    OV_TOP=$1
    OV_BRANCH=$2
    PEND=0
  else
    PEND=1
    PEND_TOP=$1
    PEND_BRANCH=$2
  fi
}

# check_reset <dir> <words...>: `reset <commit>` (other than HEAD) moves the branch back.
check_reset() {
  local dir=$1 w pos=0 rev= top
  shift
  for w in "$@"; do
    w=$(unquote "$w")
    case "$w" in
      --) return ;;
      -*|[0-9]'>'*|'>'*|'<'*) ;;
      *) pos=$((pos + 1)); [ "$pos" = 1 ] && rev=$w ;;
    esac
  done
  [ "$pos" = 1 ] || return
  case "$rev" in HEAD|@) return ;; esac
  top=$(top_of "$dir")
  [ "$top" = "?" ] && return
  git -C "$top" rev-parse --verify --quiet "$rev^{commit}" >/dev/null 2>&1 \
    && block "never move a branch back: add a new commit (git revert)"
}

# check_pull <dir> <words...>: --ff-only only, no rebase; on main, only main itself.
check_pull() {
  local dir=$1 w pos=0 second= br ref
  shift
  case " $* " in *" --ff-only "*) ;; *) block "pull only with --ff-only" ;; esac
  case " $* " in *" --rebase"*|*" -r "*) block "never pull with rebase" ;; esac
  for w in "$@"; do
    w=$(unquote "$w")
    case "$w" in
      -*|[0-9]'>'*|'>'*|'<'*) ;;
      *) pos=$((pos + 1)); [ "$pos" = 2 ] && second=$w ;;
    esac
  done
  [ -z "$second" ] && return
  br=$(branch_of "$dir")
  if protected "$br"; then
    ref=${second%%:*}
    ref=${ref#+}
    ref=${ref#refs/heads/}
    [[ "$ref" =~ $PROTECTED ]] || block "on $(describe "$br"), pull only main itself: git pull --ff-only [origin main]"
  fi
}

# check_push <dir> <words...>: explicit remote and branch, never main, never forced.
check_push() {
  local dir=$1 w ref positional=0 skip=0 br= br_read=0 lease=0 includes=0
  shift
  for w in "$@"; do
    if [ "$skip" = 1 ]; then
      skip=0
      continue
    fi
    w=$(unquote "$w")
    case "$w" in
      '') ;;
      --force-with-lease|--force-with-lease=*)
        [ "$ALLOW_FORCE_WITH_LEASE" = 1 ] || block "never force-push (--force-with-lease is off in this project: ALLOW_FORCE_WITH_LEASE=0)"
        lease=1
        ;;
      --force-if-includes) includes=1 ;;
      --force*|--mirror|--all|--prune) block "never force-push nor push every ref" ;;
      -o|--push-option|--receive-pack|--exec) skip=1 ;;
      --repo) skip=1; positional=$((positional + 1)) ;;
      --repo=*) positional=$((positional + 1)) ;;
      --*) ;;
      -*f*) block "never force-push" ;;
      -*) ;;
      '>'|'>>'|[0-9]'>'|[0-9]'>>'|'<') skip=1 ;;
      [0-9]'>'*|'>'*|'<'*) ;;
      *)
        positional=$((positional + 1))
        [ "${w#+}" != "$w" ] && block "never force-push (+refspec)"
        [ "$positional" -lt 2 ] && continue
        ref=${w##*:}
        ref=${ref#refs/heads/}
        case "$ref" in
          HEAD|@|*'$'*)
            if [ "$br_read" = 0 ]; then br=$(branch_of "$dir"); br_read=1; fi
            protected "$br" && block "never push $(describe "$br"): it only moves through a merged PR"
            ;;
        esac
        [[ "$ref" =~ $PROTECTED ]] && block "never push $ref: it only moves through a merged PR"
        ;;
    esac
  done
  [ "$includes" = 1 ] && [ "$lease" = 0 ] && block "never force-push (--force-if-includes)"
  [ "$positional" -lt 2 ] && block "name the remote and the branch explicitly: git push -u origin <branch>"
}

# check_gh_api: `gh api` never merges, auto-merges or writes a branch. Read on the raw command, not
# the neutralised one: API paths ("repos/{owner}/{repo}/…") and GraphQL queries are usually quoted
# with braces, which the reader blanks and the segment split cuts.
check_gh_api() {
  local raw=$COMMAND write=0
  raw_has() { printf '%s' "$raw" | grep -qE -- "$1"; }
  raw_has '(^|[[:space:]])(-X|--method)([[:space:]]+|=)?["'"'"']?(POST|PUT|PATCH|DELETE|post|put|patch|delete)|(^|[[:space:]])(-f|-F|--field|--raw-field|--input)([[:space:]]|=|$)' && write=1
  raw_has 'pulls/[^/[:space:]]+/merge([^[:alnum:]_-]|$)' \
    && block "never merge through the REST API: the only merge route is gh pr merge <n> --$MERGE_METHOD"
  raw_has 'repos/[^[:space:]]+/merges([^[:alnum:]_/-]|$)' && block "never merge branches through the API"
  raw_has '(enablePullRequestAutoMerge|mergePullRequest|enqueuePullRequest|mergeBranch|createCommitOnBranch|updateRefs?)([^[:alnum:]]|$)' \
    && block "never merge, auto-merge or write a branch through the GraphQL API"
  [ "$write" = 1 ] || return 0
  raw_has "git/refs/heads/(${PROTECTED_BRANCHES})([^[:alnum:]_./-]|\$)" && block "never write a protected branch through the API"
  raw_has 'repos/[^[:space:]]+/contents/' && block "never commit through the contents API: commit on the change branch"
  return 0
}

# check_gh_merge <dir> <segment>: the single merge route, `gh pr merge <n> --<MERGE_METHOD>`, then
# verified on GitHub (verify_merge). `--disable-auto` alone only cancels an automatic merge.
check_gh_merge() {
  local dir=$1 w number= method= methods=0 disable=0 match= seen=0
  set -- $2
  while [ $# -gt 0 ]; do
    w=$1
    shift
    if [ "$seen" = 0 ]; then
      case "$w" in
        GH_REPO=*|GH_HOST=*) block "run gh pr merge in the repository's checkout, without GH_REPO/GH_HOST: the merge conditions are checked for that repository" ;;
        merge) seen=1 ;;
      esac
      continue
    fi
    w=$(unquote "$w")
    case "$w" in
      --merge|-m) method=merge; methods=$((methods + 1)) ;;
      --squash|-s) method=squash; methods=$((methods + 1)) ;;
      --rebase|-r) method=rebase; methods=$((methods + 1)) ;;
      --admin|--auto) block "never bypass or defer the merge conditions (--admin, --auto)" ;;
      --disable-auto) disable=1 ;;
      --delete-branch|-d) ;;
      --subject|-t|--body|-b|--body-file|-F|--author-email|-A) shift ;;
      --subject=*|--body=*|--body-file=*|--author-email=*) ;;
      --match-head-commit) match=$(unquote "$1"); shift ;;
      --match-head-commit=*) match=${w#*=} ;;
      -R|-R?*|--repo|--repo=*) block "run gh pr merge in the repository's checkout, without --repo: the merge conditions are checked for that repository" ;;
      '>'|'>>'|[0-9]'>'|[0-9]'>>'|'<') shift ;;
      [0-9]'>'*|'>'*|'<'*) ;;
      -*) block "unknown gh pr merge option $w: the merge route is gh pr merge <n> --$MERGE_METHOD [--delete-branch]" ;;
      *)
        [ -z "$number" ] || block "merge one pull request, named by its number: gh pr merge <n> --$MERGE_METHOD"
        number=$w
        ;;
    esac
  done
  if [ "$disable" = 1 ]; then
    [ "$methods" = 0 ] || block "--disable-auto only cancels an automatic merge: run it alone"
    return
  fi
  case "$MERGE_METHOD" in
    squash|merge) ;;
    *) block "MERGE_METHOD=$MERGE_METHOD in block-git-writes.conf is neither squash nor merge (rebase is refused: the deploy guard needs the default branch before the merge as one commit): no agent merge until it is fixed" ;;
  esac
  [ "$methods" = 1 ] && [ "$method" = "$MERGE_METHOD" ] || block "merge with the project's method only: gh pr merge <n> --$MERGE_METHOD"
  [[ "$number" =~ ^[0-9]+$ ]] || block "name the pull request by its number: gh pr merge <n> --$MERGE_METHOD"
  [ "$dir" = "?" ] && block "the directory the merge runs in cannot be resolved: run gh pr merge from the repository's checkout"
  verify_merge "$dir" "$number" "$match"
}

# gh_query <dir> <gh arguments...>: gh's output, run in <dir> (gh resolves the repository there, as
# the merge itself will), non-interactive and bounded by GH_TIMEOUT seconds. Fails when gh fails.
gh_query() {
  local dir=$1
  shift
  (
    cd "$dir" 2>/dev/null || exit 1
    export GH_PROMPT_DISABLED=1 GH_PAGER=cat NO_COLOR=1
    command -v perl >/dev/null 2>&1 || exec gh "$@"
    exec perl -e 'my $t = shift; my $pid = fork; exit 1 unless defined $pid;
      if ($pid == 0) { exec @ARGV or exit 127 }
      $SIG{ALRM} = sub { kill "TERM", $pid; exit 124 };
      alarm $t; waitpid($pid, 0); exit(($? & 127) ? 1 : ($? >> 8));' "$GH_TIMEOUT" gh "$@"
  ) 2>/dev/null
}

fail_closed() {
  block "could not obtain $1 from GitHub, so the merge is blocked (fail closed): retry, or hand the merge to the owner"
}

# verify_merge <dir> <number> <expected head or empty>: asks GitHub, never the command line, whether
# the agent may merge the pull request now (see the header). Blocks with the reason otherwise.
verify_merge() {
  local dir=$1 n=$2 match=$3 out slug default state head base found st desc judged tip others
  local re='^gates: none; base ([0-9a-f]{7})$'
  command -v gh >/dev/null 2>&1 || block "gh not found: the merge route verifies $STATUS_CONTEXT on GitHub before merging (fail closed): install gh, or hand the merge to the owner"
  out=$(gh_query "$dir" repo view --json nameWithOwner,defaultBranchRef) || fail_closed "the repository (gh repo view)"
  slug=$(printf '%s' "$out" | jq -r '.nameWithOwner // "-"' 2>/dev/null)
  default=$(printf '%s' "$out" | jq -r '.defaultBranchRef.name // "-"' 2>/dev/null)
  [[ "$slug" =~ ^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$ ]] && [[ "$default" =~ ^[A-Za-z0-9._/-]+$ ]] \
    || fail_closed "the repository (gh repo view)"
  out=$(gh_query "$dir" api "repos/$slug/pulls/$n") || fail_closed "pull request #$n"
  state=$(printf '%s' "$out" | jq -r '.state // "-"' 2>/dev/null)
  head=$(printf '%s' "$out" | jq -r '.head.sha // "-"' 2>/dev/null)
  base=$(printf '%s' "$out" | jq -r '.base.ref // "-"' 2>/dev/null)
  [[ "$head" =~ ^[0-9a-f]{40}$ ]] && [ -n "$state" ] && [ "$base" != "-" ] || fail_closed "pull request #$n"
  [ "$state" = open ] || block "pull request #$n is not open (state: $state)"
  [ "$base" = "$default" ] || block "pull request #$n targets $base, not the default branch $default: the agent merges only into the default branch"
  [ -z "$match" ] || [ "$match" = "$head" ] || block "--match-head-commit $match is not the head of #$n (${head:0:12})"
  out=$(gh_query "$dir" api "repos/$slug/commits/$head/status?per_page=100") || fail_closed "the $STATUS_CONTEXT status of #$n"
  found=$(printf '%s' "$out" | jq -r --arg c "$STATUS_CONTEXT" \
    'if (.statuses | type) != "array" then error("no statuses") else
       [.sha // "", ([.statuses[] | select(.context == $c)] | first | if . == null then "none" else .state // "-" end)] | join(" ")
     end' 2>/dev/null) || fail_closed "the $STATUS_CONTEXT status of #$n"
  [ "${found%% *}" = "$head" ] || fail_closed "the $STATUS_CONTEXT status of #$n's head commit"
  st=${found#* }
  desc=$(printf '%s' "$out" | jq -r --arg c "$STATUS_CONTEXT" '[.statuses[] | select(.context == $c)] | first | .description // ""' 2>/dev/null)
  desc=${desc:0:140}
  case "$st" in
    none) block "no $STATUS_CONTEXT status on the head commit ${head:0:7} of #$n: wait for the check (a status on an older commit does not count)" ;;
    success) ;;
    pending) block "$STATUS_CONTEXT is pending on #$n ($desc): wait for it, then merge" ;;
    *) block "$STATUS_CONTEXT is $st on #$n ($desc): fix the pull request; the agent never merges it as it is" ;;
  esac
  case "$desc" in
    'gates: none' | 'gates: none;'*) ;;
    *) block "$STATUS_CONTEXT does not report 'gates: none' on #$n ($desc): hand the merge to the owner, whose merge stands for the go or the passed QA" ;;
  esac
  [[ "$desc" =~ $re ]] || block "$STATUS_CONTEXT on #$n does not name the $default commit it judged against, base <sha7> ($desc): wait for the re-judgement"
  judged=${BASH_REMATCH[1]}
  out=$(gh_query "$dir" api "repos/$slug/branches/$default") || fail_closed "the head of $default"
  tip=$(printf '%s' "$out" | jq -r '.commit.sha // "-"' 2>/dev/null)
  [[ "$tip" =~ ^[0-9a-f]{40}$ ]] || fail_closed "the head of $default"
  [ "${tip:0:7}" = "$judged" ] || block "$default moved since $STATUS_CONTEXT judged #$n (against $judged, $default is now ${tip:0:7}): wait for the re-judgement"
  # In flight = any other pull request carrying the label, whatever its state: the agent labels the
  # pull request it merged and removes the label once production is verified or rolled back.
  out=$(gh_query "$dir" pr list --label "$IN_FLIGHT_LABEL" --state all --limit 100 --json number) \
    || fail_closed "the pull requests in flight"
  others=$(printf '%s' "$out" | jq -r --argjson n "$n" \
    'if type != "array" then error("not a list") else [.[] | select(.number != $n) | "#\(.number)"] | join(" ") end' 2>/dev/null) \
    || fail_closed "the pull requests in flight"
  [ -z "$others" ] || block "another change is in flight ($others carries the $IN_FLIGHT_LABEL label): wait until it is verified in production or rolled back"
}

# --- Blocked wherever they run.
# History rewriting and raw commit creation.
check "${GIT}(rebase|am|commit-tree|filter-branch|filter-repo)${END}" "history rewriting is never delegated"
check "${GIT}update-ref${END}" "never move a ref by hand: add a new commit"
check "${GIT}commit[[:space:]][^;&|]*--amend" "never amend a commit: add a new one"
check "${GIT}reset[[:space:]]([^;&|]*[[:space:]])?[\"']?(--soft|--mixed|--hard|--keep|--merge|[^[:space:];&|]*[~^][^[:space:];&|]*|[^[:space:];&|]*@\{[^[:space:];&|]*)[\"']?${END}" "never move a branch back: add a new commit (git revert)"
# Sweeping stages: commit explicit paths only (parallel sessions share checkouts).
check "${GIT}commit[[:space:]]([^;&|]*[[:space:]])?(-[a-zA-Z]*a[a-zA-Z]*|--all)${END}" "commit -a sweeps every tracked change: stage explicit paths"
check "${GIT}add[[:space:]]([^;&|]*[[:space:]])?(-A|--all|-u|--update|\.|\./|\.\.|\.\./|\*|:/)${END}" "stage explicit paths, never the whole tree"
# Discarding work.
check "${GIT}clean[[:space:]]([^;&|]*[[:space:]])?(-[a-zA-Z]*f|--force)" "never discard work"
check "${GIT}checkout[[:space:]]([^;&|]*[[:space:]])?(\.|-f|--force|-B)${END}" "never discard work"
check "${GIT}switch[[:space:]]([^;&|]*[[:space:]])?(-f|--force|--discard-changes|-C|--force-create)${END}" "never discard work"
check "${GIT}worktree[[:space:]]+remove[[:space:]]([^;&|]*[[:space:]])?(-f|--force)${END}" "never discard work"
check "${GIT}restore[[:space:]]([^;&|]*[[:space:]])?\.${END}" "never discard work"
check "${GIT}stash[[:space:]]+(drop|clear)" "never discard work"
# Force-deleting, force-renaming or force-moving a branch: -D, -M, -f, combined -df/-fd.
check "${GIT}branch[[:space:]]([^;&|]*[[:space:]])?(-D|-M|-f|--force|-[a-zA-Z]*(df|fd)[a-zA-Z]*)${END}" "never force-delete, force-rename or force-move a branch"
# Skipping hooks. Only inside a git command: a bare match also blocked heredocs and greps
# that merely mention the flag.
check "${GIT}[^;&|]*--no-verify" "never skip hooks"
check "${GIT}commit[[:space:]]([^;&|]*[[:space:]])?-[a-zA-Z]*n[a-zA-Z]*${END}" "never skip hooks (commit -n is --no-verify)"

# --- Checked per command segment, in order, following the directory and branch.
# `&&` and parentheses (subshells, command substitutions) become segments of their own: a pending
# switch needs the &&, a subshell restores the directory on exit. The `&` of a redirection
# (`2>&1`, `&>file`) is dropped first, so it neither splits a command nor breaks an && chain.
SEGMENTS=$(printf '%s' "$CHECKED" | sed -E -e 's/[0-9]*>&[0-9-]*/ /g' -e 's/&>(>?)/>\1/g' -e 's/&&/\
@AND@\
/g' -e 's/([()])/\
\1\
/g' | tr ';&|{}`' '\n\n\n\n\n\n')
DIR=${CWD:-$PWD}
SUBSHELLS=()
PUSHED=()
while IFS= read -r seg; do
  trimmed=${seg#"${seg%%[![:space:]]*}"}
  trimmed=${trimmed%"${trimmed##*[![:space:]]}"}
  case "$trimmed" in
    '') continue ;;
    @AND@)
      if [ "$PEND" = 1 ]; then OV_TOP=$PEND_TOP; OV_BRANCH=$PEND_BRANCH; fi
      PEND=0
      continue
      ;;
  esac
  PEND=0
  case "$trimmed" in
    '(') SUBSHELLS[${#SUBSHELLS[@]}]=$DIR; continue ;;
    ')')
      k=${#SUBSHELLS[@]}
      if [ "$k" -gt 0 ]; then DIR=${SUBSHELLS[$((k - 1))]}; unset "SUBSHELLS[$((k - 1))]"; fi
      continue
      ;;
  esac
  # Cheap pre-filter: only segments that may move the directory or run git/gh are parsed.
  case "$seg" in *git*|*gh*|*cd*|*pushd*|*popd*) ;; *) continue ;; esac
  if [[ "$seg" =~ $POPD_RE ]]; then
    k=${#PUSHED[@]}
    if [ "$k" -gt 0 ]; then DIR=${PUSHED[$((k - 1))]}; unset "PUSHED[$((k - 1))]"; else DIR="?"; fi
    continue
  fi
  if [[ "$seg" =~ $CD_RE ]]; then
    verb=${BASH_REMATCH[3]}
    target=${BASH_REMATCH[7]}
    [ "$verb" = pushd ] && PUSHED[${#PUSHED[@]}]=$DIR
    if [ -n "$target" ]; then DIR=$(resolve_dir "$DIR" "$target"); else DIR=$HOME; fi
    continue
  fi
  if matches "$seg" "${GH}api${END}"; then
    check_gh_api
    continue
  fi
  if matches "$seg" "${GH}pr[[:space:]]+merge${END}"; then
    check_gh_merge "$DIR" "$seg"
    continue
  fi
  matches "$seg" "$GIT" || continue
  [[ "$seg" =~ $GITCMD_RE ]] || continue
  n=${#BASH_REMATCH[@]}
  opts=${BASH_REMATCH[2]}
  sub=${BASH_REMATCH[$((n - 2))]}
  rest=${BASH_REMATCH[$((n - 1))]}
  eff=$DIR
  while [[ "$opts" =~ $C_RE ]]; do
    eff=$(resolve_dir "$eff" "${BASH_REMATCH[1]}")
    opts=${BASH_REMATCH[$((${#BASH_REMATCH[@]} - 1))]}
  done
  case "$sub" in
    switch|checkout) track_switch "$eff" $rest ;;
    branch) check_branch "$eff" $rest ;;
    worktree) check_worktree "$eff" $rest ;;
    commit|merge|revert|cherry-pick)
      br=$(branch_of "$eff")
      protected "$br" && block "never $sub on $(describe "$br"): work on a branch, main only moves through a merged PR"
      ;;
    reset) check_reset "$eff" $rest ;;
    pull) check_pull "$eff" $rest ;;
    push)
      [ "$ALLOW_PUSH" = 1 ] || block "a human pushes in this project (ALLOW_PUSH=0): commit on the branch and stop"
      check_push "$eff" $rest
      ;;
  esac
done <<< "$SEGMENTS"
exit 0
