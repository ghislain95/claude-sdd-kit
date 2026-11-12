/** How long a tool call took, and whether it failed: its row's tail. */
export type ToolTiming = { durationMs: number; isError: boolean }

/** The two switches of the mod: the cards themselves, and the display contract added to the system prompt. */
export type CardToggles = { cards: boolean; contract: boolean }

/** What the cards know of the project, collected every 30 seconds and at each turn's end. */
export type CardFacts = { changeNames: string[]; recentCommits: { hash: string; subject: string }[] }

declare module 'claude-code' {
  interface PluginState {
    'conversation-cards': {
      toggles: CardToggles
      projectRoot: string | null
      cardFacts: CardFacts
      /** The context's fill, for the spinner; null until read. */
      contextPercent: number | null
      toolTimes: StateFamily<ToolTiming | null>
      isToolOpen: StateFamily<boolean>
      isMessageOpen: StateFamily<boolean>
      qaMarks: StateFamily<Record<string, string>>
      reportOpen: StateFamily<Record<string, boolean>>
      briefs: StateFamily<string | null>
      /** Claude's replies the person has answered since (sent anything after): their cards rest, only the latest moves. */
      settled: string[]
    }
  }
}
