# Finding format — shared by every review angle

Every reviewer of the harness reports in this format, one line per finding, so the orchestrator can
merge, verify and count findings across angles without reinterpreting them.

```
path/to/file.ext:LINE: <emoji> <SEVERITY>: <problem>. Fails when: <concrete scenario>. Fix: <fix>.
```

- **Severity**:
  - 🛑 BLOCKER — wrong behaviour on a reachable path, lost data, broken contract, security hole, or a
    specified scenario left with no test that would catch its regression;
  - 🔴 MAJOR — a defect a user or the next change will hit; a test that exercises a behaviour without
    asserting its outcome (when another test still covers the scenario);
  - 🟡 MINOR — debt, clarity, a convention bent without harm;
  - 🔵 NIT — cosmetic; only when asked.
- **Fails when** is mandatory for BLOCKER and MAJOR: the input, state or sequence that produces the
  wrong outcome. A finding without a scenario is an opinion and is downgraded to MINOR.
- **Location**: the file and line in the reviewed head. Something missing points to where it should be
  (`path:LINE` of the function that lacks the check). A surviving mutant points to the **mutated code
  line**; the missing test goes in `Fix`.
- **No praise, no scope creep**: review the diff and what it touches, not the rest of the repository.
- **Mechanical evidence** goes under the line, indented: the command run and the relevant output
  (failing assertion, surviving mutant, measured value against its threshold).

The reviewer ends its report with one line per mechanical check it ran (`<command> → <result>`), one
line per forked skill it invoked (`forked: code-review medium`), and, when its angle's tooling is
absent, the line `no mechanical backing: <what is missing>`.

If the angle finds nothing: `OK.` followed by those lines.
