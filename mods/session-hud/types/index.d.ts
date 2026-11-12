/** One task still in flight at the last turn's end, as the band's list shows it. */
export type BackgroundItem = { id: string; kind: 'service' | 'workflow' | 'agent' | 'monitor' | 'other'; label: string; port: number | null; command: string | null }

/** What the band shows, gathered every 30 seconds and at each turn's end. */
export type HudFigures = {
  startedAt: number
  contextPercent: number | null
  contextTokens: number | null
  contextWindow: number | null
  costUsd: number | null
  /** The most used rate limit, when the plan has one. */
  rateLimit: { kind: string; percent: number; resetsAt: string | null } | null
  model: string | null
  toolCalls: number
  toolErrors: number
  /** Tasks in flight at the last turn's end: services, workflows, agents, monitors. */
  tasks: BackgroundItem[]
}

declare module 'claude-code' {
  interface PluginState {
    'session-hud': {
      figures: HudFigures | null
      /** The list of background tasks is unfolded above the band. */
      isListOpen: boolean
    }
  }
}
