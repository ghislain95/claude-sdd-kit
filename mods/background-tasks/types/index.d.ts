// Self-contained, as a state contract must be: the run and agent types repeat those of hooks/shared/.

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


/** One agent the session started that is still at work: what the agent list says, and what its transcript tells. */
export type SessionAgent = { id: string; type: string; description: string; status: string; startedAt?: number; model?: string; tokens?: number; lastTool?: string }


/** A background shell Claude started (a dev server, a watcher), as the last turn's end reported it. */
export type Service = {
  id: string
  label: string
  command: string
  status: string
  port: number | null
  /** When the cockpit first saw it running: the start, give or take a turn. */
  firstSeenAt: number
}

/** The project's workflow runs and this session's agents, gathered every 30 seconds. */
export type BackgroundSnapshot = { runs: WorkflowRun[]; agents: SessionAgent[]; takenAt: number }

declare module 'claude-code' {
  interface PluginState {
    'background-tasks': {
      snapshot: BackgroundSnapshot | null
      services: Service[]
    }
  }
}
