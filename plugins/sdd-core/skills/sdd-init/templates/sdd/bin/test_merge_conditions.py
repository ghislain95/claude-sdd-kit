#!/usr/bin/env python3
"""Tests of merge_conditions.py. Run: python3 .sdd/bin/test_merge_conditions.py (needs git and PyYAML).

Every test builds a throwaway git repository in a temporary directory: `main` is the base branch, the
pull request is a branch cut from it. GitHub is replaced by a stub fed with API fixtures.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

sys.dont_write_bytecode = True  # no __pycache__ left in .sdd/bin/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import merge_conditions as mc  # noqa: E402

GIT_ENV = dict(
    os.environ,
    GIT_CONFIG_GLOBAL=os.devnull,
    GIT_CONFIG_NOSYSTEM="1",
    GIT_AUTHOR_NAME="test",
    GIT_AUTHOR_EMAIL="test@example.invalid",
    GIT_COMMITTER_NAME="test",
    GIT_COMMITTER_EMAIL="test@example.invalid",
)
os.environ.update({key: GIT_ENV[key] for key in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM")})

TRIGGERS = """\
intent:
  paths:
    - web/src/**
  content:
    - paths: [ 'api/**' ]
      pattern: 'localStorage\\.setItem'
irreversible:
  paths:
    - db/migrations/**
gate_machinery:
  paths:
    - tools/release.sh
"""


def classification(change="add-export", intent=False, irreversible=False, intent_waived=(),
                   irreversible_waived=()):
    def section(gate_open, waived):
        lines = [f"  open: {'true' if gate_open else 'false'}", "  evidence: stated in the proposal"]
        if waived:
            lines.append("  waived:")
            for trigger, reason in waived:
                lines.append(f"    - trigger: '{trigger}'")
                lines.append(f"      reason: {reason}")
        return "\n".join(lines)

    return (f"change: {change}\nintent:\n{section(intent, intent_waived)}\n"
            f"irreversible:\n{section(irreversible, irreversible_waived)}\n")


class Repo:
    def __init__(self):
        self.path = tempfile.mkdtemp(prefix="merge-conditions-")
        self.git("init", "-q", "-b", "main")
        self.git("config", "commit.gpgsign", "false")

    def git(self, *args):
        return subprocess.run(["git", "-C", self.path, *args], env=GIT_ENV, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()

    def write(self, path, content):
        full = os.path.join(self.path, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(content)

    def remove(self, path):
        self.git("rm", "-q", "--", path)

    def move(self, source, target):
        os.makedirs(os.path.dirname(os.path.join(self.path, target)), exist_ok=True)
        self.git("mv", source, target)

    def commit(self, message="commit"):
        self.git("add", "--all")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def branch(self, name):
        self.git("switch", "-q", "-c", name, "main")

    def cleanup(self):
        shutil.rmtree(self.path, ignore_errors=True)


class MatcherTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write(".sdd/triggers.yaml", TRIGGERS)
        self.repo.write("README.md", "project\n")
        self.repo.write("api/store.js", "localStorage.setItem('v1', data)\n")

    def approve(self, text, change="add-export"):
        self.repo.write(f"openspec/changes/{change}/proposal.md", "# Proposal\n")
        self.repo.write(f"openspec/changes/{change}/{mc.CLASSIFICATION_FILE}", text)

    def pull_request(self, branch="feat/add-export"):
        self.repo.commit("base")
        self.repo.branch(branch)

    def match(self, branch="feat/add-export"):
        head = self.repo.commit("pull request")
        return mc.match(self.repo.path, "main", head, branch)

    # --- change pull requests -------------------------------------------------------------

    def test_undeclared_migration_is_unaccounted(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("db/migrations/V2__add_column.sql", "alter table t add c int;\n")
        result = self.match()
        self.assertEqual(result["kind"], "change")
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual([(hit["trigger"], hit["file"]) for hit in result["unaccounted"]],
                         [("db/migrations/**", "db/migrations/V2__add_column.sql")])
        self.assertIn("unaccounted irreversible db/migrations/V2__add_column.sql", result["description"])

    def test_declared_gate_is_accounted(self):
        self.approve(classification(irreversible=True))
        self.pull_request()
        self.repo.write("db/migrations/V2__add_column.sql", "alter table t add c int;\n")
        result = self.match()
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual(result["unaccounted"], [])
        self.assertEqual(result["description"], "gates: irreversible")

    def test_waived_intent_path_stays_closed(self):
        self.approve(classification(intent_waived=[("web/src/**", "renames a private helper")]))
        self.pull_request()
        self.repo.write("web/src/helper.ts", "export const x = 1\n")
        result = self.match()
        self.assertEqual(result["gates"], [])
        self.assertEqual(result["unaccounted"], [])
        self.assertEqual([(item["trigger"], item["reason"]) for item in result["waived"]],
                         [("web/src/**", "renames a private helper")])
        self.assertEqual(result["description"], "gates: none")

    def test_waiver_of_another_trigger_does_not_close_the_gate(self):
        self.approve(classification(intent_waived=[("web/**", "not the trigger as written")]))
        self.pull_request()
        self.repo.write("web/src/helper.ts", "export const x = 1\n")
        result = self.match()
        self.assertEqual(result["gates"], ["intent"])
        self.assertEqual(len(result["unaccounted"]), 1)

    def test_gate_machinery_ignores_waivers(self):
        self.approve(classification(irreversible_waived=[(".github/workflows/**", "only a comment")]))
        self.pull_request()
        self.repo.write(".github/workflows/ci.yml", "name: CI\n")
        result = self.match()
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual(result["waived"], [])
        self.assertEqual([hit["file"] for hit in result["unaccounted"]], [".github/workflows/ci.yml"])

    def test_default_gate_machinery_applies_without_triggers_file(self):
        os.remove(os.path.join(self.repo.path, ".sdd/triggers.yaml"))
        self.approve(classification())
        self.pull_request()
        self.repo.write("vercel.json", "{}\n")
        result = self.match()
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual(result["hits"][0]["trigger"], "vercel.json")

    def test_project_gate_machinery_is_added_to_the_defaults(self):
        self.approve(classification(irreversible_waived=[("tools/release.sh", "typo")]))
        self.pull_request()
        self.repo.write("tools/release.sh", "echo release\n")
        result = self.match()
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertTrue(result["hits"][0]["machinery"])

    def test_classification_edited_in_the_pull_request_is_judged_by_the_base_version(self):
        self.approve(classification())
        self.pull_request()
        # The pull request opens the gate in its own copy: the base version must still be used.
        self.repo.write("openspec/changes/add-export/classification.yaml", classification(irreversible=True))
        self.repo.write("db/migrations/V2__add_column.sql", "alter table t add c int;\n")
        result = self.match()
        self.assertEqual(result["kind"], "change")
        self.assertEqual(result["gates"], ["irreversible"])
        triggers = sorted(hit["trigger"] for hit in result["unaccounted"])
        self.assertEqual(triggers, ["db/migrations/**", mc.CLASSIFICATION_TRIGGER])

    def test_branch_carrying_the_approved_classification_is_no_edit(self):
        self.repo.commit("base")
        self.repo.branch("feat/add-export")
        self.approve(classification())  # same content added on both sides (squashed framing PR)
        self.repo.write("src/app.py", "print(1)\n")
        head = self.repo.commit("pull request")
        self.repo.git("switch", "-q", "main")
        self.approve(classification())
        self.repo.commit("framing merged")
        result = mc.match(self.repo.path, "main", head, "feat/add-export")
        self.assertEqual(result["kind"], "change")
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["description"], "gates: none")

    def test_triggers_edited_in_the_pull_request_are_ignored(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write(".sdd/triggers.yaml", "intent: {}\nirreversible: {}\n")
        self.repo.write("db/migrations/V2__add_column.sql", "alter table t add c int;\n")
        result = self.match()
        triggers = sorted(hit["trigger"] for hit in result["unaccounted"])
        self.assertEqual(triggers, [".sdd/**", "db/migrations/**"])

    def test_content_pattern_matches_added_lines_only(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("api/store.js", "const unrelated = 1\n")  # removes the matching line
        result = self.match()
        self.assertEqual(result["hits"], [])
        self.assertEqual(result["gates"], [])

    def test_content_pattern_reports_the_added_line(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("api/store.js", "localStorage.setItem('v1', data)\nconst a = 1\n"
                                        "localStorage.setItem('v2', other)\n")
        result = self.match()
        self.assertEqual(result["gates"], ["intent"])
        self.assertEqual([(hit["file"], hit["line"]) for hit in result["hits"]], [("api/store.js", 3)])
        self.assertIn("api/store.js:3", result["description"])

    def test_content_pattern_respects_its_paths(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("scripts/store.js", "localStorage.setItem('v2', other)\n")
        self.assertEqual(self.match()["hits"], [])

    def test_invalid_approved_classification_fails(self):
        self.approve("change: add-export\nintent: {open: maybe}\n")
        self.pull_request()
        self.repo.write("src/app.py", "print(1)\n")
        result = self.match()
        self.assertEqual(result["kind"], "change")
        self.assertTrue(result["errors"])
        self.assertIn("approved classification.yaml", result["description"])

    # --- framing, archive, unclassified --------------------------------------------------

    def test_framing_pull_request(self):
        self.pull_request("docs/add-export-framing")
        self.approve(classification(intent=True))
        result = self.match("docs/add-export-framing")
        self.assertEqual((result["kind"], result["change"], result["gates"]), ("framing", "add-export", ["framing"]))
        self.assertEqual(result["description"], "gates: framing")

    def test_reclassification_is_a_framing_pull_request(self):
        self.approve(classification())
        self.pull_request("docs/add-export-framing-2")
        self.repo.write("openspec/changes/add-export/classification.yaml", classification(irreversible=True))
        self.assertEqual(self.match("docs/add-export-framing-2")["kind"], "framing")

    def test_framing_with_code_is_not_framing(self):
        self.pull_request("docs/add-export-framing")
        self.approve(classification())
        self.repo.write("src/app.py", "print(1)\n")
        self.assertEqual(self.match("docs/add-export-framing")["kind"], "unclassified")

    def test_framing_with_invalid_classification_fails(self):
        self.pull_request("docs/add-export-framing")
        self.approve("change: add-export\n")
        result = self.match("docs/add-export-framing")
        self.assertEqual(result["kind"], "framing")
        self.assertTrue(result["errors"])

    def test_archive_pull_request(self):
        self.approve(classification(intent=True))
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("openspec/specs/export/spec.md", "# export\n")
        self.repo.write("docs/ROADMAP.md", "- [x] export\n")
        result = self.match("chore/add-export-archive")
        self.assertEqual((result["kind"], result["change"]), ("archive", "add-export"))
        self.assertEqual(result["gates"], [])  # own diff only: the change's open intent gate is not carried
        self.assertEqual(result["hits"], [])

    def test_archive_with_an_edited_classification_opens_the_gate(self):
        self.approve(classification())
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("openspec/changes/archive/2026-11-13-add-export/classification.yaml",
                        classification(irreversible=True))
        result = self.match("chore/add-export-archive")
        self.assertEqual(result["kind"], "archive")
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual(result["unaccounted"][0]["trigger"], mc.CLASSIFICATION_TRIGGER)

    def test_archive_with_code_is_a_change(self):
        self.approve(classification())
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("src/app.py", "print(1)\n")
        self.assertEqual(self.match("chore/add-export-archive")["kind"], "change")

    def test_unclassified_pull_request(self):
        self.pull_request("fix/api-typo")
        self.repo.write("api/handler.py", "print(1)\n")
        result = self.match("fix/api-typo")
        self.assertEqual((result["kind"], result["change"], result["gates"]), ("unclassified", None, ["unclassified"]))
        self.assertEqual(result["description"], "gates: unclassified")

    def test_change_found_from_the_branch_name(self):
        self.approve(classification())
        self.pull_request("feat/add-export")
        self.repo.write("src/app.py", "print(1)\n")
        result = self.match("feat/add-export")
        self.assertEqual((result["kind"], result["change"]), ("change", "add-export"))

    def test_several_change_folders_without_a_matching_branch_fail(self):
        self.approve(classification())
        self.approve(classification("other"), change="other")
        self.pull_request("feat/something")
        self.repo.write("openspec/changes/add-export/tasks.md", "- [x] 1\n")
        self.repo.write("openspec/changes/other/tasks.md", "- [x] 1\n")
        self.repo.write("src/app.py", "print(1)\n")
        result = self.match("feat/something")
        self.assertTrue(any("several change folders" in error for error in result["errors"]))


class SchemaTest(unittest.TestCase):
    def test_triggers_errors(self):
        _, errors = mc.load_triggers("intent:\n  paths: [ 3 ]\n  content:\n    - pattern: '('\nextra: 1\n")
        self.assertEqual(len(errors), 3, errors)

    def test_classification_requires_evidence(self):
        text = "change: x\nintent: {open: false}\nirreversible: {open: false, evidence: none}\n"
        result, errors = mc.load_classification(text, "x")
        self.assertIsNone(result)
        self.assertEqual(errors, ["classification.yaml: intent.evidence: expected the reason for the answer"])

    def test_classification_change_must_match_its_folder(self):
        _, errors = mc.load_classification(classification("x"), "y")
        self.assertEqual(len(errors), 1)


class GlobTest(unittest.TestCase):
    def test_github_path_filter_syntax(self):
        cases = [
            ("docs/*", "docs/a.md", True), ("docs/*", "docs/a/b.md", False),
            ("docs/**", "docs/a/b.md", True), ("**/README.md", "README.md", True),
            ("**/README.md", "a/b/README.md", True), ("*.md", "a/b.md", False),
            ("**.js", "src/js/app.js", True), ("*.jsx?", "page.js", True), ("*.jsx?", "page.jsx", True),
            ("db/V[0-9]*.sql", "db/V2__x.sql", True), ("db/V[0-9]*.sql", "db/Vx.sql", False),
        ]
        for pattern, path, expected in cases:
            self.assertEqual(mc.glob_match(pattern, path), expected, (pattern, path))

    def test_negation_order(self):
        self.assertFalse(mc.filter_includes(["docs/**", "!docs/**/*.md"], "docs/a.md"))
        self.assertTrue(mc.filter_includes(["docs/**", "!docs/**/*.md", "docs/keep.md"], "docs/keep.md"))


# --- check -------------------------------------------------------------------------------------

WORKFLOWS = {
    "always.yml": "name: Always\non: [pull_request]\njobs: {}\n",
    "web.yml": "name: Web\non:\n  pull_request:\n    paths: [ 'web/**' ]\njobs: {}\n",
    "not-docs.yml": "name: NotDocs\non:\n  pull_request:\n    paths-ignore: [ 'docs/**' ]\njobs: {}\n",
    "deploy.yml": "name: Deploy\non:\n  push:\n    branches: [ main ]\njobs: {}\n",
    "release-branch.yml": "name: Release\non:\n  pull_request:\n    branches: [ 'release/**' ]\njobs: {}\n",
    "labels-only.yml": "name: Labels\non:\n  pull_request:\n    types: [ labeled ]\njobs: {}\n",
    "merge-conditions.yml": "name: Merge conditions\non: pull_request_target\njobs: {}\n",
}


class StubGitHub:
    def __init__(self, pulls, runs=(), statuses=None):
        self.pulls, self.runs, self.statuses, self.posted = pulls, list(runs), statuses or {}, []

    def get(self, path):
        if "/pulls/" in path and "/commits/" not in path:
            number = int(path.rsplit("/", 1)[1])
            return next(pull for pull in self.pulls if pull["number"] == number)
        if path.endswith("/pulls"):
            return self.pulls
        if "/actions/runs" in path:
            return {"total_count": len(self.runs), "workflow_runs": self.runs}
        if path.endswith("/status"):
            return {"statuses": [{"context": key, "state": value} for key, value in self.statuses.items()]}
        raise AssertionError(f"unexpected API call {path}")

    def post_status(self, repo, sha, state, description, target_url=None):
        self.posted.append((repo, sha, state, description))


def run(name, status="completed", conclusion="success", run_id=1, sha=None):
    return {"id": run_id, "path": f".github/workflows/{name}", "event": "pull_request",
            "status": status, "conclusion": conclusion, "head_sha": sha}


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write(".sdd/triggers.yaml", TRIGGERS)
        for name, content in WORKFLOWS.items():
            self.repo.write(f".github/workflows/{name}", content)
        self.repo.write("README.md", "project\n")

    def head(self, files, branch="feat/add-export", classified=True):
        if classified:
            self.repo.write("openspec/changes/add-export/proposal.md", "# Proposal\n")
            self.repo.write("openspec/changes/add-export/classification.yaml", classification())
        self.repo.commit("base")
        self.repo.branch(branch)
        for path, content in files.items():
            self.repo.write(path, content)
        return self.repo.commit("pull request")

    def judge(self, sha, branch="feat/add-export", runs=(), statuses=None):
        pull = {"number": 7, "state": "open", "head": {"sha": sha, "ref": branch}, "base": {"ref": "main"}}
        stub = StubGitHub([pull], runs, statuses)
        outcome = mc.check(stub, self.repo.path, "acme/app", "main", pr=7, base_ref="main", fetch=False,
                           log=lambda message: None)
        self.assertEqual(len(stub.posted), 1)
        self.assertEqual(stub.posted[0][:3], ("acme/app", sha, outcome[0]["state"]))
        return outcome[0]

    def test_required_workflows_follow_the_path_filters(self):
        sha = self.head({"src/app.py": "print(1)\n"})
        files = mc.match(self.repo.path, "main", sha, "feat/add-export")["files"]
        required = mc.required_workflows(self.repo.path, "main", files, "main")
        self.assertEqual(required, [".github/workflows/always.yml", ".github/workflows/not-docs.yml"])
        required = mc.required_workflows(self.repo.path, "main", ["web/a.ts"], "main")
        self.assertIn(".github/workflows/web.yml", required)
        required = mc.required_workflows(self.repo.path, "main", ["docs/a.md"], "main")
        self.assertEqual(required, [".github/workflows/always.yml"])

    def test_pull_request_outside_every_filter_is_still_judged(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml")],
                             statuses={"review-harness": "success", "opsx-verify": "success"})
        self.assertEqual((outcome["state"], outcome["description"]), ("success", "gates: none"))

    def test_workflow_edited_in_the_pull_request_is_judged_by_the_base_version(self):
        sha = self.head({"src/app.py": "print(1)\n",
                         ".github/workflows/not-docs.yml": "name: NotDocs\non:\n  pull_request:\n"
                                                           "    paths: [ 'nothing/**' ]\njobs: {}\n"})
        outcome = self.judge(sha, runs=[run("always.yml")],
                             statuses={"review-harness": "success", "opsx-verify": "success"})
        self.assertEqual(outcome["state"], "failure")  # gate machinery hit, irreversible not declared
        self.assertIn("no run of not-docs", outcome["description"])

    def test_running_workflow_is_pending(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml", status="in_progress", conclusion=None)],
                             statuses={"review-harness": "success", "opsx-verify": "success"})
        self.assertEqual(outcome["state"], "pending")
        self.assertEqual(outcome["description"], "gates: none - always running")

    def test_failed_workflow_is_a_failure_even_when_another_is_pending(self):
        sha = self.head({"src/app.py": "print(1)\n"})
        outcome = self.judge(sha, runs=[run("always.yml", conclusion="failure"),
                                        run("not-docs.yml", status="queued", conclusion=None, run_id=2)],
                             statuses={"review-harness": "success", "opsx-verify": "success"})
        self.assertEqual(outcome["state"], "failure")
        self.assertTrue(outcome["description"].startswith("gates: none - always failure"))

    def test_latest_run_of_a_workflow_wins(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml", conclusion="failure", run_id=1),
                                        run("always.yml", run_id=2)],
                             statuses={"review-harness": "success", "opsx-verify": "success"})
        self.assertEqual(outcome["state"], "success")

    def test_missing_review_harness_status_is_not_green(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml")], statuses={"opsx-verify": "success"})
        self.assertEqual(outcome["state"], "pending")
        self.assertIn("no review-harness status", outcome["description"])

    def test_failed_review_harness_status_is_a_failure(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml")],
                             statuses={"review-harness": "failure", "opsx-verify": "success"})
        self.assertEqual(outcome["state"], "failure")

    def test_unclassified_needs_no_review_status_and_reports_its_gate(self):
        sha = self.head({"docs/a.md": "x\n"}, branch="fix/typo", classified=False)
        outcome = self.judge(sha, branch="fix/typo", runs=[run("always.yml")])
        self.assertEqual((outcome["state"], outcome["description"]), ("success", "gates: unclassified"))

    def test_owner_merged_gate_is_success_with_its_gate(self):
        self.repo.write("openspec/changes/add-export/proposal.md", "# Proposal\n")
        self.repo.write("openspec/changes/add-export/classification.yaml", classification(intent=True))
        sha = self.head({"web/src/page.ts": "x\n"}, classified=False)
        outcome = self.judge(sha, runs=[run("always.yml"), run("web.yml", run_id=2), run("not-docs.yml", run_id=3)],
                             statuses={"review-harness": "success", "opsx-verify": "success"})
        self.assertEqual((outcome["state"], outcome["description"]), ("success", "gates: intent"))

    def test_description_fits_in_a_commit_status(self):
        files = {f"db/migrations/V{index}__a_rather_long_migration_name.sql": "x\n" for index in range(2, 12)}
        sha = self.head(files)
        outcome = self.judge(sha, runs=[])
        self.assertEqual(outcome["state"], "failure")
        self.assertLessEqual(len(outcome["description"]), mc.DESCRIPTION_MAX)
        self.assertTrue(outcome["description"].startswith("gates: irreversible - unaccounted irreversible"))

    def test_check_by_sha_judges_only_the_matching_pull_request(self):
        sha = self.head({"docs/a.md": "x\n"})
        pulls = [{"number": 7, "state": "open", "head": {"sha": sha, "ref": "feat/add-export"}, "base": {"ref": "main"}},
                 {"number": 8, "state": "open", "head": {"sha": "0" * 40, "ref": "other"}, "base": {"ref": "main"}},
                 {"number": 9, "state": "open", "head": {"sha": sha, "ref": "x"}, "base": {"ref": "release"}}]
        stub = StubGitHub(pulls, [run("always.yml")], {"review-harness": "success", "opsx-verify": "success"})
        outcomes = mc.check(stub, self.repo.path, "acme/app", "main", sha=sha, base_ref="main", fetch=False,
                            log=lambda message: None)
        self.assertEqual([outcome["number"] for outcome in outcomes], [7])
        self.assertEqual(len(stub.posted), 1)

    def test_crash_posts_an_error(self):
        pull = {"number": 7, "state": "open", "head": {"sha": "f" * 40, "ref": "feat/x"}, "base": {"ref": "main"}}
        self.repo.commit("base")
        stub = StubGitHub([pull])
        outcome = mc.check(stub, self.repo.path, "acme/app", "main", pr=7, base_ref="main", fetch=False,
                           log=lambda message: None)
        self.assertEqual(outcome[0]["state"], "error")
        self.assertEqual(stub.posted[0][2], "error")


class ValidateCommandTest(unittest.TestCase):
    def test_validate_reports_each_invalid_file(self):
        folder = tempfile.mkdtemp(prefix="merge-conditions-validate-")
        self.addCleanup(shutil.rmtree, folder, True)
        good = os.path.join(folder, "add-export", "classification.yaml")
        bad = os.path.join(folder, "triggers.yaml")
        os.makedirs(os.path.dirname(good))
        with open(good, "w") as handle:
            handle.write(classification())
        with open(bad, "w") as handle:
            handle.write(textwrap.dedent("intent:\n  paths: oops\n"))
        self.assertEqual(mc.validate_files([good]), [])
        self.assertEqual(len(mc.validate_files([good, bad])), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
