// Shared by the mods of this repository: Conventional Commit blocks in Claude's messages. Copied into each
// mod's hooks/shared/ by scripts/sync-shared.sh: edit it here, then run the script.

export type CommitBlock = { subject: string; type: string; scope: string; body: string; hasCoAuthor: boolean; text: string }

/** Fenced blocks that open with a Conventional Commit subject. */
export function commitBlocks(text: string): CommitBlock[] {
  const blocks: CommitBlock[] = []
  for (const match of text.matchAll(/```[a-z]*\n([\s\S]*?)```/g)) {
    const content = (match[1] ?? '').replace(/\s+$/, '')
    const lines = content.split('\n')
    const subject = (lines[0] ?? '').trim()
    const head = /^(feat|fix|chore|docs|refactor|test|perf|build|ci|style)\(([^)]+)\)!?:\s+\S/.exec(subject)
    if (head === null) continue
    const body = lines.slice(1).join('\n').trim()
    blocks.push({
      subject,
      type: head[1] ?? '',
      scope: head[2] ?? '',
      body,
      hasCoAuthor: /co-authored-by/i.test(content),
      text: content,
    })
  }
  return blocks
}
