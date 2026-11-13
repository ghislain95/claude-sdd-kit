#!/usr/bin/env python3
"""merge-conditions — trigger matcher and merge-conditions check of the spec-driven workflow.

Subcommands
  match     Classify a pull request's diff against `.sdd/triggers.yaml` and the approved
            `classification.yaml`, both read from the BASE commit, never from the head. Prints JSON.
            Exit 0 when the verdict is clean, 1 on an unaccounted trigger hit or any error of judgement
            (invalid classification, missing triggers file, change folder and branch disagreeing),
            2 when it cannot judge (unknown commit, git failure). The deploy guard runs it with the
            merge commit's first parent as `--base` and the merged pull request's head as `--head`.
  check     (CI) Judge open pull requests and post the `merge-conditions` commit status on their head
            commit: aggregate CI gate, `review-harness` / `opsx-verify` statuses and the matcher's
            result. `--pr N --head-sha S` judges S and posts only while S is still the head of #N;
            `--sha S` judges the open pull requests whose head is S; `--all-open` re-judges every open
            pull request into the default branch (after a push to it), posting `pending` first.
  validate  Check `triggers.yaml` / `classification.yaml` files against their schema.

The status description is `gates: <gates>[ - <reasons>]; base <sha7>` — `base` is the default-branch
commit the verdict was computed against, always last, so the merge rule can compare it with the
current head of the default branch. `error` and the `pending` posted while re-judging carry no gates.

Never executes code from the pull request head: the head commit is only read as data, through git.
Requirements: Python 3.9+, git, PyYAML; `check` also needs the `gh` CLI with a token.
Schemas: docs/OPENSPEC_GUIDE.md ("Classification and triggers"). Copied verbatim by sdd-init from the
sdd-core plugin (templates/sdd/bin/); a local edit is overwritten by `sdd-init --refresh`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, reported plainly
    sys.stderr.write("merge_conditions.py needs PyYAML: pip install pyyaml\n")
    raise

GATES = ("intent", "irreversible")
TRIGGERS_PATH = ".sdd/triggers.yaml"
CHANGES_DIR = "openspec/changes/"
ARCHIVE_DIR = "openspec/changes/archive/"
WORKFLOWS_DIR = ".github/workflows/"
CLASSIFICATION_FILE = "classification.yaml"
# Gate machinery that is always protected, even when triggers.yaml omits it: everything that changes
# what CI or this check does.
DEFAULT_MACHINERY = (
    ".github/**",
    ".sdd/**",
    ".claude/hooks/**",
    ".claude/settings.json",
    "**/.gitattributes",
    ".gitmodules",
    "openspec/config.yaml",
    "vercel.json",
)
# Trigger name reported when a pull request other than a framing one adds, changes or deletes a
# classification (an identical move into the change's archive folder excepted).
CLASSIFICATION_TRIGGER = "openspec/changes/**/classification.yaml"
# An archived change folder: `openspec/changes/archive/YYYY-MM-DD-<change>/` (or `<change>/`).
ARCHIVE_FOLDER = re.compile(r"^\d{4}-\d{2}-\d{2}-(.+)$")
# Branch suffixes of the framing and archive pull requests: `<type>/<id>-framing[-<n>]`, `<type>/<id>-archive`.
BRANCH_SUFFIX = re.compile(r"-(?:framing(?:-\d+)?|archive)$")
# Besides the moved change folder, what an archive pull request may touch.
ARCHIVE_ALLOWED = ("openspec/specs/**", "docs/**", "ROADMAP.md", "BACKLOG.md")
# Labels that replace the gates in the description.
LABEL_ONLY = ("framing", "unclassified", "invalid")
REVIEW_STATUSES = ("review-harness", "opsx-verify")
STATUS_CONTEXT = "merge-conditions"
SELF_WORKFLOW = "merge-conditions.yml"
DESCRIPTION_MAX = 140
PR_RUN_TYPES = {"opened", "synchronize", "reopened"}
PAGE_SIZE = 100
MAX_PAGES = 50


# --------------------------------------------------------------------------------------------
# Globs — GitHub Actions path-filter syntax: `*` stops at `/`, `**` crosses it, `?` = zero or one
# of the preceding character, `+` = one or more of it, `[...]` = a character class, a leading `!`
# negates (in ordered filter lists only). The whole path must match.
# --------------------------------------------------------------------------------------------

_GLOB_CACHE: dict = {}


def glob_regex(pattern: str):
    cached = _GLOB_CACHE.get(pattern)
    if cached is not None:
        return cached
    atoms = []  # [regex, quantifiable]
    i, n = 0, len(pattern)
    while i < n:
        if pattern.startswith("**/", i):
            atoms.append(["(?:.*/)?", False])
            i += 3
        elif pattern.startswith("**", i):
            atoms.append([".*", False])
            i += 2
        elif pattern[i] == "*":
            atoms.append(["[^/]*", False])
            i += 1
        elif pattern[i] in "?+" and atoms and atoms[-1][1]:
            atoms[-1][0] += pattern[i]
            atoms[-1][1] = False
            i += 1
        elif pattern[i] == "[" and pattern.find("]", i + 2) != -1:
            end = pattern.find("]", i + 2)
            body = pattern[i + 1:end].replace("\\", "\\\\")
            if body.startswith("!"):
                body = "^" + body[1:]
            atoms.append(["[" + body + "]", True])
            i = end + 1
        else:
            atoms.append([re.escape(pattern[i]), True])
            i += 1
    compiled = re.compile("".join(atom[0] for atom in atoms))
    _GLOB_CACHE[pattern] = compiled
    return compiled


def glob_match(pattern: str, path: str) -> bool:
    return glob_regex(pattern).fullmatch(path) is not None


def filter_includes(patterns, path: str) -> bool:
    """GitHub's ordered filter: the last pattern that matches decides; `!pattern` excludes."""
    included = False
    for pattern in patterns:
        if pattern.startswith("!"):
            if glob_match(pattern[1:], path):
                included = False
        elif glob_match(pattern, path):
            included = True
    return included


# --------------------------------------------------------------------------------------------
# git — read-only helpers. Every call reads objects; none runs anything from the repository.
# --------------------------------------------------------------------------------------------


class GitError(Exception):
    pass


# Settings of the caller's git configuration that would change what is parsed are neutralised;
# pathspecs are literal (a file name is never read as a pattern).
GIT_OPTIONS = ("-c", "diff.noprefix=false", "-c", "diff.mnemonicPrefix=false", "-c", "core.quotePath=false",
               "--literal-pathspecs")


def git(repo: str, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *GIT_OPTIONS, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout.decode("utf-8", "replace")


def rev_parse(repo: str, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", check=False).strip()


def show_file(repo: str, ref: str, path: str):
    """Content of `path` at `ref`, or None when absent."""
    result = subprocess.run(
        ["git", "-C", repo, *GIT_OPTIONS, "cat-file", "blob", f"{ref}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace")


def ls_tree(repo: str, ref: str, prefix: str) -> dict:
    """{path: blob sha} of every file under `prefix` at `ref`."""
    output = git(repo, "ls-tree", "-r", "-z", "--full-tree", ref, "--", prefix)
    files = {}
    for record in output.split("\0"):
        if not record:
            continue
        meta, path = record.split("\t", 1)
        mode, kind, sha = meta.split()
        if kind == "blob":
            files[path] = sha
    return files


class Entry:
    __slots__ = ("status", "path", "old_blob", "new_blob")

    def __init__(self, status, path, old_blob, new_blob):
        self.status, self.path, self.old_blob, self.new_blob = status, path, old_blob, new_blob


def diff_entries(repo: str, base: str, head: str) -> list:
    """Files touched between `base` and `head`; renames are listed as a deletion plus an addition."""
    output = git(repo, "diff", "--raw", "-z", "--no-renames", "--no-abbrev", "--no-ext-diff", base, head)
    tokens = output.split("\0")
    entries = []
    i = 0
    while i + 1 < len(tokens):
        meta = tokens[i]
        if not meta.startswith(":"):
            i += 1
            continue
        _, _, old_blob, new_blob, status = meta[1:].split()
        entries.append(Entry(status[0], tokens[i + 1], old_blob, new_blob))
        i += 2
    return entries


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def added_lines(repo: str, base: str, head: str, path: str) -> list:
    """[(line number in head, text)] of the lines ADDED to `path` between `base` and `head`.

    One file per call, named by the `-z` list of `diff_entries`, so no header is ever parsed for a
    path. `--text` reads every file as text, whatever `.gitattributes` says (`-diff`, `binary`).
    """
    output = git(
        repo, "diff", "-U0", "--text", "--no-color", "--no-ext-diff", "--no-textconv", "--no-renames",
        "--src-prefix=a/", "--dst-prefix=b/", base, head, "--", path,
    )
    lines = []
    in_hunk = False
    line_number = 0
    for line in output.split("\n"):
        if line.startswith("@@"):
            found = _HUNK.match(line)
            in_hunk = found is not None
            line_number = int(found.group(1)) if found else 0
            continue
        if in_hunk and line.startswith("+"):
            lines.append((line_number, line[1:]))
            line_number += 1
    return lines


# --------------------------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------------------------


def _string_list(value, where: str, errors: list) -> list:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        errors.append(f"{where}: expected a list of non-empty strings")
        return []
    return list(value)


def load_triggers(text):
    """Parse triggers.yaml. Returns (triggers, errors); the gate machinery always holds the defaults."""
    errors: list = []
    triggers = {gate: {"paths": [], "content": []} for gate in GATES}
    machinery = list(DEFAULT_MACHINERY)
    triggers["gate_machinery"] = machinery
    if text is None:
        return triggers, errors
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return triggers, [f"triggers.yaml: not valid YAML ({str(exc).splitlines()[0]})"]
    if data is None:
        return triggers, errors
    if not isinstance(data, dict):
        return triggers, ["triggers.yaml: expected a mapping at the top level"]
    for key in sorted(set(data) - {"intent", "irreversible", "gate_machinery"}, key=str):
        errors.append(f"triggers.yaml: unknown key {key!r}")
    for gate in GATES:
        section = data.get(gate)
        if section is None:
            continue
        if not isinstance(section, dict):
            errors.append(f"triggers.yaml: {gate}: expected a mapping with paths and content")
            continue
        for key in sorted(set(section) - {"paths", "content"}, key=str):
            errors.append(f"triggers.yaml: {gate}: unknown key {key!r}")
        triggers[gate]["paths"] = _string_list(section.get("paths"), f"triggers.yaml: {gate}.paths", errors)
        content = section.get("content")
        if content is None:
            continue
        if not isinstance(content, list):
            errors.append(f"triggers.yaml: {gate}.content: expected a list")
            continue
        for index, item in enumerate(content):
            where = f"triggers.yaml: {gate}.content[{index}]"
            if not isinstance(item, dict) or not isinstance(item.get("pattern"), str) or not item["pattern"]:
                errors.append(f"{where}: expected a mapping with a non-empty pattern")
                continue
            for key in sorted(set(item) - {"paths", "pattern"}, key=str):
                errors.append(f"{where}: unknown key {key!r}")
            try:
                regex = re.compile(item["pattern"])
            except re.error as exc:
                errors.append(f"{where}.pattern: invalid regex ({exc})")
                continue
            triggers[gate]["content"].append({
                "paths": _string_list(item.get("paths"), f"{where}.paths", errors),
                "pattern": item["pattern"],
                "regex": regex,
            })
    section = data.get("gate_machinery")
    if section is not None:
        if not isinstance(section, dict):
            errors.append("triggers.yaml: gate_machinery: expected a mapping with paths")
        else:
            for key in sorted(set(section) - {"paths"}, key=str):
                errors.append(f"triggers.yaml: gate_machinery: unknown key {key!r}")
            for glob in _string_list(section.get("paths"), "triggers.yaml: gate_machinery.paths", errors):
                if glob not in machinery:
                    machinery.append(glob)
    return triggers, errors


def load_classification(text, change=None):
    """Parse classification.yaml. Returns (classification or None, errors)."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, [f"classification.yaml: not valid YAML ({str(exc).splitlines()[0]})"]
    if not isinstance(data, dict):
        return None, ["classification.yaml: expected a mapping at the top level"]
    errors: list = []
    for key in sorted(set(data) - {"change", "intent", "irreversible", "revert_of"}, key=str):
        errors.append(f"classification.yaml: unknown key {key!r}")
    if not isinstance(data.get("change"), str) or not data.get("change"):
        errors.append("classification.yaml: change: expected the change id")
    elif change is not None and data["change"] != change:
        errors.append(f"classification.yaml: change is {data['change']!r}, the folder is {change!r}")
    if "revert_of" in data and (not isinstance(data["revert_of"], str) or not data["revert_of"]):
        errors.append("classification.yaml: revert_of: expected a change id")
    classification = {"change": data.get("change"), "revert_of": data.get("revert_of")}
    for gate in GATES:
        section = data.get(gate)
        where = f"classification.yaml: {gate}"
        if not isinstance(section, dict):
            errors.append(f"{where}: expected a mapping with open and evidence")
            continue
        for key in sorted(set(section) - {"open", "evidence", "waived"}, key=str):
            errors.append(f"{where}: unknown key {key!r}")
        if not isinstance(section.get("open"), bool):
            errors.append(f"{where}.open: expected true or false")
        if not isinstance(section.get("evidence"), str) or not section.get("evidence", "").strip():
            errors.append(f"{where}.evidence: expected the reason for the answer")
        waived = []
        raw_waived = section.get("waived")
        if raw_waived is not None and not isinstance(raw_waived, list):
            errors.append(f"{where}.waived: expected a list")
            raw_waived = []
        for index, item in enumerate(raw_waived or []):
            if (not isinstance(item, dict) or not isinstance(item.get("trigger"), str) or not item["trigger"]
                    or not isinstance(item.get("reason"), str) or not item["reason"].strip()):
                errors.append(f"{where}.waived[{index}]: expected a trigger and a reason")
                continue
            for key in sorted(set(item) - {"trigger", "reason"}, key=str):
                errors.append(f"{where}.waived[{index}]: unknown key {key!r}")
            waived.append({"trigger": item["trigger"], "reason": item["reason"]})
        classification[gate] = {"open": section.get("open") is True, "waived": waived}
    if errors:
        return None, errors
    return classification, errors


# --------------------------------------------------------------------------------------------
# Matcher
# --------------------------------------------------------------------------------------------


def _change_folder(path: str):
    """`<id>` when `path` is inside `openspec/changes/<id>/` (archive excluded)."""
    if not path.startswith(CHANGES_DIR):
        return None
    parts = path[len(CHANGES_DIR):].split("/")
    if len(parts) < 2 or parts[0] == "archive":
        return None
    return parts[0]


def _archive_folder(path: str) -> str:
    return path[len(ARCHIVE_DIR):].split("/", 1)[0]


def _archive_folder_of(path: str, change: str) -> bool:
    """Whether `path` is inside `change`'s archive folder: `YYYY-MM-DD-<change>/` or `<change>/`."""
    folder = _archive_folder(path)
    dated = ARCHIVE_FOLDER.match(folder)
    return folder == change or (dated is not None and dated.group(1) == change)


def _branch_candidates(branch):
    """Change ids a branch `<type>/<id>[-framing[-<n>]|-archive]` may belong to."""
    if not branch:
        return []
    name = branch.split("/", 1)[1] if "/" in branch else branch
    stripped = BRANCH_SUFFIX.sub("", name)
    return [name, stripped] if stripped and stripped != name else [name]


def find_change(files, branch):
    """(change, error) of a pull request: the one change folder it touches, named by its branch too.

    A branch name alone never selects a classification: a pull request that touches no change folder
    is unclassified. Several folders, or a folder the branch does not name, is an error.
    """
    folders = sorted({folder for folder in (_change_folder(path) for path in files) if folder})
    if not folders:
        return None, None
    if len(folders) > 1:
        return None, f"several change folders touched ({', '.join(folders)})"
    if folders[0] not in _branch_candidates(branch):
        return None, f"change folder {folders[0]} does not match the branch {branch or '(none)'}"
    return folders[0], None


def is_framing(change: str, entries) -> bool:
    prefix = f"{CHANGES_DIR}{change}/"
    paths = {entry.path for entry in entries}
    return (
        bool(entries)
        and all(entry.path.startswith(prefix) and entry.status in "AM" for entry in entries)
        and f"{prefix}{CLASSIFICATION_FILE}" in paths
    )


def is_archive(change: str, entries) -> bool:
    """Moves `openspec/changes/<change>/` into ONE archive folder of that change, nothing else but
    `ARCHIVE_ALLOWED`."""
    prefix = f"{CHANGES_DIR}{change}/"
    moved_out = False
    folders = set()
    for entry in entries:
        if entry.path.startswith(prefix):
            if entry.status != "D":
                return False
            moved_out = True
        elif entry.path.startswith(ARCHIVE_DIR):
            if entry.status == "D" or not _archive_folder_of(entry.path, change):
                return False
            folders.add(_archive_folder(entry.path))
        elif not any(glob_match(glob, entry.path) for glob in ARCHIVE_ALLOWED):
            return False
    return moved_out and len(folders) == 1


def classification_edits(repo: str, base: str, entries) -> list:
    """Classifications the pull request adds, changes or deletes, whether or not on the base ref.

    Judged by what the merge would do to the base ref: a file whose head content equals the base
    content is no edit (a branch that already carries the approved version), nor is a deletion absent
    from the base ref. An approved classification moved identically into its change's archive folder
    (archive pull request) is no edit either — both sides of the move.
    """
    on_base = {path: blob for path, blob in ls_tree(repo, base, CHANGES_DIR).items()
               if path.endswith("/" + CLASSIFICATION_FILE)}
    touched = [entry for entry in entries if glob_match(CLASSIFICATION_TRIGGER, entry.path)]
    added = {entry.path: entry.new_blob for entry in touched if entry.status != "D"}
    moved = set()
    for entry in touched:
        change = _change_folder(entry.path)
        blob = on_base.get(entry.path)
        if entry.status != "D" or change is None or blob is None:
            continue
        for path, new_blob in added.items():
            if (new_blob == blob and path.startswith(ARCHIVE_DIR) and _archive_folder_of(path, change)
                    and path == f"{ARCHIVE_DIR}{_archive_folder(path)}/{CLASSIFICATION_FILE}"):
                moved.update((entry.path, path))
                break
    edits = []
    for entry in touched:
        head_blob = None if entry.status == "D" else entry.new_blob
        if entry.path in moved or on_base.get(entry.path) == head_blob:
            continue
        edits.append(entry.path)
    return sorted(edits)


def needs_lines(triggers, path: str) -> bool:
    """Whether a content trigger reads `path`."""
    return any(not content["paths"] or any(glob_match(glob, path) for glob in content["paths"])
               for gate in GATES for content in triggers[gate]["content"])


def compute_hits(triggers, files, lines_by_file, edits) -> list:
    hits = []
    for gate in GATES:
        for glob in triggers[gate]["paths"]:
            for path in files:
                if glob_match(glob, path):
                    hits.append({"gate": gate, "trigger": glob, "file": path})
        for content in triggers[gate]["content"]:
            for path in sorted(lines_by_file):
                if content["paths"] and not any(glob_match(glob, path) for glob in content["paths"]):
                    continue
                for number, text in lines_by_file[path]:
                    if content["regex"].search(text):
                        hits.append({"gate": gate, "trigger": content["pattern"], "file": path, "line": number})
                        break
    for glob in triggers["gate_machinery"]:
        for path in files:
            if glob_match(glob, path):
                hits.append({"gate": "irreversible", "trigger": glob, "file": path, "machinery": True})
    for path in edits:
        hits.append({"gate": "irreversible", "trigger": CLASSIFICATION_TRIGGER, "file": path, "machinery": True})
    return hits


def resolve_gates(kind: str, classification, hits):
    """(gates, unaccounted, waived) of a classified pull request."""
    declared = {gate for gate in GATES if classification[gate]["open"]}
    gates = set(declared) if kind == "change" else set()
    unaccounted, waived = [], []
    for hit in hits:
        gate = hit["gate"]
        if not hit.get("machinery"):
            reason = next((item["reason"] for item in classification[gate]["waived"]
                           if item["trigger"] == hit["trigger"]), None)
            if reason is not None:
                waived.append(dict(hit, reason=reason))
                continue
        gates.add(gate)
        if gate not in declared:
            unaccounted.append(hit)
    return [gate for gate in GATES if gate in gates], unaccounted, waived


def gates_label(gates) -> str:
    if len(gates) == 1 and gates[0] in LABEL_ONLY:
        return f"gates: {gates[0]}"
    return "gates: " + ("+".join(gates) if gates else "none")


def unaccounted_reason(unaccounted) -> str:
    seen = []
    for hit in unaccounted:
        item = f"{hit['gate']} {hit['file']}" + (f":{hit['line']}" if "line" in hit else "")
        if item not in seen:
            seen.append(item)
    return "unaccounted " + ", ".join(seen)


def match(repo: str, base: str, head: str, branch=None) -> dict:
    base_sha = rev_parse(repo, base)
    head_sha = rev_parse(repo, head)
    if not base_sha or not head_sha:
        raise GitError(f"unknown commit: {base if not base_sha else head}")
    merge_base = git(repo, "merge-base", base_sha, head_sha).strip()
    triggers_text = show_file(repo, base_sha, TRIGGERS_PATH)
    triggers, errors = load_triggers(triggers_text)
    if triggers_text is None:
        errors.append(f"{TRIGGERS_PATH} missing on the base ref")
    entries = diff_entries(repo, merge_base, head_sha)
    files = sorted({entry.path for entry in entries})
    change, change_error = find_change(files, branch)
    if change_error:
        errors.append(change_error)
    framing = change is not None and is_framing(change, entries)
    edits = [] if framing else classification_edits(repo, base_sha, entries)
    lines_by_file = {entry.path: added_lines(repo, merge_base, head_sha, entry.path) for entry in entries
                     if entry.status != "D" and needs_lines(triggers, entry.path)}
    hits = compute_hits(triggers, files, lines_by_file, edits)

    classification = None
    if change:
        text = show_file(repo, base_sha, f"{CHANGES_DIR}{change}/{CLASSIFICATION_FILE}")
        if text is not None:
            classification, classification_errors = load_classification(text, change)
            errors.extend(f"approved {message}" for message in classification_errors)
            if classification is None:
                classification = False  # present on the base ref but invalid

    gates, unaccounted, waived = [], [], []
    if framing:
        kind = "framing"
        proposed = show_file(repo, head_sha, f"{CHANGES_DIR}{change}/{CLASSIFICATION_FILE}")
        _, proposed_errors = load_classification(proposed or "", change)
        errors = [message for message in errors if not message.startswith("approved ")]
        errors.extend(f"proposed {message}" for message in proposed_errors)
        gates = ["framing"]
    elif classification is False:
        kind = "change"
        gates = ["invalid"]
    elif classification:
        kind = "archive" if is_archive(change, entries) else "change"
        gates, unaccounted, waived = resolve_gates(kind, classification, hits)
    else:
        kind = "unclassified"
        gates = ["unclassified"]

    label = gates_label(gates)
    reasons = list(errors)
    if unaccounted:
        reasons.append(unaccounted_reason(unaccounted))
    return {
        "kind": kind,
        "change": change,
        "base": base_sha,
        "head": head_sha,
        "merge_base": merge_base,
        "gates": gates,
        "hits": hits,
        "unaccounted": unaccounted,
        "waived": waived,
        "errors": errors,
        "files": files,
        "label": label,
        "description": label + (" - " + "; ".join(reasons) if reasons else ""),
    }


# --------------------------------------------------------------------------------------------
# Check — aggregate CI gate, review statuses, commit status
# --------------------------------------------------------------------------------------------


def _as_list(value):
    if value is None:
        return None
    return [value] if isinstance(value, str) else [str(item) for item in value]


def workflow_events(document) -> dict:
    if not isinstance(document, dict):
        return {}
    events = document.get("on", document.get(True))  # PyYAML reads a bare `on` key as True
    if isinstance(events, str):
        return {events: None}
    if isinstance(events, list):
        return {event: None for event in events if isinstance(event, str)}
    return events if isinstance(events, dict) else {}


def workflow_required(document, files, base_branch: str) -> bool:
    """Whether a workflow runs on a pull request into `base_branch` touching `files`."""
    events = workflow_events(document)
    if "pull_request" not in events:
        return False
    config = events["pull_request"] if isinstance(events["pull_request"], dict) else {}
    types = _as_list(config.get("types"))
    if types is not None and not PR_RUN_TYPES & set(types):
        return False
    branches = _as_list(config.get("branches"))
    if branches is not None and not filter_includes(branches, base_branch):
        return False
    ignored_branches = _as_list(config.get("branches-ignore"))
    if ignored_branches is not None and filter_includes(ignored_branches, base_branch):
        return False
    paths = _as_list(config.get("paths"))
    if paths is not None:
        return any(filter_includes(paths, path) for path in files)
    ignored = _as_list(config.get("paths-ignore"))
    if ignored is not None:
        return any(not filter_includes(ignored, path) for path in files)
    return True


def is_workflow(path: str) -> bool:
    """GitHub runs the YAML files directly in `.github/workflows/`, not those of its subfolders."""
    return (path.startswith(WORKFLOWS_DIR) and path.count("/") == 2
            and path.endswith((".yml", ".yaml")))


def _load_workflow(repo: str, ref: str, path: str):
    """The workflow document, or None when it is not valid YAML."""
    try:
        return yaml.safe_load(show_file(repo, ref, path) or "")
    except yaml.YAMLError:
        return None


def required_workflows(repo: str, base: str, files, base_branch: str) -> list:
    """Workflows of the base ref that a pull request with these files must have run, by path."""
    required = []
    for path in sorted(ls_tree(repo, base, WORKFLOWS_DIR)):
        if not is_workflow(path) or path.rsplit("/", 1)[1] == SELF_WORKFLOW:
            continue
        document = _load_workflow(repo, base, path)
        if document is None or workflow_required(document, files, base_branch):
            required.append(path)  # unreadable: GitHub cannot run it either, so it never goes green
    return required


def _workflow_name(path: str) -> str:
    return path.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def workflow_problems(repo: str, result: dict, required, base_branch: str) -> dict:
    """{workflow path: reason} of the pull request's own workflow edits that its runs cannot reflect.

    A required workflow the pull request deletes (a rename is a deletion plus an addition) or edits so
    that it no longer runs on it would wait forever for a run; a workflow it adds runs although nothing
    requires it, and can post any status. Each is a reason of its own (such pull requests are gate
    machinery: the owner merges them).
    """
    on_base = {path for path in ls_tree(repo, result["base"], WORKFLOWS_DIR) if is_workflow(path)}
    problems = {}
    for entry in diff_entries(repo, result["merge_base"], result["head"]):
        path = entry.path
        if not is_workflow(path):
            continue
        name = _workflow_name(path)
        if path in required:
            if entry.status == "D":
                problems[path] = f"{name} deleted by the pull request"
            elif not workflow_required(_load_workflow(repo, result["head"], path), result["files"], base_branch):
                problems[path] = f"{name} no longer runs on the pull request"
        elif entry.status != "D" and path not in on_base:
            problems[path] = f"{name} added by the pull request"
    return problems


def truncate(text: str, limit: int = DESCRIPTION_MAX) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def describe(label: str, reasons, base_sha: str) -> str:
    """`<label>; base <sha7>`, or `<label> - <reasons>; base <sha7>`, cut inside the reasons so that the
    base always survives."""
    suffix = f"base {base_sha[:7]}"
    reasons = list(reasons)
    if not reasons:
        return f"{label}; {suffix}"
    text = label + " - " + "".join(f"{reason}; " for reason in reasons)
    if len(text) + len(suffix) > DESCRIPTION_MAX:
        text = text[: DESCRIPTION_MAX - len(suffix) - 5] + "...; "
    return text + suffix


def evaluate(result: dict, required, runs, statuses, problems=None):
    """(state, description) of `merge-conditions` for one head commit."""
    problems = problems or {}
    failures, waiting = list(result["errors"]), []
    if result["unaccounted"]:
        failures.append(unaccounted_reason(result["unaccounted"]))
    latest = {}
    for run in runs:
        if run.get("event") != "pull_request" or run.get("head_sha") != result["head"]:
            continue
        path = run.get("path", "").split("@", 1)[0]
        if path not in latest or run.get("id", 0) > latest[path].get("id", 0):
            latest[path] = run
    for path in required:
        if path in problems:
            continue
        name = _workflow_name(path)
        run = latest.get(path)
        if run is None:
            waiting.append(f"no run of {name}")
        elif run.get("status") != "completed":
            waiting.append(f"{name} running")
        elif run.get("conclusion") != "success":
            failures.append(f"{name} {run.get('conclusion')}")
    failures.extend(problems[path] for path in sorted(problems))
    if result["kind"] == "change":
        for context in REVIEW_STATUSES:
            state = statuses.get(context)
            if state is None:
                waiting.append(f"no {context} status")
            elif state == "pending":
                waiting.append(f"{context} pending")
            elif state != "success":
                failures.append(f"{context} {state}")
    if failures:
        state, reasons = "failure", failures + waiting
    elif waiting:
        state, reasons = "pending", waiting
    else:
        state, reasons = "success", []
    return state, describe(result["label"], reasons, result["base"])


class GitHub:
    """`gh api` client; tests replace it with a stub exposing the same two methods."""

    def get(self, path: str):
        result = subprocess.run(["gh", "api", path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise RuntimeError(f"gh api {path}: {result.stderr.decode('utf-8', 'replace').strip()}")
        return json.loads(result.stdout or b"null")

    def post_status(self, repo: str, sha: str, state: str, description: str, target_url=None):
        command = ["gh", "api", "--method", "POST", f"repos/{repo}/statuses/{sha}",
                   "-f", f"state={state}", "-f", f"context={STATUS_CONTEXT}", "-f", f"description={description}"]
        if target_url:
            command += ["-f", f"target_url={target_url}"]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL)


def get_pages(api, path: str, key=None) -> list:
    """Every item of a paginated list; `key` names the array when the response is an object."""
    items = []
    separator = "&" if "?" in path else "?"
    for page in range(1, MAX_PAGES + 1):
        data = api.get(f"{path}{separator}per_page={PAGE_SIZE}&page={page}")
        batch = (data or {}).get(key) or [] if key else data or []
        items.extend(batch)
        if len(batch) < PAGE_SIZE:
            return items
    raise RuntimeError(f"{path}: more than {MAX_PAGES} pages")


def fetch_default_branch(repo: str, default_branch: str):
    git(repo, "fetch", "--no-tags", "--quiet", "origin",
        f"+refs/heads/{default_branch}:refs/remotes/origin/{default_branch}")


def fetch_pull_request(repo: str, default_branch: str, number: int, head_sha: str):
    """Fetch the base branch and the pull request head as data (no checkout, nothing executed)."""
    git(repo, "fetch", "--no-tags", "--quiet", "origin",
        f"+refs/heads/{default_branch}:refs/remotes/origin/{default_branch}",
        f"+refs/pull/{number}/head:refs/remotes/origin/pull/{number}")
    if not git(repo, "cat-file", "-t", head_sha, check=False).strip() == "commit":
        git(repo, "fetch", "--no-tags", "--quiet", "origin", head_sha)


def _judgeable(pull, default_branch: str, log) -> bool:
    if pull.get("state") != "open":
        log(f"#{pull['number']}: not open, skipped")
        return False
    if pull["base"]["ref"] != default_branch:
        log(f"#{pull['number']}: targets {pull['base']['ref']}, not {default_branch}; skipped")
        return False
    return True


def _still_head(api, slug: str, number: int, head_sha: str, default_branch: str) -> bool:
    """Whether `head_sha` is still the head of the open pull request #number into the default branch."""
    pull = api.get(f"repos/{slug}/pulls/{number}") or {}
    return (pull.get("state") == "open" and pull.get("head", {}).get("sha") == head_sha
            and pull.get("base", {}).get("ref") == default_branch)


def check(api, repo: str, slug: str, default_branch: str, pr=None, sha=None, all_open: bool = False,
          base_ref=None, fetch: bool = True, post: bool = True, target_url=None, log=None) -> list:
    """Judge open pull requests and post their status.

    `pr` (with `sha`, the head the event named): that pull request, skipped when its head moved;
    `sha` alone: the open pull requests whose head is `sha`; `all_open`: every open pull request into
    the default branch, each first set to `pending`. A status is posted only if the judged commit is
    still the pull request's head at that moment.
    """
    log = log or (lambda message: print(message, file=sys.stderr))
    base_ref = base_ref or f"origin/{default_branch}"
    if all_open:
        if fetch:
            fetch_default_branch(repo, default_branch)
        pulls = [pull for pull in get_pages(api, f"repos/{slug}/pulls?state=open&base={default_branch}")
                 if _judgeable(pull, default_branch, log)]
        moved_to = rev_parse(repo, base_ref)[:7]
        for pull in pulls:
            if post:
                api.post_status(slug, pull["head"]["sha"], "pending",
                                f"re-judging: {default_branch} moved to {moved_to}", target_url)
    elif pr is not None:
        pull = api.get(f"repos/{slug}/pulls/{pr}")
        if sha is not None and pull["head"]["sha"] != sha:
            log(f"#{pr}: head moved from {sha[:12]} to {pull['head']['sha'][:12]}; a newer run judges it")
            return []
        pulls = [pull] if _judgeable(pull, default_branch, log) else []
    else:
        pulls = [pull for pull in get_pages(api, f"repos/{slug}/commits/{sha}/pulls")
                 if pull.get("head", {}).get("sha") == sha and _judgeable(pull, default_branch, log)]
    outcomes = []
    for pull in pulls:
        number, head_sha = pull["number"], pull["head"]["sha"]
        result = None
        required = []
        try:
            if fetch:
                fetch_pull_request(repo, default_branch, number, head_sha)
            result = match(repo, base_ref, head_sha, pull["head"].get("ref"))
            required = required_workflows(repo, result["base"], result["files"], default_branch)
            problems = workflow_problems(repo, result, required, default_branch)
            runs = get_pages(api, f"repos/{slug}/actions/runs?head_sha={head_sha}&event=pull_request",
                             "workflow_runs")
            statuses = {item["context"]: item["state"]
                        for item in get_pages(api, f"repos/{slug}/commits/{head_sha}/status", "statuses")}
            state, description = evaluate(result, required, runs, statuses, problems)
        except Exception as exc:  # fail closed, with the reason where the owner looks
            state, description = "error", truncate(f"merge-conditions could not judge: {exc}")
        log(f"#{number} {head_sha[:12]}: {state} - {description}")
        if result is not None:
            log(json.dumps({key: result[key] for key in ("kind", "change", "gates", "hits", "unaccounted",
                                                          "waived", "errors")}, indent=2))
            log("required workflows: " + (", ".join(required) or "none"))
        posted = False
        if post:
            if _still_head(api, slug, number, head_sha, default_branch):
                api.post_status(slug, head_sha, state, description, target_url)
                posted = True
            else:
                log(f"#{number}: {head_sha[:12]} is no longer its head; not posted")
        outcomes.append({"number": number, "sha": head_sha, "state": state, "description": description,
                         "posted": posted})
    return outcomes


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


def validate_files(paths) -> list:
    errors = []
    for path in paths:
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            errors.append(f"{path}: {exc}")
            continue
        if name == "triggers.yaml":
            _, found = load_triggers(text)
        elif name == CLASSIFICATION_FILE:
            folder = os.path.basename(os.path.dirname(os.path.abspath(path)))
            _, found = load_classification(text, folder)
        else:
            found = ["not a triggers.yaml or classification.yaml file"]
        errors.extend(f"{path}: {message}" for message in found)
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("-C", dest="directory", default=".", help="repository directory (default: .)")
    commands = parser.add_subparsers(dest="command", required=True)

    match_parser = commands.add_parser("match", help="classify a diff; prints JSON; exit 1 when not clean")
    match_parser.add_argument("--base", required=True,
                              help="base commit, e.g. origin/main; in the deploy guard, the default branch before the merge (the push event's `before`), never <merge>^1, which a rebase merge makes wrong")
    match_parser.add_argument("--head", required=True, help="head commit or ref")
    match_parser.add_argument("--branch", required=True, help="pull request branch name, e.g. feat/<change-id>")

    check_parser = commands.add_parser("check", help="judge pull requests and post the merge-conditions status")
    check_parser.add_argument("--repo", required=True, help="owner/name")
    check_parser.add_argument("--default-branch", required=True)
    target = check_parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--pr", type=int)
    target.add_argument("--sha")
    target.add_argument("--all-open", action="store_true",
                        help="re-judge every open pull request into the default branch")
    check_parser.add_argument("--head-sha", help="with --pr: the head commit the event named")
    check_parser.add_argument("--dry-run", action="store_true", help="print, do not post the status")

    validate_parser = commands.add_parser("validate", help="check triggers.yaml / classification.yaml files")
    validate_parser.add_argument("files", nargs="+")

    args = parser.parse_args(argv)
    if args.command == "match":
        try:
            result = match(args.directory, args.base, args.head, args.branch)
        except GitError as exc:
            print(f"merge_conditions.py: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(result, indent=2))
        return 1 if result["errors"] or result["unaccounted"] else 0
    if args.command == "validate":
        errors = validate_files(args.files)
        for message in errors:
            print(message, file=sys.stderr)
        return 1 if errors else 0
    if args.head_sha and args.pr is None:
        parser.error("--head-sha goes with --pr")
    server = os.environ.get("GITHUB_SERVER_URL")
    run_id = os.environ.get("GITHUB_RUN_ID")
    target_url = f"{server}/{args.repo}/actions/runs/{run_id}" if server and run_id else None
    outcomes = check(GitHub(), args.directory, args.repo, args.default_branch, pr=args.pr,
                     sha=args.sha if args.pr is None else args.head_sha, all_open=args.all_open,
                     post=not args.dry_run, target_url=target_url)
    print(json.dumps(outcomes, indent=2))
    return 1 if any(outcome["state"] == "error" for outcome in outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
