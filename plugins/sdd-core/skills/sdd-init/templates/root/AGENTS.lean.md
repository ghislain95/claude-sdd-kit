<!-- sdd:note: AGENTS.md version for the lean option (single module, small project) -->
# AGENTS.md — the Claude virtual team for {{PROJECT_NAME}}

This project's agents are defined in [`.claude/agents/`](.claude/agents/); their routing table
is in [`.claude/agents/README.md`](.claude/agents/README.md), and the cycle they follow
in [`CLAUDE.md`](CLAUDE.md) §3 (feature) and §8 (routing). To add a role: a file
`.claude/agents/<name>.md` with `name`, a `description` "USE WHEN … DO NOT USE …",
`tools` and `model: {{AGENT_MODEL}}`, then a line in the agents README.
