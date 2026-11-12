// Copied from shared/tasks.ts by scripts/sync-shared.sh: edit the original, not this copy.
// Shared by the mods of this repository: the tasks a turn's end reports in flight (background shells,
// workflows, agents, monitors), read the same way by the band and the pane.

/** One in-flight task as a turn's end reports it (`background_tasks` of the Stop event). */
export type InFlightTask = { id: string; type: string; status: string; description: string; command?: string; name?: string; agent_type?: string }

export type TaskKind = 'service' | 'workflow' | 'agent' | 'monitor' | 'other'

const FINISHED = /completed|failed|killed|stopped|cancel/i

export function isInFlight(task: InFlightTask): boolean {
  return !FINISHED.test(task.status)
}

/** The port a command listens on, when it says so: `--port 5173`, `-p 8080`, `PORT=3000`, `localhost:4443`. */
export function portOf(command: string): number | null {
  const match = /(?:--port[ =]|-p\s+|PORT=|localhost:|127\.0\.0\.1:)(\d{2,5})\b/.exec(command)
  return match === null ? null : Number(match[1])
}

export function taskKind(type: string): TaskKind {
  if (type === 'shell') return 'service'
  if (type === 'workflow') return 'workflow'
  if (type === 'subagent' || type === 'agent') return 'agent'
  if (type === 'monitor') return 'monitor'
  return 'other'
}

/** What a task is called: a workflow's name, a shell's description or command, an agent's description. */
export function taskLabel(task: InFlightTask): string {
  const description = task.description.trim()
  if (task.type === 'workflow') return task.name ?? (description || 'workflow')
  if (task.type === 'shell') return description || (task.command ?? 'commande')
  return description || task.agent_type || task.type
}

export const KIND_LABEL: Record<TaskKind, string> = { service: 'service', workflow: 'workflow', agent: 'agent', monitor: 'surveillance', other: 'tâche' }
