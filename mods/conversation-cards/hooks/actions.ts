// What the cards' buttons do. Each takes `$` and is declared at the top
// level, as the engine requires of a function `$` is handed to.

import { atom, memberOf, read, update } from 'claude-code'
import type { EngineInterface } from 'claude-code'



const qaMarks = atom({ plugin: 'conversation-cards', key: 'qaMarks' } as const, {})

const reportOpen = atom({ plugin: 'conversation-cards', key: 'reportOpen' } as const, {})

const briefs = atom({ plugin: 'conversation-cards', key: 'briefs' } as const, null)

/** The clipboard through pbcopy: the mods copy has no path on the desktop surface yet. */
export async function copyText($: EngineInterface, text: string, label: string): Promise<void> {
  try {
    const result = await $.process.run(['/usr/bin/pbcopy'], { stdin: text, env: { LANG: 'en_US.UTF-8', LC_ALL: 'en_US.UTF-8' } })
    $.ui.toast(result.exitCode === 0 ? `${label} copié` : `Copie impossible (pbcopy ${result.exitCode})`)
  } catch {
    $.ui.toast('Copie impossible : pbcopy absent')
  }
}

/** Adds a line to the prompt box, after what is already typed. */
export async function addToPrompt($: EngineInterface, text: string): Promise<void> {
  const filled = await $.prompt.fill({ text: `${text}\n`, mode: 'append' }).catch(() => undefined)
  if (filled !== undefined && !filled.isFilled) $.ui.toast(`Prompt occupé : « ${text} » non ajouté`)
}

/** Sets a mark of a message's card (`qa:0` → ok, `q:Q1` → B…); the same mark again clears it. */
export async function markQa($: EngineInterface, messageId: string, key: string, mark: string): Promise<void> {
  await update($, memberOf(qaMarks, { requestId: messageId }), current => {
    const next = { ...current }
    if (next[key] === mark) delete next[key]
    else next[key] = mark
    return next
  })
}

export async function toggleReportSection($: EngineInterface, messageId: string, kind: string): Promise<void> {
  await update($, memberOf(reportOpen, { requestId: messageId }), current => ({ ...current, [kind]: current[kind] !== true }))
}

/** Opens a file at a line in IntelliJ (Toolbox launcher), else in the default app for it. */
/**
 * Where a cited path really is: as written from the project root, else inside an active change's folder
 * (`verification/x.md` is `openspec/changes/<change>/verification/x.md`), else the first file of the project ending with it.
 */
async function resolveFile($: EngineInterface, root: string, path: string, changeNames: string[]): Promise<string | null> {
  if (path.startsWith('/')) return (await $.fs.exists(path).catch(() => false)) ? path : null
  const candidates = [`${root}/${path}`, ...changeNames.map(name => `${root}/openspec/changes/${name}/${path}`)]
  for (const candidate of candidates) if (await $.fs.exists(candidate).catch(() => false)) return candidate
  const found = await $.process
    .run(['/usr/bin/find', root, '-path', `*/${path}`, '-not', '-path', '*/node_modules/*', '-not', '-path', '*/.git/*', '-print', '-quit'], { timeoutMs: 5000 })
    .catch(() => null)
  const first = found?.exitCode === 0 ? found.stdout.split('\n')[0]?.trim() : undefined
  return first !== undefined && first !== '' ? first : null
}

export async function openFile($: EngineInterface, root: string, home: string, path: string, line: number | null, changeNames: string[] = []): Promise<void> {
  const resolved = await resolveFile($, root, path, changeNames)
  if (resolved === null) {
    $.ui.toast(`Fichier introuvable : ${path}`)
    return
  }
  const absolute = resolved
  const launcher = `${home}/Library/Application Support/JetBrains/Toolbox/scripts/idea`
  try {
    const args = line !== null ? [launcher, '--line', String(line), absolute] : [launcher, absolute]
    const result = await $.process.run(args, { timeoutMs: 15000 })
    if (result.exitCode === 0) return
  } catch {
    // fall back below
  }
  await $.process.run(['/usr/bin/open', absolute]).catch(() => undefined)
}

/** Three bullets from Haiku for a long message, on demand. */
export async function summarize($: EngineInterface, messageId: string, text: string): Promise<void> {
  await update($, memberOf(briefs, { requestId: messageId }), () => '…')
  const result = await $.model.complete({
    model: 'claude-haiku-5-5',
    system: 'Tu résumes un message d’un assistant de code pour son lecteur pressé. Français, 3 puces courtes au maximum, sans rien perdre de ce qui compte : décisions, chiffres, demandes faites au lecteur. Pas de préambule.',
    prompt: text.slice(0, 24000),
    maxTokens: 300,
  })
  await update($, memberOf(briefs, { requestId: messageId }), () =>
    result.isAnswered ? result.text.trim() : `Résumé indisponible (${result.reason}).`,
  )
}

export const ANSWERS_START = '── Réponses aux cartes ──'

export const ANSWERS_END = '── fin des réponses ──'

/** Puts the answers block at the end of the prompt, or in place of the block already there; the rest of the prompt is kept. */
export function mergeAnswers(current: string, block: string): string {
  const framed = `${ANSWERS_START}\n${block}\n${ANSWERS_END}`
  const start = current.indexOf(ANSWERS_START)
  const end = current.indexOf(ANSWERS_END)
  if (start !== -1 && end > start) return `${current.slice(0, start)}${framed}${current.slice(end + ANSWERS_END.length)}`
  const trimmed = current.replace(/\s+$/, '')
  return trimmed === '' ? framed : `${trimmed}\n\n${framed}`
}

export async function insertAnswers($: EngineInterface, block: string): Promise<void> {
  const box = await $.prompt.read().catch(() => ({ text: '', cursor: 0 }))
  const filled = await $.prompt.fill({ text: mergeAnswers(box.text, block), mode: 'replace' }).catch(() => undefined)
  $.ui.toast(filled?.isFilled === false ? 'Prompt occupé : réponses non ajoutées' : 'Réponses ajoutées à la fin du prompt (ton texte est conservé)')
}

/** Opens a labelled line at the end of the prompt, where the note is written in the full-size box. */
export async function notePrompt($: EngineInterface, label: string): Promise<void> {
  const box = await $.prompt.read().catch(() => ({ text: '', cursor: 0 }))
  const separator = box.text === '' || box.text.endsWith('\n') ? '' : '\n'
  await $.prompt.fill({ text: `${separator}[${label}] `, mode: 'append' }).catch(() => undefined)
  $.ui.toast('Écris ta note dans le prompt, après l’étiquette')
}

