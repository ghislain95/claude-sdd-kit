# conversation-cards

Claude's messages drawn as cards in the transcript, in every project:

- **Questions** (`### Q1 · …` with `- A · …` options): every option with its explanation, the recommended one
  marked, one « Envoyer mes réponses » for the whole card.
- **End-of-task reports**: asks, decisions, reserves, sections one by one, findings, QA, the commit.
- **The cockpit block** (` ```cockpit `): hidden from the message, turned into buttons.
- **Commits**: the message, copied in one press, and whether it landed.
- **Tool calls**: one compact row each, which opens onto Claude Code's own row.
- **The spinner**: gains the context's fill.
- **The display contract**: three rules added to the system prompt so Claude keeps the shapes the cards read.

`/cartes` shows the switches; `/cartes off|on` turns the cards off or on; `/cartes contrat off|on` the contract.
Both are remembered across sessions. The message itself is never changed: a message the cards do not
recognise is left to Claude Code.
