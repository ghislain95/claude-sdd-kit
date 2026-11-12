// Copied from shared/collect-workflows.ts by scripts/sync-shared.sh: edit the original, not this copy.
// Shared by the mods of this repository: reading the workflow runs and agents from Claude's own files
// (~/.claude/projects/<project>/<session>/…), read-only, with caches for what no longer changes.

import type { EngineInterface } from 'claude-code'

import { DAY } from './format'
import {
  type RunAgent,
  type ScriptMeta,
  type TranscriptFacts,
  type WorkflowRun,
  countFindings,
  finishedRun,
  journalDetail,
  liveRun,
  orderRuns,
  parseJournal,
  scriptMeta,
  suiteLine,
  transcriptFacts,
} from './workflows'

/** Finished runs never change: their parsed state is kept by path and mtime. */
/** Finished runs never change: their parsed state is kept by path and mtime. */
const finishedCache = new Map<string, { mtimeMs: number; run: WorkflowRun | null }>()

/** How much of an agent's transcript is read from its end: enough to hold its last turn past a long tool result. */
const TAIL_BYTES = 262144

/** Transcript facts by path, kept while the file is unchanged: a finished agent's transcript is read once. */
const transcriptCache = new Map<string, { mtimeMs: number; facts: TranscriptFacts }>()

type AgentFigures = TranscriptFacts & { type?: string; startedAt?: number; lastActivityAt?: number }

/** The agent whose files `agent-<id>.*` sit in `dir`: type, start, last activity, model, context tokens, last tool. */
async function agentFigures($: EngineInterface, dir: string, id: string, mtimes: Map<string, number>): Promise<AgentFigures> {
  const startedAt = mtimes.get(`agent-${id}.meta.json`)
  const lastActivityAt = mtimes.get(`agent-${id}.jsonl`)
  let type: string | undefined
  if (startedAt !== undefined) {
    try {
      type = (JSON.parse((await readText($, `${dir}/agent-${id}.meta.json`)) ?? '{}') as { agentType?: string }).agentType
    } catch {
      type = undefined
    }
  }
  if (lastActivityAt === undefined) return { type, startedAt }
  const path = `${dir}/agent-${id}.jsonl`
  const cached = transcriptCache.get(path)
  if (cached !== undefined && cached.mtimeMs === lastActivityAt) return { type, startedAt, lastActivityAt, ...cached.facts }
  const fresh = transcriptFacts((await run($, ['/usr/bin/tail', '-c', String(TAIL_BYTES), path], dir)) ?? '')
  // A tail that ends inside a long tool result holds no turn: the last known figures stand.
  const facts: TranscriptFacts = {
    model: fresh.model ?? cached?.facts.model,
    tokens: fresh.tokens ?? cached?.facts.tokens,
    lastTool: fresh.lastTool ?? cached?.facts.lastTool,
  }
  transcriptCache.delete(path)
  transcriptCache.set(path, { mtimeMs: lastActivityAt, facts })
  const oldest = transcriptCache.keys().next().value
  if (transcriptCache.size > 300 && oldest !== undefined) transcriptCache.delete(oldest)
  return { type, startedAt, lastActivityAt, ...facts }
}

async function fileMtimes($: EngineInterface, dir: string): Promise<Map<string, number>> {
  const entries = await $.fs.list(dir).catch(() => [])
  return new Map(entries.map(entry => [entry.name, entry.mtimeMs] as const))
}

async function run($: EngineInterface, argv: string[], cwd: string): Promise<string | undefined> {
  try {
    const result = await $.process.run(argv, { cwd, timeoutMs: 10000 })
    return result.exitCode === 0 ? result.stdout : undefined
  } catch {
    return undefined
  }
}

async function mtimeOf($: EngineInterface, path: string): Promise<number | undefined> {
  try {
    return (await $.fs.stat(path)).mtimeMs
  } catch {
    return undefined
  }
}

async function readText($: EngineInterface, path: string): Promise<string | undefined> {
  try {
    return (await $.fs.read(path)) as string
  } catch {
    return undefined
  }
}

async function sessionTitle($: EngineInterface, sessionDir: string): Promise<string | undefined> {
  const text = await readText($, `${sessionDir}/custom-title.json`)
  if (text === undefined) return undefined
  try {
    const title = (JSON.parse(text) as { customTitle?: unknown }).customTitle
    return typeof title === 'string' ? title : undefined
  } catch {
    return undefined
  }
}

export function projectSlug(path: string): string {
  return path.replace(/[^a-zA-Z0-9]/g, '-')
}

/** The project's workflow runs of the last three days, running ones first: every session of the project, not only this one. */
export async function collectWorkflows($: EngineInterface, context: { root: string; home: string }, now: number): Promise<WorkflowRun[]> {
  const projectDir = `${context.home}/.claude/projects/${projectSlug(context.root)}`
  const found = await run(
    $,
    [
      '/usr/bin/find',
      projectDir,
      '-maxdepth',
      '5',
      '(',
      '-path',
      '*/subagents/workflows/wf_*/journal.jsonl',
      '-o',
      '-path',
      '*/workflows/wf_*.json',
      ')',
      '-mtime',
      '-3',
    ],
    context.root,
  )
  const paths = (found ?? '').split('\n').filter(path => path.length > 0)
  const finishedIds = new Set<string>()
  const runs: WorkflowRun[] = []
  const titles = new Map<string, string | undefined>()
  const titleOf = async (sessionDir: string) => {
    if (!titles.has(sessionDir)) titles.set(sessionDir, await sessionTitle($, sessionDir))
    return titles.get(sessionDir)
  }

  for (const path of paths.filter(path => path.endsWith('.json'))) {
    const parts = path.split('/')
    const sessionDir = parts.slice(0, -2).join('/')
    const sessionId = parts[parts.length - 3] ?? ''
    const mtimeMs = (await mtimeOf($, path)) ?? 0
    let cached = finishedCache.get(path)
    if (cached === undefined || cached.mtimeMs !== mtimeMs) {
      const text = await readText($, path)
      let parsed: WorkflowRun | null = null
      try {
        const state = text === undefined ? null : (JSON.parse(text) as Record<string, unknown>)
        const base = state === null ? null : finishedRun(sessionId, state)
        parsed =
          base === null || state === null
            ? null
            : {
                ...base,
                phases: Array.isArray(state.phases)
                  ? state.phases.map(phase => String((phase as { title?: unknown }).title ?? '')).filter(title => title !== '')
                  : undefined,
                findings: countFindings(state.result),
                tests: suiteLine(state.result),
                openQuestions: countOpenQuestions(state.result),
              }
      } catch {
        parsed = null
      }
      cached = { mtimeMs, run: parsed }
      finishedCache.set(path, cached)
    }
    if (cached.run === null) continue
    finishedIds.add(cached.run.id)
    runs.push({ ...cached.run, sessionTitle: await titleOf(sessionDir) })
  }

  for (const path of paths.filter(path => path.endsWith('journal.jsonl'))) {
    const parts = path.split('/')
    const id = parts[parts.length - 2] ?? ''
    if (finishedIds.has(id)) continue
    const runDir = parts.slice(0, -1).join('/')
    const sessionDir = parts.slice(0, -4).join('/')
    const sessionId = parts[parts.length - 5] ?? ''
    const [journalText, entries] = await Promise.all([
      readText($, path),
      $.fs.list(runDir).catch(() => []),
    ])
    const metas = entries.filter(entry => entry.name.endsWith('.meta.json')).map(entry => entry.mtimeMs)
    const base = liveRun({
      id,
      sessionId,
      journal: parseJournal(journalText ?? ''),
      startedAt: metas.length > 0 ? Math.min(...metas) : undefined,
      lastActivityAt: Math.max(0, ...entries.map(entry => entry.mtimeMs)),
      now,
    })
    const detail = journalDetail(journalText ?? '')
    const script = await runScript($, sessionDir, id)
    const agents = await describeAgents($, runDir, entries, detail.agents, base.status === 'running')
    runs.push({
      ...base,
      name: script.name,
      description: script.description,
      phases: script.phases.length > 0 ? script.phases : undefined,
      phaseDetails: script.phaseDetails,
      phaseCounts: detail.phaseCounts,
      agents,
      findings: detail.findings,
      tests: detail.tests,
      openQuestions: detail.openQuestions,
      sessionTitle: await titleOf(sessionDir),
    })
  }
  return orderRuns(runs, now, 8)
}

const LIVE_AGENT_STATUSES = new Set(['pending', 'running', 'waiting'])

function countOpenQuestions(value: unknown): number {
  let count = 0
  const visit = (node: unknown) => {
    if (Array.isArray(node)) node.forEach(visit)
    else if (node !== null && typeof node === 'object') {
      for (const [key, child] of Object.entries(node as Record<string, unknown>)) {
        if (key === 'openQuestions' && Array.isArray(child)) count += child.length
        else visit(child)
      }
    }
  }
  visit(value)
  return count
}

/** The workflow's script, saved beside the session as `<name>-<runId>.js`: its meta. */
async function runScript($: EngineInterface, sessionDir: string, runId: string): Promise<ScriptMeta> {
  const none: ScriptMeta = { phases: [], phaseDetails: {} }
  const scripts = await $.fs.list(`${sessionDir}/workflows/scripts`).catch(() => [])
  const file = scripts.find(entry => entry.name.endsWith(`-${runId}.js`))
  if (file === undefined) return none
  const source = await readText($, `${sessionDir}/workflows/scripts/${file.name}`)
  return source === undefined ? none : scriptMeta(source)
}

/** Agent rows, each matched to its own files by id: type, start, activity, model, tokens; the last tool while it runs. */
async function describeAgents(
  $: EngineInterface,
  runDir: string,
  entries: { name: string; mtimeMs: number }[],
  agents: RunAgent[],
  isRunning: boolean,
): Promise<RunAgent[]> {
  const mtimes = new Map(entries.map(entry => [entry.name, entry.mtimeMs] as const))
  return Promise.all(
    agents.slice(-80).map(async agent => {
      const figures = await agentFigures($, runDir, agent.id, mtimes)
      return {
        ...agent,
        type: figures.type,
        startedAt: figures.startedAt,
        lastActivityAt: figures.lastActivityAt,
        model: figures.model,
        tokens: figures.tokens,
        lastTool: isRunning && agent.state === 'running' ? figures.lastTool : undefined,
      }
    }),
  )
}


/** One agent the session started that is still at work: what the agent list says, and what its transcript tells. */
export type SessionAgent = { id: string; type: string; description: string; status: string; startedAt?: number; model?: string; tokens?: number; lastTool?: string }

/** The agents this session started and that are still at work, with their model, tokens and last tool. */
export async function collectSessionAgents($: EngineInterface, context: { root: string; home: string }): Promise<SessionAgent[]> {
  const agents = await $.agent.list().catch(() => [])
  const live = agents.filter(agent => LIVE_AGENT_STATUSES.has(agent.status))
  if (live.length === 0) return []
  const sessionId = await $.session.id().catch(() => undefined)
  const dir = sessionId !== undefined ? `${context.home}/.claude/projects/${projectSlug(context.root)}/${sessionId}/subagents` : undefined
  const mtimes = dir !== undefined ? await fileMtimes($, dir) : new Map<string, number>()
  return Promise.all(
    live.map(async agent => {
      const figures = dir !== undefined ? await agentFigures($, dir, agent.id, mtimes) : {}
      return {
        id: agent.id,
        type: agent.type,
        description: agent.description,
        status: agent.status,
        startedAt: figures.startedAt,
        model: figures.model,
        tokens: figures.tokens,
        lastTool: figures.lastTool,
      }
    }),
  )
}
