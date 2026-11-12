// Copied from shared/services.ts by scripts/sync-shared.sh: edit the original, not this copy.
// Shared by the mods of this repository: the services Claude left running in the background (dev servers,
// watchers), from the in-flight tasks a turn's end reports. Copied into each mod's hooks/shared/ by
// scripts/sync-shared.sh: edit it here, then run the script.

import { type InFlightTask, isInFlight, portOf, taskLabel } from './tasks'

export { portOf } from './tasks'

/** A background shell Claude started (a dev server, a watcher), as the last turn's end reported it. */
export type Service = {
  id: string
  label: string
  command: string
  status: string
  port: number | null
  /** When it was first seen running: the start, give or take a turn. */
  firstSeenAt: number
}

/**
 * The services after a turn's end: the background shells still in flight, each keeping the time it was first seen;
 * a shell no longer reported has stopped, and leaves the list.
 */
export function mergeServices(previous: readonly Service[], tasks: readonly InFlightTask[], now: number): Service[] {
  return tasks
    .filter(task => task.type === 'shell' && isInFlight(task))
    .map(task => {
      const known = previous.find(service => service.id === task.id)
      const command = task.command ?? ''
      return {
        id: task.id,
        label: taskLabel(task),
        command,
        status: task.status,
        port: portOf(command),
        firstSeenAt: known?.firstSeenAt ?? now,
      }
    })
}
