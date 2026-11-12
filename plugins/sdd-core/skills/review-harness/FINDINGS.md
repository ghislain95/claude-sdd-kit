# Finding format — shared by every review angle

Every reviewer of the harness reports in this format, one line per finding, so the orchestrator can
merge, verify and count findings across angles without reinterpreting them.

```
path/to/file.ext:LINE: <emoji> <SEVERITY>: <problem>. Fails when: <concrete scenario>. Fix: <fix>.
```

- **Severity**: 🛑 BLOCKER (wrong behaviour, lost data, broken contract, security hole, a test that
  proves nothing on the changed code), 🔴 MAJOR (a defect a user or the next change will hit),
  🟡 MINOR (debt, clarity, a convention bent without harm), 🔵 NIT (cosmetic; only when asked).
- **Fails when** is mandatory for BLOCKER and MAJOR: the input, state or sequence that produces the
  wrong outcome. A finding without a scenario is an opinion and is downgraded to MINOR.
- **Location**: the file and line in the diff's final state. A finding about something missing points
  to where it should be (`path:LINE` of the function that lacks the check).
- **No praise, no scope creep**: review the diff and what it touches, not the rest of the repository.
- **Mechanical evidence** goes after the line, indented: the command run and the relevant output
  (failing assertion, surviving mutant, measured value against its threshold).

The reviewer ends its report with one line per mechanical check it ran (`<command> → <result>`) and,
when its angle's tooling is absent, the line `no mechanical backing: <what is missing>`.

If the angle finds nothing: `OK.` followed by the mechanical lines.
