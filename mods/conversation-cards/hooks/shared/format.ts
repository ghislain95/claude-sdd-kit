// Copied from shared/format.ts by scripts/sync-shared.sh: edit the original, not this copy.
// Shared by the mods of this repository: French formatting. Copied into each mod's hooks/shared/ by scripts/sync-shared.sh.

export const MINUTE = 60 * 1000
export const HOUR = 60 * MINUTE
export const DAY = 24 * HOUR

export function cleanMarkdown(text: string): string {
  return text
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()
}

export function plural(count: number, singular: string, pluralForm: string): string {
  return `${count} ${count === 1 ? singular : pluralForm}`
}

export function truncate(text: string, max: number): string {
  return text.length <= max ? text : text.slice(0, Math.max(1, max - 1)).trimEnd() + '…'
}

/** `claude-opus-5-5` → « Opus 5.5 », `claude-3-5-sonnet-20241022` → « Sonnet 3.5 »; an unknown id as it is. */
export function modelLabel(model: string): string {
  const id = model.replace(/\[.*\]$/, '').replace(/-\d{8}$/, '')
  const family = /(opus|sonnet|haiku|fable)/.exec(id)?.[1]
  if (family === undefined) return id
  const version = (id.replace(family, '').match(/\d+/g) ?? []).slice(0, 2).join('.')
  return `${family.charAt(0).toUpperCase()}${family.slice(1)}${version === '' ? '' : ` ${version}`}`
}

/** 443 491 → « 443,5 k », 1 234 567 → « 1,2 M ». */
export function formatTokens(count: number): string {
  if (count < 1000) return String(count)
  if (count < 1000000) return `${(count / 1000).toFixed(1).replace('.', ',')} k`
  return `${(count / 1000000).toFixed(1).replace('.', ',')} M`
}

export function formatDuration(ms: number): string {
  const safe = Math.max(0, ms)
  if (safe < MINUTE) return `${Math.round(safe / 1000)} s`
  if (safe < HOUR) return `${Math.round(safe / MINUTE)} min`
  if (safe < DAY) {
    const totalMinutes = Math.round(safe / MINUTE)
    const hours = Math.floor(totalMinutes / 60)
    const minutes = totalMinutes % 60
    if (hours === 24) return '1 j'
    return minutes === 0 ? `${hours} h` : `${hours} h ${String(minutes).padStart(2, '0')}`
  }
  return `${Math.round(safe / DAY)} j`
}

export function formatAgo(ms: number): string {
  if (ms < MINUTE) return "à l'instant"
  return `il y a ${formatDuration(ms)}`
}

export function percent(done: number, total: number): number {
  return total <= 0 ? 0 : Math.round((done / total) * 100)
}
