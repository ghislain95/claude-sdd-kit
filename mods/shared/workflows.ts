// Shared by the mods of this repository: background workflow runs, read from Claude's own files.
// Pure: parsing and ordering. The reading of files is in collect-workflows.ts.

import { DAY, HOUR, MINUTE, cleanMarkdown, formatAgo, formatDuration, formatTokens, modelLabel, plural, truncate } from './format'

export type Severities = { blocking: number; major: number; minor: number }

export type RunAgent = {
  /** The agent id: its files are `agent-<id>.*`. Two agents may share a label (a verify loop), never an id. */
  id: string
  label: string
  type?: string
  phase?: string
  state: 'running' | 'done' | 'waiting'
  startedAt?: number
  lastActivityAt?: number
  lastTool?: string
  /** The model of its last turn (`claude-opus-5-5`). */
  model?: string
  /** Its context at the last turn: input, cache and output tokens, as Claude Code's task list counts them. */
  tokens?: number
}

export type PhaseCount = { started: number; done: number }

export type WorkflowRun = {
  id: string
  sessionId: string
  sessionTitle?: string
  status: 'running' | 'silent' | 'completed' | 'failed'
  name?: string
  label?: string
  phase?: string
  agentsStarted: number
  agentsDone: number
  startedAt?: number
  finishedAt?: number
  durationMs?: number
  lastActivityAt?: number
  phases?: string[]
  /** The script's one-line purpose (`meta.description`). */
  description?: string
  /** Each phase's `detail` from the script's meta, by phase title. */
  phaseDetails?: Record<string, string>
  /** Agents started and done per phase, over the whole journal. */
  phaseCounts?: Record<string, PhaseCount>
  agents?: RunAgent[]
  findings?: Severities
  tests?: string
  openQuestions?: number
}

/** A run whose folder has not moved for this long is shown as silent, not running. */
/** A finished run is announced by a toast only within this window after it ends. */
export const ANNOUNCE_WITHIN_MS = 15 * 60 * 1000

export const SILENT_AFTER_MS = 20 * 60 * 1000

export type JournalFacts = {
  started: number
  done: number
  lastLabel?: string
  lastPhase?: string
}

export function parseJournal(text: string): JournalFacts {
  const facts: JournalFacts = { started: 0, done: 0 }
  for (const line of text.split('\n')) {
    if (line.trim() === '') continue
    let entry: { type?: string; label?: string; phase?: string }
    try {
      entry = JSON.parse(line)
    } catch {
      continue
    }
    if (entry.type === 'started') {
      facts.started += 1
      if (entry.label !== undefined) facts.lastLabel = entry.label
      if (entry.phase !== undefined) facts.lastPhase = entry.phase
    } else if (entry.type === 'result') {
      facts.done += 1
    }
  }
  return facts
}

export function finishedRun(sessionId: string, state: Record<string, unknown>): WorkflowRun | null {
  const id = typeof state.runId === 'string' ? state.runId : undefined
  if (id === undefined) return null
  const finishedAt = typeof state.timestamp === 'string' ? Date.parse(state.timestamp) : undefined
  const durationMs = typeof state.durationMs === 'number' ? state.durationMs : undefined
  const agentCount = typeof state.agentCount === 'number' ? state.agentCount : 0
  return {
    id,
    sessionId,
    status: state.status === 'completed' ? 'completed' : 'failed',
    name: typeof state.workflowName === 'string' ? state.workflowName : undefined,
    agentsStarted: agentCount,
    agentsDone: agentCount,
    startedAt: typeof state.startTime === 'number' ? state.startTime : undefined,
    finishedAt: Number.isNaN(finishedAt) ? undefined : finishedAt,
    durationMs,
  }
}

export function liveRun(input: {
  id: string
  sessionId: string
  journal: JournalFacts
  startedAt: number | undefined
  lastActivityAt: number
  now: number
}): WorkflowRun {
  const { id, sessionId, journal, startedAt, lastActivityAt, now } = input
  return {
    id,
    sessionId,
    status: now - lastActivityAt > SILENT_AFTER_MS ? 'silent' : 'running',
    label: journal.lastLabel,
    phase: journal.lastPhase,
    agentsStarted: journal.started,
    agentsDone: journal.done,
    startedAt,
    lastActivityAt,
  }
}

/** Running first, then silent (a day at most), then finished, newest first. */
export function orderRuns(runs: WorkflowRun[], now: number, limit: number): WorkflowRun[] {
  const rank = (run: WorkflowRun) => (run.status === 'running' ? 0 : run.status === 'silent' ? 1 : 2)
  const when = (run: WorkflowRun) => run.finishedAt ?? run.lastActivityAt ?? run.startedAt ?? 0
  return runs
    .filter(run => run.status !== 'silent' || now - (run.lastActivityAt ?? 0) < DAY)
    .sort((a, b) => rank(a) - rank(b) || when(b) - when(a))
    .slice(0, limit)
}

export function runName(run: WorkflowRun): string {
  if (run.name !== undefined) return run.name
  if (run.label !== undefined && run.phase !== undefined) return `${run.label} · ${run.phase}`
  return run.label ?? run.id
}

export type PhaseState = 'done' | 'skipped' | 'running' | 'upcoming'

export type PhaseRow = { title: string; detail?: string; state: PhaseState; started: number; done: number }

/** The run's phases in script order: done, skipped, running (agents at work, or the furthest phase reached) or upcoming. */
export function phaseRows(run: WorkflowRun): PhaseRow[] {
  const phases = run.phases ?? []
  const counts = run.phaseCounts ?? {}
  const working = new Set((run.agents ?? []).filter(agent => agent.state === 'running').map(agent => agent.phase))
  const isReached = (title: string) => (counts[title]?.started ?? 0) > 0 || working.has(title) || title === run.phase
  const furthest = phases.reduce((last, title, index) => (isReached(title) ? index : last), -1)
  return phases.map((title, index) => {
    const count = counts[title] ?? { started: 0, done: 0 }
    const isWorking = working.has(title) || count.started > count.done
    const state: PhaseState =
      isWorking || index === furthest ? 'running' : index > furthest ? 'upcoming' : count.started > 0 ? 'done' : 'skipped'
    return { title, detail: run.phaseDetails?.[title], state, started: count.started, done: count.done }
  })
}

/** What an agent row says under its name: model, tokens, and the tool it is in while it runs. */
export function agentFiguresLine(agent: { model?: string; tokens?: number; lastTool?: string }): string {
  return [
    agent.model !== undefined ? modelLabel(agent.model) : null,
    agent.tokens !== undefined ? `${formatTokens(agent.tokens)} tokens` : null,
    agent.lastTool ?? null,
  ]
    .filter((part): part is string => part !== null)
    .join(' · ')
}

/** The phases on one line, for the text pane: ✓ done, – skipped, ▶ running, ○ upcoming. */
export function phasesLine(rows: PhaseRow[]): string {
  const marks: Record<PhaseState, string> = { done: '✓', skipped: '–', running: '▶', upcoming: '○' }
  return rows.map(row => `${marks[row.state]} ${row.title}`).join(' · ')
}

export function runLine(run: WorkflowRun, now: number): string {
  if (run.status === 'running' || run.status === 'silent') {
    const elapsed = run.startedAt !== undefined ? ` · ${formatDuration(now - run.startedAt)}` : ''
    const agents = ` · ${run.agentsDone}/${plural(run.agentsStarted, 'agent', 'agents')}`
    const quiet =
      run.status === 'silent' && run.lastActivityAt !== undefined
        ? ` · muet depuis ${formatDuration(now - run.lastActivityAt)}`
        : ''
    return `${run.status === 'running' ? '▶' : '⏸'} ${runName(run)}${agents}${elapsed}${quiet}`
  }
  const mark = run.status === 'completed' ? '✓' : '✗'
  const duration = run.durationMs !== undefined ? ` · ${formatDuration(run.durationMs)}` : ''
  const ago = run.finishedAt !== undefined ? ` · ${formatAgo(now - run.finishedAt)}` : ''
  return `${mark} ${runName(run)} · ${plural(run.agentsStarted, 'agent', 'agents')}${duration}${ago}`
}

export function runsToAnnounce(runs: WorkflowRun[], announced: readonly string[], now: number): WorkflowRun[] {
  return runs.filter(
    run =>
      (run.status === 'completed' || run.status === 'failed') &&
      run.finishedAt !== undefined &&
      now - run.finishedAt < ANNOUNCE_WITHIN_MS &&
      !announced.includes(run.id),
  )
}

export function announcement(run: WorkflowRun): string {
  const mark = run.status === 'completed' ? '✅' : '❌'
  const verb = run.status === 'completed' ? 'terminé' : 'en échec'
  const duration = run.durationMs !== undefined ? `, ${formatDuration(run.durationMs)}` : ''
  return `${mark} Workflow « ${runName(run)} » ${verb} — ${plural(run.agentsStarted, 'agent', 'agents')}${duration}`
}

export function emptySeverities(): Severities {
  return { blocking: 0, major: 0, minor: 0 }
}

export function severityOf(label: string): keyof Severities | null {
  const upper = label.toUpperCase()
  if (/BLOQUANT|BLOCKING|BLOCKER/.test(upper)) return 'blocking'
  if (/MAJEUR|MAJOR/.test(upper)) return 'major'
  if (/MINEUR|MINOR/.test(upper)) return 'minor'
  return null
}

/** Counts every `{ severity }` object found anywhere in a result. */
export function countFindings(value: unknown, into: Severities = emptySeverities()): Severities {
  if (Array.isArray(value)) {
    for (const item of value) countFindings(item, into)
  } else if (value !== null && typeof value === 'object') {
    const record = value as Record<string, unknown>
    if (typeof record.severity === 'string') {
      const severity = severityOf(record.severity)
      if (severity !== null) into[severity] += 1
    }
    for (const [key, child] of Object.entries(record)) {
      if (key !== 'severity') countFindings(child, into)
    }
  }
  return into
}

/** The last full-suite line a result reports (`fullSuite`, `fullVitest`, …). */
export function suiteLine(value: unknown): string | undefined {
  let found: string | undefined
  const visit = (node: unknown) => {
    if (Array.isArray(node)) node.forEach(visit)
    else if (node !== null && typeof node === 'object') {
      for (const [key, child] of Object.entries(node as Record<string, unknown>)) {
        if (/^full[A-Z]/.test(key) && typeof child === 'string') found = child
        else visit(child)
      }
    }
  }
  visit(value)
  return found
}

export type ScriptMeta = { name?: string; description?: string; phases: string[]; phaseDetails: Record<string, string> }

/** A quoted string property of an object literal's source, any of the three quotes. */
function quotedProperty(source: string, key: string): string | undefined {
  return new RegExp(`\\b${key}:\\s*(['"\`])((?:(?!\\1)[^\\\\]|\\\\.)*)\\1`).exec(source)?.[2]
}

/** The workflow script's `meta`: name, description, phase titles in order and each phase's detail. */
export function scriptMeta(source: string): ScriptMeta {
  const meta = /export\s+const\s+meta\s*=\s*\{([\s\S]*?)\n\}/.exec(source)?.[1] ?? source.slice(0, 4000)
  const phasesBlock = /phases:\s*\[([\s\S]*?)\]/.exec(meta)?.[1] ?? ''
  const head = meta.replace(phasesBlock, '')
  const phases: string[] = []
  const phaseDetails: Record<string, string> = {}
  for (const match of phasesBlock.matchAll(/\{([^{}]*)\}/g)) {
    const title = quotedProperty(match[1] ?? '', 'title')
    if (title === undefined || title === '') continue
    phases.push(title)
    const detail = quotedProperty(match[1] ?? '', 'detail')
    if (detail !== undefined && detail !== '') phaseDetails[title] = detail
  }
  return { name: quotedProperty(head, 'name'), description: quotedProperty(head, 'description'), phases, phaseDetails }
}

export type JournalDetail = {
  agents: RunAgent[]
  /** Agents started and done per phase, every agent counted. */
  phaseCounts: Record<string, PhaseCount>
  findings: Severities
  tests?: string
  openQuestions: number
}

/** Agents (from `started`/`result` entries), findings and the last suite line of a journal. */
export function journalDetail(text: string): JournalDetail {
  const agents = new Map<string, RunAgent>()
  const findings = emptySeverities()
  let tests: string | undefined
  let openQuestions = 0
  for (const line of text.split('\n')) {
    if (line.trim() === '') continue
    let entry: { type?: string; agentId?: string; label?: string; phase?: string; result?: unknown }
    try {
      entry = JSON.parse(line)
    } catch {
      continue
    }
    const id = entry.agentId
    if (id === undefined) continue
    if (entry.type === 'started') {
      agents.set(id, { id, label: entry.label ?? id, phase: entry.phase, state: 'running' })
    } else if (entry.type === 'result') {
      const agent = agents.get(id)
      if (agent !== undefined) agent.state = 'done'
      countFindings(entry.result, findings)
      tests = suiteLine(entry.result) ?? tests
      const questions = (entry.result as { openQuestions?: unknown } | undefined)?.openQuestions
      if (Array.isArray(questions)) openQuestions += questions.length
    }
  }
  const phaseCounts: Record<string, PhaseCount> = {}
  for (const agent of agents.values()) {
    if (agent.phase === undefined) continue
    const count = (phaseCounts[agent.phase] ??= { started: 0, done: 0 })
    count.started += 1
    if (agent.state === 'done') count.done += 1
  }
  return { agents: [...agents.values()], phaseCounts, findings, tests, openQuestions }
}

export type TranscriptFacts = { model?: string; tokens?: number; lastTool?: string }

/** From the end of an agent's transcript: the model and context of its last turn, and the last tool it called. */
export function transcriptFacts(tail: string): TranscriptFacts {
  const model = [...tail.matchAll(/"message":\{"model":"([^"]+)"/g)].at(-1)?.[1]
  const usageAt = tail.lastIndexOf('"usage":{')
  let tokens: number | undefined
  if (usageAt >= 0) {
    const usage = tail.slice(usageAt, usageAt + 1200)
    const field = (name: string) => Number(new RegExp(`"${name}":(\\d+)`).exec(usage)?.[1] ?? 0)
    tokens = field('input_tokens') + field('cache_creation_input_tokens') + field('cache_read_input_tokens') + field('output_tokens')
  }
  const lastTool = [...tail.matchAll(/"type":"tool_use","id":"[^"]+","name":"([^"]+)"/g)].at(-1)?.[1]
  return { model, tokens, lastTool }
}
