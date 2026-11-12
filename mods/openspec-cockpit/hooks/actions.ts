// What the cockpit's buttons do. Each takes `$` and is declared at the top
// level, as the engine requires of a function `$` is handed to.

import { atom, memberOf, read, update } from 'claude-code'
import type { EngineInterface } from 'claude-code'

import type { ActionButton } from './logic'


const busy = atom({ plugin: 'openspec-cockpit', key: 'busy' } as const, null)

const collapsed = atom({ plugin: 'openspec-cockpit', key: 'collapsed' } as const, {})

const ritualMarks = atom({ plugin: 'openspec-cockpit', key: 'ritualMarks' } as const, {})

const GRAPHIFY_CANDIDATES = ['graphify', '/opt/homebrew/bin/graphify', '/usr/local/bin/graphify']

/** The clipboard through pbcopy: the mods copy has no path on the desktop surface yet. */
export async function copyText($: EngineInterface, text: string, label: string): Promise<void> {
  try {
    const result = await $.process.run(['/usr/bin/pbcopy'], { stdin: text, env: { LANG: 'en_US.UTF-8', LC_ALL: 'en_US.UTF-8' } })
    $.ui.toast(result.exitCode === 0 ? `${label} copié` : `Copie impossible (pbcopy ${result.exitCode})`)
  } catch {
    $.ui.toast('Copie impossible : pbcopy absent')
  }
}

export async function fillPrompt($: EngineInterface, text: string): Promise<void> {
  await $.prompt.fill({ text, mode: 'replace' }).catch(() => undefined)
}

/** `graphify update .` in the project, the busy flag up while it runs. */
export async function refreshGraph($: EngineInterface, root: string, home: string, onDone: () => void): Promise<void> {
  if ((await read($, busy)) !== null) return
  await update($, busy, () => 'graph')
  try {
    for (const binary of [...GRAPHIFY_CANDIDATES, `${home}/.local/bin/graphify`]) {
      try {
        const result = await $.process.run([binary, 'update', '.'], { cwd: root, timeoutMs: 180 * 1000 })
        $.ui.toast(result.exitCode === 0 ? 'Graph rafraîchi' : `graphify a échoué (${result.exitCode})`)
        return
      } catch {
        // next candidate
      }
    }
    $.ui.toast('graphify introuvable')
  } finally {
    await update($, busy, () => null)
    onDone()
  }
}

export async function runAction($: EngineInterface, action: ActionButton, root: string, home: string, onDone: () => void): Promise<void> {
  if (action.kind === 'fill') await fillPrompt($, action.value)
  else if (action.kind === 'copy') await copyText($, action.value, 'Message de commit')
  else await refreshGraph($, root, home, onDone)
}

export async function toggleSection($: EngineInterface, id: string): Promise<void> {
  let after: Record<string, boolean> = {}
  await update($, collapsed, current => {
    after = { ...current, [id]: current[id] !== true }
    return after
  })
  await $.store.set('collapsed', after)
}

export async function toggleRitual($: EngineInterface, key: string): Promise<void> {
  let after: Record<string, boolean> = {}
  await update($, ritualMarks, current => {
    after = { ...current, [key]: current[key] !== true }
    return after
  })
  await $.store.set('ritualMarks', after)
}

