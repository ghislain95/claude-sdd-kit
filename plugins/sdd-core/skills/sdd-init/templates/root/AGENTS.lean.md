<!-- sdd:note: version de AGENTS.md pour l'option lean (module unique, petit projet) -->
# AGENTS.md — équipe virtuelle Claude pour {{PROJECT_NAME}}

Les agents de ce projet sont définis dans [`.claude/agents/`](.claude/agents/) ; leur table de
routage est dans [`.claude/agents/README.md`](.claude/agents/README.md), et le cycle qu'ils suivent
dans [`CLAUDE.md`](CLAUDE.md) §3 (feature) et §8 (routage). Pour ajouter un rôle : un fichier
`.claude/agents/<nom>.md` avec `name`, une `description` « UTILISER QUAND … NE PAS UTILISER … »,
`tools` et `model: {{AGENT_MODEL}}`, puis une ligne dans le README des agents.
