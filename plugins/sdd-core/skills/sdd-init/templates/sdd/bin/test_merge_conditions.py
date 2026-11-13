#!/usr/bin/env python3
"""Tests of merge_conditions.py. Run: python3 .sdd/bin/test_merge_conditions.py (needs git and PyYAML).

Every test builds a throwaway git repository in a temporary directory: `main` is the base branch, the
pull request is a branch cut from it. GitHub is replaced by a stub fed with API fixtures.
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import re
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

    def match(self, branch="feat/add-export", tasks="add-export"):
        """Commit the pull request; a change pull request ticks a task of its own change folder."""
        if tasks:
            self.repo.write(f"openspec/changes/{tasks}/tasks.md", "- [x] 1.1 done\n")
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
        self.approve(classification(irreversible_waived=[(".github/**", "only a comment")]))
        self.pull_request()
        self.repo.write(".github/workflows/ci.yml", "name: CI\n")
        result = self.match()
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual(result["waived"], [])
        self.assertEqual([hit["file"] for hit in result["unaccounted"]], [".github/workflows/ci.yml"])

    def test_built_in_gate_machinery(self):
        # None of these is in TRIGGERS: each changes what CI or the check does.
        for path in (".github/actions/test/action.yml", ".github/CODEOWNERS", ".gitattributes",
                     "web/.gitattributes", ".gitmodules", "openspec/config.yaml", ".sdd/harness.yaml",
                     ".claude/hooks/block.sh", ".claude/settings.json", "vercel.json"):
            with self.subTest(path=path):
                repo = Repo()
                self.addCleanup(repo.cleanup)
                repo.write(".sdd/triggers.yaml", "intent: {}\nirreversible: {}\n")
                repo.write(f"openspec/changes/add-export/{mc.CLASSIFICATION_FILE}", classification())
                repo.commit("base")
                repo.branch("feat/add-export")
                repo.write("openspec/changes/add-export/tasks.md", "- [x] 1.1\n")
                repo.write(path, "x\n")
                result = mc.match(repo.path, "main", repo.commit("pull request"), "feat/add-export")
                self.assertEqual([hit["file"] for hit in result["unaccounted"] if hit.get("machinery")], [path])

    def test_missing_triggers_file_is_an_error_and_keeps_the_default_machinery(self):
        os.remove(os.path.join(self.repo.path, ".sdd/triggers.yaml"))
        self.approve(classification())
        self.pull_request()
        self.repo.write("vercel.json", "{}\n")
        result = self.match()
        self.assertEqual(result["errors"], [".sdd/triggers.yaml missing on the base ref"])
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

    def test_classification_added_by_a_change_pull_request_is_gate_machinery(self):
        # R1: a classification absent from the base ref, added for another change, is an edit too.
        self.approve(classification())
        self.pull_request()
        self.repo.write("openspec/changes/sneaky/classification.yaml",
                        classification("sneaky", irreversible_waived=[("db/migrations/**", "anything")]))
        result = self.match()
        self.assertIn((mc.CLASSIFICATION_TRIGGER, "openspec/changes/sneaky/classification.yaml"),
                      [(hit["trigger"], hit["file"]) for hit in result["hits"]])
        self.assertIn("several change folders touched (add-export, sneaky)", result["errors"])

    def test_classification_added_under_the_archive_is_gate_machinery(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("openspec/changes/archive/2026-01-01-old/classification.yaml", classification("old"))
        result = self.match()
        self.assertEqual(result["kind"], "change")
        self.assertEqual([(hit["trigger"], hit["file"]) for hit in result["unaccounted"]],
                         [(mc.CLASSIFICATION_TRIGGER, "openspec/changes/archive/2026-01-01-old/classification.yaml")])

    def test_classification_deleted_by_a_change_pull_request_is_gate_machinery(self):
        self.approve(classification())
        self.pull_request()
        self.repo.remove("openspec/changes/add-export/classification.yaml")
        result = self.match()
        self.assertEqual([hit["file"] for hit in result["unaccounted"]],
                         ["openspec/changes/add-export/classification.yaml"])

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
        self.repo.write("api/other.js", "const b = 2\n")
        self.assertEqual(self.match()["hits"], [])

    def test_content_pattern_reads_files_gitattributes_hides(self):
        # R2: `-diff` / `binary` on the base ref must not blind the content triggers.
        self.repo.write(".gitattributes", "*.js -diff\napi/*.dat binary\n")
        self.approve(classification())
        self.pull_request()
        self.repo.write("api/new.js", "localStorage.setItem('v2', data)\n")
        self.repo.write("api/blob.dat", "localStorage.setItem('v3', data)\n")
        result = self.match()
        self.assertEqual([(hit["file"], hit["line"]) for hit in result["hits"]],
                         [("api/blob.dat", 1), ("api/new.js", 1)])

    def test_content_pattern_ignores_the_callers_diff_configuration(self):
        # R3: diff.noprefix / diff.mnemonicPrefix in the caller's configuration.
        self.approve(classification())
        self.pull_request()
        self.repo.write("api/new.js", "localStorage.setItem('v2', data)\n")
        head = self.repo.commit("pull request")
        for setting in ("diff.noprefix", "diff.mnemonicPrefix"):
            with self.subTest(setting=setting):
                self.repo.git("config", setting, "true")
                result = mc.match(self.repo.path, "main", head, "feat/add-export")
                self.repo.git("config", "--unset", setting)
                self.assertEqual([hit["file"] for hit in result["hits"]], ["api/new.js"])

    def test_content_pattern_with_unusual_file_names(self):
        # repro2: a backslash is C-quoted in diff headers; `[ab]` is a pathspec pattern unless literal.
        self.approve(classification())
        self.pull_request()
        self.repo.write("api/we\\ird.js", "localStorage.setItem(1)\n")
        self.repo.write("api/[ab].js", "const quiet = 1\n")
        self.repo.write("api/a.js", "localStorage.setItem(2)\n")
        result = self.match()
        self.assertEqual(sorted(hit["file"] for hit in result["hits"]), ["api/a.js", "api/we\\ird.js"])

    def test_invalid_approved_classification_fails(self):
        self.approve("change: add-export\nintent: {open: maybe}\n")
        self.pull_request()
        self.repo.write("src/app.py", "print(1)\n")
        result = self.match()
        self.assertEqual((result["kind"], result["gates"], result["label"]), ("change", ["invalid"], "gates: invalid"))
        self.assertTrue(result["errors"])
        self.assertTrue(result["description"].startswith("gates: invalid - approved classification.yaml"))

    # --- which change a pull request belongs to -------------------------------------------

    def test_branch_name_alone_is_unclassified(self):
        # R4: a hotfix named after an in-flight change, touching no change folder, gets no waiver.
        self.approve(classification(intent_waived=[("web/src/**", "rename")]))
        self.pull_request("fix/add-export")
        self.repo.write("web/src/checkout.tsx", "export const Pay = () => null\n")
        result = self.match("fix/add-export", tasks=None)
        self.assertEqual((result["kind"], result["change"], result["gates"]), ("unclassified", None, ["unclassified"]))
        self.assertEqual(result["waived"], [])

    def test_change_folder_must_match_the_branch(self):
        # repro2: a pull request cannot pick the classification that judges it.
        self.approve(classification("strict", intent=True), change="strict")
        self.approve(classification("permissive", intent_waived=[("web/src/**", "x")]), change="permissive")
        self.pull_request("feat/strict")
        self.repo.write("web/src/page.tsx", "x\n")
        result = self.match("feat/strict", tasks="permissive")
        self.assertEqual((result["kind"], result["change"]), ("unclassified", None))
        self.assertEqual(result["errors"], ["change folder permissive does not match the branch feat/strict"])

    def test_several_change_folders_fail(self):
        self.approve(classification())
        self.approve(classification("other"), change="other")
        self.pull_request()
        self.repo.write("openspec/changes/other/tasks.md", "- [x] 1\n")
        self.repo.write("src/app.py", "print(1)\n")
        result = self.match()
        self.assertEqual(result["change"], None)
        self.assertIn("several change folders touched (add-export, other)", result["errors"])

    # --- framing, archive, unclassified --------------------------------------------------

    def test_framing_pull_request(self):
        self.pull_request("docs/add-export-framing")
        self.approve(classification(intent=True))
        result = self.match("docs/add-export-framing", tasks=None)
        self.assertEqual((result["kind"], result["change"], result["gates"]), ("framing", "add-export", ["framing"]))
        self.assertEqual(result["description"], "gates: framing")

    def test_reclassification_is_a_framing_pull_request(self):
        self.approve(classification())
        self.pull_request("docs/add-export-framing-2")
        self.repo.write("openspec/changes/add-export/classification.yaml", classification(irreversible=True))
        result = self.match("docs/add-export-framing-2", tasks=None)
        self.assertEqual((result["kind"], result["errors"], result["hits"]), ("framing", [], []))

    def test_framing_with_code_is_not_framing(self):
        self.pull_request("docs/add-export-framing")
        self.approve(classification())
        self.repo.write("src/app.py", "print(1)\n")
        self.assertEqual(self.match("docs/add-export-framing", tasks=None)["kind"], "unclassified")

    def test_framing_with_invalid_classification_fails(self):
        self.pull_request("docs/add-export-framing")
        self.approve("change: add-export\n")
        result = self.match("docs/add-export-framing", tasks=None)
        self.assertEqual(result["kind"], "framing")
        self.assertTrue(result["errors"])

    def test_archive_pull_request(self):
        self.approve(classification(intent=True))
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("openspec/specs/export/spec.md", "# export\n")
        self.repo.write("docs/ROADMAP.md", "- [x] export\n")
        result = self.match("chore/add-export-archive", tasks=None)
        self.assertEqual((result["kind"], result["change"]), ("archive", "add-export"))
        self.assertEqual(result["gates"], [])  # own diff only: the change's open intent gate is not carried
        self.assertEqual(result["hits"], [])

    def test_archive_with_an_edited_classification_opens_the_gate(self):
        self.approve(classification())
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("openspec/changes/archive/2026-11-13-add-export/classification.yaml",
                        classification(irreversible=True))
        result = self.match("chore/add-export-archive", tasks=None)
        self.assertEqual(result["kind"], "archive")
        self.assertEqual(result["gates"], ["irreversible"])
        self.assertEqual(sorted(hit["file"] for hit in result["unaccounted"]),
                         ["openspec/changes/add-export/classification.yaml",
                          "openspec/changes/archive/2026-11-13-add-export/classification.yaml"])

    def test_archive_with_code_is_a_change(self):
        self.approve(classification())
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("src/app.py", "print(1)\n")
        self.assertEqual(self.match("chore/add-export-archive", tasks=None)["kind"], "change")

    def test_archive_folder_of_another_change_is_not_an_archive(self):
        # R8: `2026-11-13-add-export` is not an archive folder of `export`.
        for change in ("export", "add-export"):
            self.approve(classification(change), change=change)
        self.pull_request("chore/export-archive")
        self.repo.move("openspec/changes/export", "openspec/changes/archive/2026-11-13-export")
        self.repo.write("openspec/changes/archive/2026-11-13-add-export/proposal.md", "# not this change\n")
        self.assertEqual(self.match("chore/export-archive", tasks=None)["kind"], "change")

    def test_archive_into_a_folder_whose_name_merely_ends_with_the_change_is_not_an_archive(self):
        self.approve(classification("export"), change="export")
        self.pull_request("chore/export-archive")
        self.repo.move("openspec/changes/export", "openspec/changes/archive/2026-11-13-add-export")
        result = self.match("chore/export-archive", tasks=None)
        self.assertEqual(result["kind"], "change")
        self.assertIn("openspec/changes/export/classification.yaml", [hit["file"] for hit in result["unaccounted"]])

    def test_archive_into_two_folders_is_not_an_archive(self):
        self.approve(classification())
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/2026-11-13-add-export")
        self.repo.write("openspec/changes/archive/add-export/notes.md", "# a second archive folder\n")
        self.assertEqual(self.match("chore/add-export-archive", tasks=None)["kind"], "change")

    def test_archive_into_the_undated_folder(self):
        self.approve(classification())
        self.pull_request("chore/add-export-archive")
        self.repo.move("openspec/changes/add-export", "openspec/changes/archive/add-export")
        result = self.match("chore/add-export-archive", tasks=None)
        self.assertEqual((result["kind"], result["hits"]), ("archive", []))

    def test_unclassified_pull_request(self):
        self.pull_request("fix/api-typo")
        self.repo.write("api/handler.py", "print(1)\n")
        result = self.match("fix/api-typo", tasks=None)
        self.assertEqual((result["kind"], result["change"], result["gates"]), ("unclassified", None, ["unclassified"]))
        self.assertEqual(result["description"], "gates: unclassified")

    # --- the deploy guard's call ---------------------------------------------------------

    def run_main(self, *argv):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
            code = mc.main(["-C", self.repo.path, *argv])
        return code, (json.loads(output.getvalue()) if output.getvalue() else None)

    def merged(self, branch="feat/add-export"):
        """Merge the pull request into main; (first parent of the merge commit, pull request head)."""
        self.repo.write("openspec/changes/add-export/tasks.md", "- [x] 1.1 done\n")
        head = self.repo.commit("pull request")
        self.repo.git("switch", "-q", "main")
        self.repo.git("merge", "-q", "--no-ff", "-m", "merge", branch)
        return self.repo.git("rev-parse", "HEAD^1"), head

    def test_match_after_the_merge_judges_the_merged_pull_request(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("src/app.py", "print(1)\n")
        base, head = self.merged()
        code, result = self.run_main("match", "--base", base, "--head", head, "--branch", "feat/add-export")
        self.assertEqual((code, result["kind"], result["base"], result["gates"]), (0, "change", base, []))

    def test_match_exits_non_zero_on_an_unaccounted_hit(self):
        self.approve(classification())
        self.pull_request()
        self.repo.write("db/migrations/V2__add_column.sql", "alter table t add c int;\n")
        base, head = self.merged()
        code, result = self.run_main("match", "--base", base, "--head", head, "--branch", "feat/add-export")
        self.assertEqual((code, result["gates"]), (1, ["irreversible"]))

    def test_match_exits_non_zero_on_an_invalid_classification(self):
        self.approve("change: add-export\n")
        self.pull_request()
        self.repo.write("src/app.py", "print(1)\n")
        base, head = self.merged()
        code, result = self.run_main("match", "--base", base, "--head", head, "--branch", "feat/add-export")
        self.assertEqual((code, result["label"]), (1, "gates: invalid"))

    def test_match_exits_2_when_it_cannot_judge(self):
        self.repo.commit("base")
        code, result = self.run_main("match", "--base", "main", "--head", "0" * 40, "--branch", "feat/x")
        self.assertEqual((code, result), (2, None))


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
    "not-main.yml": "name: NotMain\non:\n  pull_request:\n    branches-ignore: [ 'main' ]\njobs: {}\n",
    "labels-only.yml": "name: Labels\non:\n  pull_request:\n    types: [ labeled ]\njobs: {}\n",
    "nested/inner.yml": "name: Inner\non: [pull_request]\njobs: {}\n",  # not a workflow: GitHub ignores subfolders
    "merge-conditions.yml": "name: Merge conditions\non: pull_request_target\njobs: {}\n",
}
GREEN = {"review-harness": "success", "opsx-verify": "success"}


def quiet(message):
    pass


def pull_request(number, sha, branch="feat/add-export", base="main", state="open"):
    return {"number": number, "state": state, "head": {"sha": sha, "ref": branch}, "base": {"ref": base}}


class StubGitHub:
    """GitHub's REST API as `check` uses it, with its pagination (30 items when per_page is absent)."""

    def __init__(self, pulls, runs=(), statuses=None, moves=None):
        self.pulls, self.runs, self.statuses, self.posted = pulls, list(runs), dict(statuses or {}), []
        self.moves = moves or {}  # number: (reads after which the head moves, new head sha)
        self.reads = {}

    @staticmethod
    def page(items, params):
        size, page = int(params.get("per_page", 30)), int(params.get("page", 1))
        return items[(page - 1) * size:page * size]

    def get(self, path):
        route, _, query = path.partition("?")
        params = dict(item.split("=", 1) for item in query.split("&") if item)
        single = re.fullmatch(r"repos/[^/]+/[^/]+/pulls/(\d+)", route)
        if single:
            number = int(single.group(1))
            pull = next(pull for pull in self.pulls if pull["number"] == number)
            self.reads[number] = self.reads.get(number, 0) + 1
            after, sha = self.moves.get(number, (None, None))
            if after is not None and self.reads[number] > after:
                return dict(pull, head=dict(pull["head"], sha=sha))
            return pull
        if route.endswith("/pulls"):
            pulls = self.pulls
            if "state" in params:
                pulls = [pull for pull in pulls
                         if pull["state"] == params["state"] and pull["base"]["ref"] == params.get("base")]
            return self.page(pulls, params)
        if route.endswith("/actions/runs"):
            return {"total_count": len(self.runs), "workflow_runs": self.page(self.runs, params)}
        if route.endswith("/status"):
            statuses = [{"context": key, "state": value} for key, value in self.statuses.items()]
            return {"total_count": len(statuses), "statuses": self.page(statuses, params)}
        raise AssertionError(f"unexpected API call {path}")

    def post_status(self, repo, sha, state, description, target_url=None):
        self.posted.append((repo, sha, state, description))


def run(name, sha, status="completed", conclusion="success", run_id=1, event="pull_request"):
    return {"id": run_id, "path": f".github/workflows/{name}", "event": event,
            "status": status, "conclusion": conclusion, "head_sha": sha}


class CheckTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.cleanup)
        self.repo.write(".sdd/triggers.yaml", TRIGGERS)
        for name, content in WORKFLOWS.items():
            self.repo.write(f".github/workflows/{name}", content)
        self.repo.write("README.md", "project\n")

    def head(self, files, branch="feat/add-export", classified=True, removed=()):
        """Commit the base, then the pull request; a change pull request ticks one of its tasks."""
        if classified:
            self.repo.write("openspec/changes/add-export/proposal.md", "# Proposal\n")
            self.repo.write("openspec/changes/add-export/classification.yaml", classification())
        self.repo.commit("base")
        self.repo.branch(branch)
        if branch == "feat/add-export":
            self.repo.write("openspec/changes/add-export/tasks.md", "- [x] 1.1\n")
        for path, content in files.items():
            self.repo.write(path, content)
        for path in removed:
            self.repo.remove(path)
        return self.repo.commit("pull request")

    def base7(self):
        return self.repo.git("rev-parse", "main")[:7]

    def judge(self, sha, branch="feat/add-export", runs=(), statuses=None):
        stub = StubGitHub([pull_request(7, sha, branch)], runs, statuses)
        outcome = mc.check(stub, self.repo.path, "acme/app", "main", pr=7, sha=sha, base_ref="main", fetch=False,
                           log=quiet)
        self.assertEqual(len(stub.posted), 1)
        self.assertEqual(stub.posted[0][:4], ("acme/app", sha, outcome[0]["state"], outcome[0]["description"]))
        return outcome[0]

    def green_runs(self, sha):
        return [run("always.yml", sha), run("not-docs.yml", sha, run_id=2)]

    # --- required workflows ------------------------------------------------------------------

    def test_required_workflows_follow_the_path_filters(self):
        sha = self.head({"src/app.py": "print(1)\n"})
        files = mc.match(self.repo.path, "main", sha, "feat/add-export")["files"]
        required = mc.required_workflows(self.repo.path, "main", files, "main")
        self.assertEqual(required, [".github/workflows/always.yml", ".github/workflows/not-docs.yml"])
        required = mc.required_workflows(self.repo.path, "main", ["web/a.ts"], "main")
        self.assertEqual(required, [".github/workflows/always.yml", ".github/workflows/not-docs.yml",
                                    ".github/workflows/web.yml"])
        required = mc.required_workflows(self.repo.path, "main", ["docs/a.md"], "main")
        self.assertEqual(required, [".github/workflows/always.yml"])
        required = mc.required_workflows(self.repo.path, "main", ["docs/a.md"], "release/1")
        self.assertEqual(required, [".github/workflows/always.yml", ".github/workflows/not-main.yml",
                                    ".github/workflows/release-branch.yml"])

    def test_unreadable_workflow_is_required(self):
        self.repo.write(".github/workflows/broken.yml", "on: [ pull_request\n")
        self.repo.commit("base")
        required = mc.required_workflows(self.repo.path, "main", ["docs/a.md"], "main")
        self.assertEqual(required, [".github/workflows/always.yml", ".github/workflows/broken.yml"])

    def test_pull_request_outside_every_filter_is_still_judged(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=self.green_runs(sha), statuses=GREEN)
        self.assertEqual((outcome["state"], outcome["description"]), ("success", f"gates: none; base {self.base7()}"))

    def test_running_workflow_is_pending(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml", sha, status="in_progress", conclusion=None),
                                        run("not-docs.yml", sha, run_id=2)], statuses=GREEN)
        self.assertEqual(outcome["state"], "pending")
        self.assertEqual(outcome["description"], f"gates: none - always running; base {self.base7()}")

    def test_failed_workflow_is_a_failure_even_when_another_is_pending(self):
        sha = self.head({"src/app.py": "print(1)\n"})
        outcome = self.judge(sha, runs=[run("always.yml", sha, conclusion="failure"),
                                        run("not-docs.yml", sha, status="queued", conclusion=None, run_id=2)],
                             statuses=GREEN)
        self.assertEqual(outcome["state"], "failure")
        self.assertTrue(outcome["description"].startswith("gates: none - always failure; not-docs running"))

    def test_latest_run_of_a_workflow_wins(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=[run("always.yml", sha, conclusion="failure", run_id=1),
                                        run("always.yml", sha, run_id=3), run("not-docs.yml", sha, run_id=2)],
                             statuses=GREEN)
        self.assertEqual(outcome["state"], "success")

    def test_run_of_another_commit_does_not_count(self):
        sha = self.head({"docs/a.md": "x\n"})
        for other in ("0" * 40, None):
            with self.subTest(head_sha=other):
                runs = [run("always.yml", other, run_id=5), run("not-docs.yml", sha, run_id=2)]
                outcome = self.judge(sha, runs=runs, statuses=GREEN)
                self.assertEqual(outcome["state"], "pending")
                self.assertIn("no run of always", outcome["description"])

    def test_run_of_another_event_does_not_count(self):
        sha = self.head({"docs/a.md": "x\n"})
        runs = [run("always.yml", sha, event="push", run_id=5), run("not-docs.yml", sha, run_id=2)]
        outcome = self.judge(sha, runs=runs, statuses=GREEN)
        self.assertEqual(outcome["state"], "pending")
        self.assertIn("no run of always", outcome["description"])

    def test_runs_and_statuses_are_read_past_the_first_page(self):
        sha = self.head({"docs/a.md": "x\n"})
        noise = [run("lint.yml", sha, run_id=100 + index) for index in range(150)]
        statuses = {f"ci/{index}": "success" for index in range(120)}
        statuses.update(GREEN)
        outcome = self.judge(sha, runs=noise + self.green_runs(sha), statuses=statuses)
        self.assertEqual(outcome["state"], "success")

    # --- review statuses --------------------------------------------------------------------

    def test_missing_review_harness_status_is_not_green(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=self.green_runs(sha), statuses={"opsx-verify": "success"})
        self.assertEqual(outcome["state"], "pending")
        self.assertIn("no review-harness status", outcome["description"])

    def test_pending_review_harness_status_is_pending(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=self.green_runs(sha),
                             statuses={"review-harness": "pending", "opsx-verify": "success"})
        self.assertEqual(outcome["description"], f"gates: none - review-harness pending; base {self.base7()}")
        self.assertEqual(outcome["state"], "pending")

    def test_failed_review_harness_status_is_a_failure(self):
        sha = self.head({"docs/a.md": "x\n"})
        outcome = self.judge(sha, runs=self.green_runs(sha),
                             statuses={"review-harness": "failure", "opsx-verify": "success"})
        self.assertEqual(outcome["state"], "failure")

    def test_unclassified_needs_no_review_status_and_reports_its_gate(self):
        sha = self.head({"docs/a.md": "x\n"}, branch="fix/typo", classified=False)
        outcome = self.judge(sha, branch="fix/typo", runs=[run("always.yml", sha)])
        self.assertEqual((outcome["state"], outcome["description"]),
                         ("success", f"gates: unclassified; base {self.base7()}"))

    def test_owner_merged_gate_is_success_with_its_gate(self):
        self.repo.write("openspec/changes/add-export/proposal.md", "# Proposal\n")
        self.repo.write("openspec/changes/add-export/classification.yaml", classification(intent=True))
        sha = self.head({"web/src/page.ts": "x\n"}, classified=False)
        outcome = self.judge(sha, runs=self.green_runs(sha) + [run("web.yml", sha, run_id=3)], statuses=GREEN)
        self.assertEqual((outcome["state"], outcome["description"]), ("success", f"gates: intent; base {self.base7()}"))

    def test_description_fits_in_a_commit_status_and_keeps_the_base(self):
        files = {f"db/migrations/V{index}__a_rather_long_migration_name.sql": "x\n" for index in range(2, 12)}
        sha = self.head(files)
        outcome = self.judge(sha, runs=[])
        self.assertEqual(outcome["state"], "failure")
        self.assertLessEqual(len(outcome["description"]), mc.DESCRIPTION_MAX)
        self.assertTrue(outcome["description"].startswith("gates: irreversible - unaccounted irreversible"))
        self.assertTrue(outcome["description"].endswith(f"...; base {self.base7()}"))

    # --- workflows the pull request edits ---------------------------------------------------

    def gated_head(self, files, removed=()):
        """A change pull request whose classification opens the irreversible gate (gate machinery)."""
        self.repo.write("openspec/changes/add-export/proposal.md", "# Proposal\n")
        self.repo.write("openspec/changes/add-export/classification.yaml", classification(irreversible=True))
        return self.head(files, classified=False, removed=removed)

    def test_required_workflow_deleted_by_the_pull_request_is_its_own_reason(self):
        sha = self.gated_head({"src/app.py": "print(1)\n"}, removed=[".github/workflows/not-docs.yml"])
        outcome = self.judge(sha, runs=[run("always.yml", sha)], statuses=GREEN)
        self.assertEqual((outcome["state"], outcome["description"]),
                         ("failure", f"gates: irreversible - not-docs deleted by the pull request; base {self.base7()}"))

    def test_required_workflow_filtered_out_by_the_pull_request_is_its_own_reason(self):
        sha = self.gated_head({"src/app.py": "print(1)\n",
                               ".github/workflows/not-docs.yml": "name: NotDocs\non:\n  pull_request:\n"
                                                                 "    paths: [ 'nothing/**' ]\njobs: {}\n"})
        outcome = self.judge(sha, runs=[run("always.yml", sha)], statuses=GREEN)
        self.assertEqual((outcome["state"], outcome["description"]),
                         ("failure", f"gates: irreversible - not-docs no longer runs on the pull request; "
                                     f"base {self.base7()}"))

    def test_required_workflow_edited_but_still_running_is_awaited(self):
        sha = self.gated_head({"src/app.py": "print(1)\n",
                               ".github/workflows/not-docs.yml": "name: NotDocs2\non: [pull_request]\njobs: {}\n"})
        outcome = self.judge(sha, runs=[run("always.yml", sha)], statuses=GREEN)
        self.assertEqual((outcome["state"], outcome["description"]),
                         ("pending", f"gates: irreversible - no run of not-docs; base {self.base7()}"))

    def test_workflow_added_by_the_pull_request_is_its_own_reason(self):
        sha = self.gated_head({"src/app.py": "print(1)\n",
                               ".github/workflows/new.yml": "name: New\non: [pull_request]\njobs: {}\n",
                               ".github/workflows/helpers/data.yml": "not: a workflow\n"})
        outcome = self.judge(sha, runs=self.green_runs(sha), statuses=GREEN)
        self.assertEqual((outcome["state"], outcome["description"]),
                         ("failure", f"gates: irreversible - new added by the pull request; base {self.base7()}"))

    # --- which pull requests are judged, and when the status is posted ----------------------

    def test_check_by_sha_judges_only_the_matching_open_pull_request(self):
        sha = self.head({"docs/a.md": "x\n"})
        pulls = [pull_request(7, sha), pull_request(8, "0" * 40, "other"),
                 pull_request(9, sha, "x", base="release"), pull_request(10, sha, state="closed")]
        stub = StubGitHub(pulls, self.green_runs(sha), GREEN)
        outcomes = mc.check(stub, self.repo.path, "acme/app", "main", sha=sha, base_ref="main", fetch=False,
                            log=quiet)
        self.assertEqual([outcome["number"] for outcome in outcomes], [7])
        self.assertEqual([posted[2] for posted in stub.posted], ["success"])

    def test_closed_pull_request_is_not_judged(self):
        sha = self.head({"docs/a.md": "x\n"})
        stub = StubGitHub([pull_request(7, sha, state="closed")], self.green_runs(sha), GREEN)
        outcomes = mc.check(stub, self.repo.path, "acme/app", "main", sha=sha, base_ref="main", fetch=False,
                            log=quiet)
        self.assertEqual((outcomes, stub.posted), ([], []))

    def test_event_head_that_is_no_longer_the_head_is_not_judged(self):
        sha = self.head({"docs/a.md": "x\n"})
        stub = StubGitHub([pull_request(7, "1" * 40)], self.green_runs(sha), GREEN)
        outcomes = mc.check(stub, self.repo.path, "acme/app", "main", pr=7, sha=sha, base_ref="main", fetch=False,
                            log=quiet)
        self.assertEqual((outcomes, stub.posted), ([], []))

    def test_head_moved_while_judging_is_not_posted(self):
        sha = self.head({"docs/a.md": "x\n"})
        stub = StubGitHub([pull_request(7, sha)], self.green_runs(sha), GREEN, moves={7: (1, "1" * 40)})
        outcomes = mc.check(stub, self.repo.path, "acme/app", "main", pr=7, sha=sha, base_ref="main", fetch=False,
                            log=quiet)
        self.assertEqual(([outcome["posted"] for outcome in outcomes], stub.posted), ([False], []))

    def test_push_to_main_re_judges_every_open_pull_request(self):
        first = self.head({"docs/a.md": "x\n"})
        self.repo.git("switch", "-q", "main")
        self.repo.branch("fix/typo")
        self.repo.write("docs/b.md", "y\n")
        second = self.repo.commit("second pull request")
        pulls = [pull_request(7, first), pull_request(8, second, "fix/typo"),
                 pull_request(9, second, "x", base="release"), pull_request(10, first, state="closed")]
        stub = StubGitHub(pulls, self.green_runs(first) + [run("always.yml", second, run_id=4)], GREEN)
        outcomes = mc.check(stub, self.repo.path, "acme/app", "main", all_open=True, base_ref="main", fetch=False,
                            log=quiet)
        base7 = self.base7()
        self.assertEqual([outcome["number"] for outcome in outcomes], [7, 8])
        self.assertEqual([posted[1:] for posted in stub.posted], [
            (first, "pending", f"re-judging: main moved to {base7}"),
            (second, "pending", f"re-judging: main moved to {base7}"),
            (first, "success", f"gates: none; base {base7}"),
            (second, "success", f"gates: unclassified; base {base7}"),
        ])

    def test_crash_posts_an_error(self):
        self.repo.commit("base")
        stub = StubGitHub([pull_request(7, "f" * 40, "feat/x")])
        outcome = mc.check(stub, self.repo.path, "acme/app", "main", pr=7, base_ref="main", fetch=False, log=quiet)
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
