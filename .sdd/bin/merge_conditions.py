#!/usr/bin/env python3
"""merge-conditions — trigger matcher and merge-conditions check of the spec-driven workflow.

Subcommands
  match     Classify a pull request's diff against `.sdd/triggers.yaml` and the approved
            `classification.yaml`, both read from the BASE ref, never from the head. Prints JSON.
  check     (CI) Judge the open pull request(s) of a head commit and post the `merge-conditions`
            commit status on it: aggregate CI gate, `review-harness` / `opsx-verify` statuses and
            the matcher's result.
  validate  Check `triggers.yaml` / `classification.yaml` files against their schema.

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
CLASSIFICATION_FILE = "classification.yaml"
# Gate machinery that is always protected, even when triggers.yaml omits it (or is missing).
DEFAULT_MACHINERY = (
    ".sdd/**",
    ".claude/hooks/**",
    ".claude/settings.json",
    ".github/workflows/**",
    "vercel.json",
)
# Trigger name reported when an approved classification of the base ref is edited.
CLASSIFICATION_TRIGGER = "openspec/changes/**/classification.yaml"
# Besides the moved change folder, what an archive pull request may touch.
ARCHIVE_ALLOWED = ("openspec/specs/**", "docs/**", "ROADMAP.md", "BACKLOG.md")
REVIEW_STATUSES = ("review-harness", "opsx-verify")
STATUS_CONTEXT = "merge-conditions"
SELF_WORKFLOW = "merge-conditions.yml"
DESCRIPTION_MAX = 140
PR_RUN_TYPES = {"opened", "synchronize", "reopened"}


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


def git(repo: str, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", repo, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout.decode("utf-8", "replace")


def rev_parse(repo: str, ref: str) -> str:
    return git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").strip()


def show_file(repo: str, ref: str, path: str):
    """Content of `path` at `ref`, or None when absent."""
    result = subprocess.run(
        ["git", "-C", repo, "show", f"{ref}:{path}"],
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


def added_lines(repo: str, base: str, head: str) -> dict:
    """{path: [(line number in head, text)]} of the lines ADDED between `base` and `head`."""
    output = git(
        repo, "-c", "core.quotePath=false", "diff", "-U0", "--no-color", "--no-ext-diff",
        "--no-textconv", "--no-renames", base, head,
    )
    lines_by_file: dict = {}
    path = None
    in_header = False
    line_number = 0
    for line in output.split("\n"):
        if line.startswith("diff --git "):
            in_header, path = True, None
            continue
        if in_header:
            if line.startswith("+++ "):
                target = line[4:]
                if target.startswith('"') and target.endswith('"'):
                    target = target[1:-1]
                path = target[2:] if target.startswith("b/") else None
                continue
            if not line.startswith("@@"):
                continue
            in_header = False
        if line.startswith("@@"):
            found = _HUNK.match(line)
            line_number = int(found.group(1)) if found else 0
            continue
        if path is None:
            continue
        if line.startswith("+"):
            lines_by_file.setdefault(path, []).append((line_number, line[1:]))
            line_number += 1
    return lines_by_file


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


def _archive_folder_of(path: str, change: str) -> bool:
    folder = path[len(ARCHIVE_DIR):].split("/", 1)[0]
    return folder == change or folder.endswith("-" + change)


def _branch_candidates(branch):
    if not branch or "/" not in branch:
        return []
    name = branch.split("/", 1)[1]
    candidates = [name]
    for suffix in ("-framing", "-archive"):
        if name.endswith(suffix):
            candidates.append(name[: -len(suffix)])
    return candidates


def find_change(repo: str, base: str, files, branch):
    """The change a pull request belongs to: the change folder it touches, else its branch name."""
    folders = {folder for folder in (_change_folder(path) for path in files) if folder}
    candidates = _branch_candidates(branch)
    if len(folders) == 1:
        return next(iter(folders)), None
    if folders:
        for candidate in candidates:
            if candidate in folders:
                return candidate, None
        return None, f"several change folders touched ({', '.join(sorted(folders))})"
    for candidate in candidates:
        if show_file(repo, base, f"{CHANGES_DIR}{candidate}/{CLASSIFICATION_FILE}") is not None:
            return candidate, None
        if ls_tree(repo, base, f"{CHANGES_DIR}{candidate}/"):
            return candidate, None
    return None, None


def is_framing(change: str, entries) -> bool:
    prefix = f"{CHANGES_DIR}{change}/"
    paths = {entry.path for entry in entries}
    return (
        bool(entries)
        and all(entry.path.startswith(prefix) and entry.status in "AM" for entry in entries)
        and f"{prefix}{CLASSIFICATION_FILE}" in paths
    )


def is_archive(change: str, entries) -> bool:
    prefix = f"{CHANGES_DIR}{change}/"
    moved_out = moved_in = False
    for entry in entries:
        if entry.path.startswith(prefix):
            if entry.status != "D":
                return False
            moved_out = True
        elif entry.path.startswith(ARCHIVE_DIR):
            if entry.status == "D" or not _archive_folder_of(entry.path, change):
                return False
            moved_in = True
        elif not any(glob_match(glob, entry.path) for glob in ARCHIVE_ALLOWED):
            return False
    return moved_out and moved_in


def classification_edits(repo: str, base: str, head: str, entries) -> list:
    """Approved classifications of the base ref that the pull request changes or deletes.

    A file the diff touches whose head content equals the base content is no edit (a branch that
    already carries the approved version); neither is a deletion that moves the identical file into
    the change's archive folder (archive pull request).
    """
    approved = {path: blob for path, blob in ls_tree(repo, base, CHANGES_DIR).items()
                if path.endswith("/" + CLASSIFICATION_FILE)}
    touched = {entry.path: entry for entry in entries}
    archived = None
    edits = []
    for path, blob in sorted(approved.items()):
        entry = touched.get(path)
        if entry is None:
            continue
        if entry.status != "D":
            if entry.new_blob != blob:
                edits.append(path)
            continue
        change = _change_folder(path)
        if change is not None:
            if archived is None:
                archived = ls_tree(repo, head, ARCHIVE_DIR)
            if any(candidate.endswith("/" + CLASSIFICATION_FILE) and archived[candidate] == blob
                   and _archive_folder_of(candidate, change) for candidate in archived):
                continue
        edits.append(path)
    return edits


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


def gates_label(kind: str, gates) -> str:
    if kind in ("framing", "unclassified"):
        return f"gates: {kind}"
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
        raise GitError(f"unknown ref: {base if not base_sha else head}")
    merge_base = git(repo, "merge-base", base_sha, head_sha).strip()
    triggers, errors = load_triggers(show_file(repo, base_sha, TRIGGERS_PATH))
    entries = diff_entries(repo, merge_base, head_sha)
    files = sorted({entry.path for entry in entries})
    change, change_error = find_change(repo, base_sha, files, branch)
    if change_error:
        errors.append(change_error)
    edits = classification_edits(repo, base_sha, head_sha, entries)
    hits = compute_hits(triggers, files, added_lines(repo, merge_base, head_sha), edits)

    classification = None
    if change:
        text = show_file(repo, base_sha, f"{CHANGES_DIR}{change}/{CLASSIFICATION_FILE}")
        if text is not None:
            classification, classification_errors = load_classification(text, change)
            errors.extend(f"approved {message}" for message in classification_errors)
            if classification is None:
                classification = False  # present on the base ref but invalid

    gates, unaccounted, waived = [], [], []
    if change and is_framing(change, entries):
        kind = "framing"
        proposed = show_file(repo, head_sha, f"{CHANGES_DIR}{change}/{CLASSIFICATION_FILE}")
        _, proposed_errors = load_classification(proposed or "", change)
        errors = [message for message in errors if not message.startswith("approved ")]
        errors.extend(f"proposed {message}" for message in proposed_errors)
        gates = ["framing"]
    elif classification is False:
        kind = "change"
    elif classification:
        kind = "archive" if is_archive(change, entries) else "change"
        gates, unaccounted, waived = resolve_gates(kind, classification, hits)
    else:
        kind = "unclassified"
        gates = ["unclassified"]

    label = gates_label(kind, gates)
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


def required_workflows(repo: str, base: str, files, base_branch: str) -> list:
    """Workflows of the base ref that a pull request with these files must have run, by path."""
    required = []
    for path in sorted(ls_tree(repo, base, ".github/workflows/")):
        if path.count("/") != 2 or not path.endswith((".yml", ".yaml")):
            continue
        if path.rsplit("/", 1)[1] == SELF_WORKFLOW:
            continue
        try:
            document = yaml.safe_load(show_file(repo, base, path) or "")
        except yaml.YAMLError:
            required.append(path)  # unreadable: GitHub cannot run it either, so it never goes green
            continue
        if workflow_required(document, files, base_branch):
            required.append(path)
    return required


def _workflow_name(path: str) -> str:
    return path.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def truncate(text: str, limit: int = DESCRIPTION_MAX) -> str:
    return text if len(text) <= limit else text[: limit - 3] + "..."


def evaluate(result: dict, required, runs, statuses):
    """(state, description) of `merge-conditions` for one head commit."""
    failures, waiting = list(result["errors"]), []
    if result["unaccounted"]:
        failures.append(unaccounted_reason(result["unaccounted"]))
    latest = {}
    for run in runs:
        if run.get("event") != "pull_request" or run.get("head_sha") not in (None, result["head"]):
            continue
        path = run.get("path", "").split("@", 1)[0]
        if path not in latest or run.get("id", 0) > latest[path].get("id", 0):
            latest[path] = run
    for path in required:
        name = _workflow_name(path)
        run = latest.get(path)
        if run is None:
            waiting.append(f"no run of {name}")
        elif run.get("status") != "completed":
            waiting.append(f"{name} running")
        elif run.get("conclusion") != "success":
            failures.append(f"{name} {run.get('conclusion')}")
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
    description = result["label"] + (" - " + "; ".join(reasons) if reasons else "")
    return state, truncate(description)


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


def fetch_pull_request(repo: str, default_branch: str, number: int, head_sha: str):
    """Fetch the base branch and the pull request head as data (no checkout, nothing executed)."""
    git(repo, "fetch", "--no-tags", "--quiet", "origin",
        f"+refs/heads/{default_branch}:refs/remotes/origin/{default_branch}",
        f"+refs/pull/{number}/head:refs/remotes/origin/pull/{number}")
    if not git(repo, "cat-file", "-t", head_sha, check=False).strip() == "commit":
        git(repo, "fetch", "--no-tags", "--quiet", "origin", head_sha)


def check(api, repo: str, slug: str, default_branch: str, pr=None, sha=None, base_ref=None,
          fetch: bool = True, post: bool = True, target_url=None, log=None) -> list:
    """Judge the open pull requests of `pr` or of the head commit `sha`; post their status."""
    log = log or (lambda message: print(message, file=sys.stderr))
    base_ref = base_ref or f"origin/{default_branch}"
    if pr is not None:
        pulls = [api.get(f"repos/{slug}/pulls/{pr}")]
    else:
        pulls = [pull for pull in api.get(f"repos/{slug}/commits/{sha}/pulls") or []
                 if pull.get("head", {}).get("sha") == sha]
    outcomes = []
    for pull in pulls:
        number, head_sha = pull["number"], pull["head"]["sha"]
        if pull.get("state") != "open":
            log(f"#{number}: not open, skipped")
            continue
        if pull["base"]["ref"] != default_branch:
            log(f"#{number}: targets {pull['base']['ref']}, not {default_branch}; skipped")
            continue
        result = None
        try:
            if fetch:
                fetch_pull_request(repo, default_branch, number, head_sha)
            result = match(repo, base_ref, head_sha, pull["head"].get("ref"))
            required = required_workflows(repo, base_ref, result["files"], default_branch)
            runs = (api.get(f"repos/{slug}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100")
                    or {}).get("workflow_runs", [])
            combined = api.get(f"repos/{slug}/commits/{head_sha}/status") or {}
            statuses = {item["context"]: item["state"] for item in combined.get("statuses", [])}
            state, description = evaluate(result, required, runs, statuses)
        except Exception as exc:  # fail closed, with the reason where the owner looks
            required = []
            state, description = "error", truncate(f"merge-conditions could not judge: {exc}")
        log(f"#{number} {head_sha[:12]}: {state} - {description}")
        if result is not None:
            log(json.dumps({key: result[key] for key in ("kind", "change", "gates", "hits", "unaccounted",
                                                          "waived", "errors")}, indent=2))
            log("required workflows: " + (", ".join(required) or "none"))
        if post:
            api.post_status(slug, head_sha, state, description, target_url)
        outcomes.append({"number": number, "sha": head_sha, "state": state, "description": description})
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

    match_parser = commands.add_parser("match", help="classify a diff; prints JSON")
    match_parser.add_argument("--base", required=True, help="base ref, e.g. origin/main")
    match_parser.add_argument("--head", required=True, help="head commit or ref")
    match_parser.add_argument("--branch", help="pull request branch name, e.g. feat/<change-id>")

    check_parser = commands.add_parser("check", help="judge pull requests and post the merge-conditions status")
    check_parser.add_argument("--repo", required=True, help="owner/name")
    check_parser.add_argument("--default-branch", required=True)
    target = check_parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--pr", type=int)
    target.add_argument("--sha")
    check_parser.add_argument("--dry-run", action="store_true", help="print, do not post the status")

    validate_parser = commands.add_parser("validate", help="check triggers.yaml / classification.yaml files")
    validate_parser.add_argument("files", nargs="+")

    args = parser.parse_args(argv)
    if args.command == "match":
        print(json.dumps(match(args.directory, args.base, args.head, args.branch), indent=2))
        return 0
    if args.command == "validate":
        errors = validate_files(args.files)
        for message in errors:
            print(message, file=sys.stderr)
        return 1 if errors else 0
    server = os.environ.get("GITHUB_SERVER_URL")
    run_id = os.environ.get("GITHUB_RUN_ID")
    target_url = f"{server}/{args.repo}/actions/runs/{run_id}" if server and run_id else None
    outcomes = check(GitHub(), args.directory, args.repo, args.default_branch, pr=args.pr, sha=args.sha,
                     post=not args.dry_run, target_url=target_url)
    print(json.dumps(outcomes, indent=2))
    return 1 if any(outcome["state"] == "error" for outcome in outcomes) else 0


if __name__ == "__main__":
    sys.exit(main())
