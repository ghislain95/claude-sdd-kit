// Pure logic of the cards: the tool rows, the spinner's suffix, the display contract.
// No `$` here, so every function is testable under `claude plugin test`.

import type { CardToggles } from '../types'
import { formatDuration } from './shared/format'

export { cleanMarkdown, formatDuration, plural, truncate } from './shared/format'

/** The spinner's addition: the context's fill, or nothing. */
export function spinnerSuffix(contextPercent: number | null): string {
  return contextPercent === null ? '' : ` · contexte ${Math.round(contextPercent)} %`
}

/** The two switches in words, for /cartes. */
export function togglesText(toggles: CardToggles): string {
  return `cartes ${toggles.cards ? 'on' : 'off'} · consigne ${toggles.contract ? 'on' : 'off'}`
}

export type ToolCard = { icon: string; title: string; detail: string; tone: 'tool' | 'agent' | 'web' }

function relative(path: unknown, root: string): string {
  if (typeof path !== 'string') return ''
  return path.startsWith(`${root}/`) ? path.slice(root.length + 1) : path
}

function text(value: unknown): string {
  return typeof value === 'string' ? value.replace(/\s+/g, ' ').trim() : ''
}

/** How a tool call reads as a compact card, or null to leave Claude Code's own row. */
export function toolCard(tool: string, input: Record<string, unknown>, root: string): ToolCard | null {
  switch (tool) {
    case 'Bash': {
      const description = text(input.description)
      const command = text(input.command)
      return { icon: '❯', title: description || command, detail: description ? command : '', tone: 'tool' }
    }
    case 'Read': {
      const range =
        typeof input.offset === 'number' ? ` · l. ${input.offset}${typeof input.limit === 'number' ? `+${input.limit}` : ''}` : ''
      return { icon: '◇', title: relative(input.file_path, root) || 'fichier', detail: range.replace(/^ · /, ''), tone: 'tool' }
    }
    case 'Grep':
    case 'Glob':
      return {
        icon: '⌕',
        title: text(input.pattern),
        detail: [relative(input.path, root), text(input.glob)].filter(part => part !== '').join(' · '),
        tone: 'tool',
      }
    case 'Agent':
    case 'Task':
      return { icon: '◆', title: text(input.description) || 'agent', detail: text(input.subagent_type), tone: 'agent' }
    case 'Workflow': {
      const name = /name:\s*['"]([^'"]+)['"]/.exec(text(input.script))?.[1] ?? text(input.name)
      return { icon: '⧉', title: name || 'workflow', detail: text(input.description), tone: 'agent' }
    }
    case 'Skill':
      return { icon: '✦', title: text(input.skill), detail: text(input.args), tone: 'agent' }
    case 'WebFetch':
      return { icon: '↗', title: text(input.url), detail: '', tone: 'web' }
    case 'WebSearch':
      return { icon: '⌕', title: text(input.query), detail: 'web', tone: 'web' }
    case 'ToolSearch':
      return { icon: '⌕', title: text(input.query), detail: 'outils', tone: 'tool' }
    default:
      return null
  }
}

export function toolTail(state: {
  isRunning: boolean
  isErrored: boolean
  isInterrupted: boolean
  durationMs: number | undefined
}): { text: string; tone: 'running' | 'error' | 'muted' | 'ok' } {
  if (state.isRunning) return { text: 'en cours', tone: 'running' }
  if (state.isInterrupted) return { text: 'interrompu', tone: 'muted' }
  if (state.isErrored) return { text: '✗ erreur', tone: 'error' }
  if (state.durationMs === undefined) return { text: '✓', tone: 'ok' }
  const seconds = state.durationMs / 1000
  const shown = seconds < 10 ? `${seconds.toFixed(1).replace('.', ',')} s` : formatDuration(state.durationMs)
  return { text: `${shown} ✓`, tone: 'ok' }
}

export const CONTRACT = [
  'OpenSpec cockpit display contract. The desktop UI draws cards from three shapes; write everything else exactly as you would without it, in your own structure and words:',
  '- Decisions you need from the user: one heading per question, `### Q1 · <short title>`, one or two lines of context, then each option as `- A · <label> — <its explanation: what it means, its cost or risk>`, the option you recommend marked `(recommandé)`, then one line `Recommandation : B, parce que …`.',
  '- Commit messages: a fenced ```text block starting `type(<change-id>): subject`, a blank line, then the body; never a Co-Authored-By trailer.',
  "- The cockpit block: when a message asks the user to decide, do or check something, end it with a fenced ```cockpit block; the cockpit draws the buttons from it and hides it. One short line per item, a title rather than the instructions (your prose above holds the details): `trancher: <point> → reco: <your recommendation>`, `confirmer: <a decision you took alone>`, `faire: <an action only the user can do now>`, `vérifier: <the name of a check the user runs>`, `info: <what you will do next without them>`. Questions and commit messages stay out of it.",
].join('\n')
