// Copied from shared/sienne.ts by scripts/sync-shared.sh: edit the original, not this copy.
// Shared by the mods of this repository: the Terre de Sienne theme. Colour tokens for the light and dark
// themes, the colours native elements may use, and the small SVG drawings that give the mods their relief
// and motion. Copied into each mod's hooks/shared/ by scripts/sync-shared.sh: edit it here, then run the script.
//
// Every drawing is a standalone <svg>. With scheme 'auto' (the default) it carries both themes and switches
// with prefers-color-scheme; 'light' or 'dark' pins one, for a surface that does not report the scheme.
// Every animation stops under prefers-reduced-motion.

export type Scheme = 'auto' | 'light' | 'dark'
export type Tone = 'ok' | 'running' | 'warning' | 'danger' | 'accent' | 'muted'
export type TokenName =
  | 'base' | 'halo1' | 'halo2' | 'halo3' | 'text' | 'mute' | 'accent' | 'accent2'
  | 'ok' | 'running' | 'warning' | 'danger' | 'track' | 'shadow' | 'highlight' | 'glass' | 'pill1' | 'pill2'

export const TOKENS: { light: Record<TokenName, string>; dark: Record<TokenName, string> } = {
  light: {
    base: '#f4ece0', halo1: '#eab26a', halo2: '#d98a5c', halo3: '#f0cf9a',
    text: '#3b2617', mute: '#8a6f58', accent: '#b8621f', accent2: '#d98a3d',
    ok: '#5f9a62', running: '#c27a2c', warning: '#c9902a', danger: '#b4473a',
    track: 'rgba(122,72,34,.14)', shadow: 'rgba(110,60,20,.22)', highlight: 'rgba(255,255,255,.9)',
    glass: 'rgba(255,250,242,.78)', pill1: '#fffaf3', pill2: '#f3e4cf',
  },
  dark: {
    base: '#17110d', halo1: '#c8693c', halo2: '#e0a458', halo3: '#7a3b22',
    text: '#f2e7d7', mute: '#a08c77', accent: '#e8ae62', accent2: '#f3c47a',
    ok: '#9fd08a', running: '#f0b866', warning: '#e8c06a', danger: '#e07a68',
    track: 'rgba(255,230,200,.10)', shadow: 'rgba(0,0,0,.55)', highlight: 'rgba(255,255,255,.16)',
    glass: 'rgba(40,29,21,.72)', pill1: '#3b2b1f', pill2: '#22180f',
  },
}

/** The only raw colours a native element may carry: one value each, legible on the light and the dark theme. */
export const NATIVE = {
  accent: '#c0702a',
  accentBorder: 'rgba(192,112,42,.45)',
  accentFill: 'rgba(217,138,61,.12)',
  ok: '#568a52',
  danger: '#c0503f',
} as const

/** The narrowest a full-width drawing (ribbon, timeline) is ever drawn, in CSS pixels. */
export const MIN_WIDTH = 240

const TONE_VAR: Record<Tone, string> = {
  ok: 'var(--ok)', running: 'var(--running)', warning: 'var(--warning)', danger: 'var(--danger)', accent: 'var(--accent)', muted: 'var(--mute)',
}

const FONT = '-apple-system,BlinkMacSystemFont,&quot;SF Pro Text&quot;,Inter,sans-serif'
const EASE = 'cubic-bezier(.23,1,.32,1)'

function vars(scheme: 'light' | 'dark'): string {
  return Object.entries(TOKENS[scheme]).map(([name, value]) => `--${name}:${value}`).join(';')
}

/** The <style> every drawing opens with: the colour variables, the shared animations, reduced motion. */
export function styleSheet(scheme: Scheme = 'auto'): string {
  const colours =
    scheme === 'auto'
      ? `:root{${vars('light')}}@media (prefers-color-scheme: dark){:root{${vars('dark')}}}`
      : `:root{${vars(scheme)}}`
  return (
    `<style>${colours}` +
    `.wave{transform-box:fill-box;transform-origin:center;animation:wave 1.9s ${EASE} infinite}` +
    `@keyframes wave{0%{opacity:.55;transform:scale(1)}80%,100%{opacity:0;transform:scale(1.9)}}` +
    `.fill{animation:fill 1.5s ${EASE} both}@keyframes fill{from{stroke-dashoffset:var(--from)}}` +
    `.grow{transform-box:fill-box;transform-origin:left center;animation:grow 1.2s ${EASE} both}@keyframes grow{from{transform:scaleX(0)}}` +
    `.draw{animation:draw .6s ${EASE} .4s both}@keyframes draw{from{stroke-dashoffset:var(--from)}}` +
    `.glide{animation:slide 1.8s linear infinite}` +
    `@keyframes slide{from{transform:translateX(var(--from-x))}to{transform:translateX(var(--to-x))}}` +
    // What waits for an answer: one sweep, then a rest, for as long as it waits; it catches the eye without tiring it.
    `.shimmer{animation:sweep 5s ${EASE} infinite}` +
    `@keyframes sweep{0%{transform:translateX(var(--from-x))}45%,100%{transform:translateX(var(--to-x))}}` +
    `.calm{animation-duration:3.6s}` +
    `.drift1{animation:drift1 24s ease-in-out infinite alternate}@keyframes drift1{to{transform:translate(220px,140px) scale(1.15)}}` +
    `.drift2{animation:drift2 31s ease-in-out infinite alternate}@keyframes drift2{to{transform:translate(-260px,-120px) scale(.9)}}` +
    `.drift3{animation:drift3 38s ease-in-out infinite alternate}@keyframes drift3{to{transform:translate(160px,-160px)}}` +
    `@media (prefers-reduced-motion: reduce){*{animation:none!important}.motion{display:none}}` +
    `</style>`
  )
}

function open(width: number, height: number, scheme: Scheme, extra = ''): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"${extra}>${styleSheet(scheme)}`
}

function clamp01(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0
}

function safeId(id: string): string {
  return `s-${id.replace(/[^A-Za-z0-9_-]/g, '_')}`
}

export function escapeXml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
}

/** Cuts `text` with an ellipsis so it fits `maxPx` at about `pxPerChar` per character. */
export function fitText(text: string, maxPx: number, pxPerChar = 7): string {
  const max = Math.max(1, Math.floor(maxPx / pxPerChar))
  return text.length <= max ? text : `${text.slice(0, Math.max(1, max - 1)).trimEnd()}…`
}

/** A status dot; a pulsing one sends out a wave; a hollow one is a ring, for a step still ahead. */
export function dot(tone: Tone, o: { pulse?: boolean; hollow?: boolean; size?: number; scheme?: Scheme } = {}): string {
  const size = o.size ?? 12
  const c = size / 2
  const r = size / 4
  if (o.hollow === true) {
    return `${open(size, size, o.scheme ?? 'auto')}<circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke-width="1.5" style="stroke:${TONE_VAR[tone]}"/></svg>`
  }
  const fill = `style="fill:${TONE_VAR[tone]}"`
  const wave = o.pulse === true ? `<circle class="wave motion" cx="${c}" cy="${c}" r="${r}" ${fill}/>` : ''
  return `${open(size, size, o.scheme ?? 'auto')}${wave}<circle cx="${c}" cy="${c}" r="${r}" ${fill}/></svg>`
}

/** A ring filled to `fraction` from twelve o'clock, filling up as it appears; from 48 px, a glass disc under it. */
export function ring(fraction: number, o: { size?: number; tone?: Tone; label?: string; scheme?: Scheme; id?: string } = {}): string {
  const size = o.size ?? 16
  const id = safeId(o.id ?? 'ring')
  const isLarge = size >= 48
  const stroke = isLarge ? Math.round(size / 11) : size >= 24 ? 3 : 2.5
  const c = size / 2
  const r = c - stroke / 2 - (isLarge ? 4 : 0)
  const circumference = 2 * Math.PI * r
  const offset = circumference * (1 - clamp01(fraction))
  const tone = o.tone ?? 'accent'
  const paint = tone === 'accent' ? `url(#${id}-g)` : TONE_VAR[tone]
  const defs =
    `<defs><linearGradient id="${id}-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" style="stop-color:var(--accent2)"/><stop offset="1" style="stop-color:var(--halo1)"/></linearGradient>` +
    (isLarge ? `<filter id="${id}-s" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="2" stdDeviation="2.5" style="flood-color:var(--shadow)"/></filter>` : '') +
    `</defs>`
  const disc = isLarge ? `<circle cx="${c}" cy="${c}" r="${c - 2}" style="fill:var(--glass)" filter="url(#${id}-s)"/>` : ''
  const label =
    o.label !== undefined
      ? `<text x="${c}" y="${c + size * 0.07}" text-anchor="middle" dominant-baseline="middle" font-family="${FONT}" font-size="${Math.round(size * 0.22)}" font-weight="700" style="fill:var(--text)">${escapeXml(o.label)}</text>`
      : ''
  return (
    `${open(size, size, o.scheme ?? 'auto')}${defs}${disc}` +
    `<circle cx="${c}" cy="${c}" r="${r.toFixed(2)}" fill="none" stroke-width="${stroke}" style="stroke:var(--track)"/>` +
    `<circle class="fill" cx="${c}" cy="${c}" r="${r.toFixed(2)}" fill="none" stroke-width="${stroke}" stroke-linecap="round" stroke="${paint}" ` +
    `stroke-dasharray="${circumference.toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}" style="--from:${circumference.toFixed(2)};stroke:${paint}" transform="rotate(-90 ${c} ${c})"/>` +
    `${label}</svg>`
  )
}

/** A bar filled to `fraction`, growing as it appears; a running one carries a light that moves along it. */
export function bar(width: number, fraction: number, o: { running?: boolean; scheme?: Scheme; id?: string } = {}): string {
  const w = Math.max(40, Math.round(width))
  const id = safeId(o.id ?? 'bar')
  const filled = Math.round(w * clamp01(fraction))
  const shimmer =
    o.running === true && filled > 0
      ? `<g clip-path="url(#${id}-c)"><rect class="glide motion" x="0" y="2" width="40" height="6" fill="url(#${id}-l)" style="--from-x:-40px;--to-x:${filled}px"/></g>`
      : ''
  return (
    `${open(w, 10, o.scheme ?? 'auto')}<defs>` +
    `<linearGradient id="${id}-g" x1="0" x2="1"><stop offset="0" style="stop-color:var(--accent)"/><stop offset="1" style="stop-color:var(--accent2)"/></linearGradient>` +
    `<linearGradient id="${id}-l" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>` +
    `<clipPath id="${id}-c"><rect x="0" y="2" width="${filled}" height="6" rx="3"/></clipPath></defs>` +
    `<rect x="0" y="2" width="${w}" height="6" rx="3" style="fill:var(--track)"/>` +
    (filled > 0 ? `<rect class="grow" x="0" y="2" width="${filled}" height="6" rx="3" fill="url(#${id}-g)"/>` : '') +
    `${shimmer}</svg>`
  )
}

export type IconName = 'question' | 'report' | 'qa' | 'commit' | 'check' | 'tool' | 'info' | 'warning' | 'cockpit'

/** Each icon drawn with strokes in an 18 × 18 box. */
const ICON_PATHS: Record<IconName, string> = {
  question: '<circle cx="9" cy="9" r="7"/><path d="M6.8 7a2.3 2.3 0 1 1 3.2 2.1c-.7.3-1 .8-1 1.4"/><path d="M9 13.2v.1"/>',
  report: '<rect x="3.5" y="2.5" width="11" height="13" rx="2"/><path d="M6.5 6.5h5M6.5 9.5h5M6.5 12.5h3"/>',
  qa: '<rect x="3" y="3" width="12" height="12" rx="3"/><path d="M6 9.2l2 2 4-4.4"/>',
  commit: '<circle cx="9" cy="9" r="3.5"/><path d="M1 9h4.5M12.5 9H17"/>',
  check: '<path d="M4 9.5l3.2 3.2L14 5.5"/>',
  tool: '<path d="M11.5 3.2a3.5 3.5 0 0 0-4.3 4.6L3 12l3 3 4.2-4.2a3.5 3.5 0 0 0 4.6-4.3l-2.1 2.1-2-.5-.5-2z"/>',
  info: '<circle cx="9" cy="9" r="7"/><path d="M9 8v4.5M9 5.5v.1"/>',
  warning: '<path d="M9 2.5l7 12.5H2z"/><path d="M9 7.5v3.5M9 13v.1"/>',
  cockpit: '<circle cx="9" cy="9" r="7"/><path d="M9 9l3.5-3.5"/><path d="M4.5 11.5h1.5M12 11.5h1.5"/>',
}

function iconGroup(name: IconName, x: number, y: number, size: number, colour: string, draw: boolean): string {
  const scale = size / 18
  const drawn = draw ? ` class="draw" stroke-dasharray="24" stroke-dashoffset="0" style="--from:24;stroke:${colour}"` : ` style="stroke:${colour}"`
  return `<g transform="translate(${x} ${y}) scale(${scale})" fill="none" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"${drawn}>${ICON_PATHS[name]}</g>`
}

/** A small stroked icon; `draw` traces it as it appears (the commit check). */
export function icon(name: IconName, o: { size?: number; tone?: Tone; draw?: boolean; scheme?: Scheme } = {}): string {
  const size = o.size ?? 16
  return `${open(size, size, o.scheme ?? 'auto')}${iconGroup(name, 0, 0, size, TONE_VAR[o.tone ?? 'accent'], o.draw === true)}</svg>`
}

/**
 * A card's header: badge or icon, title, meta on the right, a gradient that fades to the right (so a width a
 * little short of the slot never shows) and a rule underneath. A waiting one shimmers and its badge sends a wave.
 */
export function ribbon(
  width: number,
  o: {
    id: string
    icon: IconName | { badge: string }
    title: string
    meta?: string
    tone?: Tone
    waiting?: boolean
    done?: boolean
    /** Rounds the top corners, to run parallel to the corners of the card the ribbon heads. */
    radius?: number
    scheme?: Scheme
  },
): string {
  const w = Math.max(MIN_WIDTH, Math.round(width))
  const h = 36
  const id = safeId(o.id)
  const tone = o.tone ?? 'accent'
  const colour = TONE_VAR[tone]
  const top = tone === 'accent' ? 'var(--accent2)' : colour
  const isWaiting = o.waiting === true
  const radius = Math.max(0, Math.min(h / 2, o.radius ?? 0))
  const meta = o.meta !== undefined ? escapeXml(fitText(o.meta, w * 0.25, 6)) : ''
  const titleRoom = w - 46 - (o.meta !== undefined ? Math.min(w * 0.25, o.meta.length * 6) + 16 : 0) - (o.done === true ? 24 : 0)
  const title = escapeXml(fitText(o.title, titleRoom, 7.4))
  const lead =
    typeof o.icon === 'string'
      ? iconGroup(o.icon, 9, 9, 18, colour, false)
      : `<circle cx="18" cy="18" r="10" fill="url(#${id}-b)"/>` +
        (isWaiting
          ? `<circle class="wave calm motion" cx="18" cy="18" r="10" fill="none" style="stroke:${colour}"/>`
          : '') +
        `<text x="18" y="18" text-anchor="middle" dominant-baseline="central" font-family="${FONT}" font-size="9.5" font-weight="800" style="fill:var(--pill1)">${escapeXml(o.icon.badge.slice(0, 3))}</text>`
  const shimmer = isWaiting
    ? `<rect class="shimmer motion" x="0" width="110" height="${h}" fill="url(#${id}-l)" style="--from-x:-110px;--to-x:${w}px"/>`
    : ''
  const check = o.done === true ? iconGroup('check', w - 26, 9, 18, 'var(--ok)', true) : ''
  return (
    `${open(w, h, o.scheme ?? 'auto')}<defs>` +
    `<linearGradient id="${id}-g" x1="0" x2="1"><stop offset="0" style="stop-color:${top}" stop-opacity=".5"/><stop offset=".55" style="stop-color:${colour}" stop-opacity=".14"/><stop offset="1" style="stop-color:${colour}" stop-opacity="0"/></linearGradient>` +
    `<linearGradient id="${id}-l" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".32"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>` +
    `<radialGradient id="${id}-b" cx=".35" cy=".3"><stop offset="0" style="stop-color:${top}"/><stop offset="1" style="stop-color:${colour}"/></radialGradient>` +
    (radius > 0 ? `<clipPath id="${id}-r"><rect width="${w}" height="${h + radius}" rx="${radius}"/></clipPath>` : '') +
    `</defs>` +
    (radius > 0 ? `<g clip-path="url(#${id}-r)">` : '') +
    `<rect width="${w}" height="${h}" fill="url(#${id}-g)"/>${shimmer}` +
    `<rect width="${w}" height="1" style="fill:var(--highlight)"/>` +
    `<rect y="${h - 1}" width="${w}" height="1" style="fill:${colour}" opacity=".45"/>` +
    lead +
    `<text x="36" y="18" dominant-baseline="central" font-family="${FONT}" font-size="12.5" font-weight="650" style="fill:var(--text)">${title}</text>` +
    (meta !== '' ? `<text x="${w - (o.done === true ? 34 : 10)}" y="18" dominant-baseline="central" text-anchor="end" font-family="${FONT}" font-size="10.5" style="fill:var(--mute)">${meta}</text>` : '') +
    `${check}${radius > 0 ? '</g>' : ''}</svg>`
  )
}

/** The phases: done steps filled, the line traced up to the current one, which pulses; the rest hollow. */
export function timeline(width: number, steps: string[], current: number, o: { scheme?: Scheme; id?: string } = {}): string {
  const w = Math.max(MIN_WIDTH, Math.round(width))
  const h = 36
  // Room for half of the first and last labels, so the edges never cut them.
  const pad = Math.max(14, Math.ceil(((steps[0]?.length ?? 0) * 5.6) / 2) + 2, Math.ceil(((steps.at(-1)?.length ?? 0) * 5.6) / 2) + 2)
  const span = steps.length > 1 ? (w - 2 * pad) / (steps.length - 1) : 0
  const xs = steps.map((_, index) => (steps.length > 1 ? pad + index * span : w / 2))
  const isAllDone = current >= steps.length
  const at = isAllDone ? steps.length : Math.max(-1, current)
  const reach = isAllDone ? (xs.at(-1) ?? pad) - pad : at >= 0 ? (xs[at] ?? pad) - pad : 0
  const marks = steps
    .map((step, index) => {
      const x = (xs[index] ?? 0).toFixed(1)
      const isDone = index < at
      const isCurrent = index === at
      const mark = isCurrent
        ? `<circle class="wave motion" cx="${x}" cy="12" r="5" style="fill:var(--accent2)"/><circle cx="${x}" cy="12" r="5" style="fill:var(--accent2)"/>`
        : isDone
          ? `<circle cx="${x}" cy="12" r="5" style="fill:var(--accent)"/>`
          : `<circle cx="${x}" cy="12" r="4.5" fill="none" stroke-width="1.5" style="stroke:var(--mute)"/>`
      const label = escapeXml(fitText(step, Math.max(30, span), 5.6))
      return `${mark}<text x="${x}" y="31" text-anchor="middle" font-family="${FONT}" font-size="9.5" style="fill:${isCurrent ? 'var(--text)' : 'var(--mute)'}">${label}</text>`
    })
    .join('')
  return (
    `${open(w, h, o.scheme ?? 'auto')}` +
    `<line x1="${pad}" y1="12" x2="${w - pad}" y2="12" stroke-width="2" style="stroke:var(--track)"/>` +
    (reach > 0
      ? `<line class="draw" x1="${pad}" y1="12" x2="${(pad + reach).toFixed(1)}" y2="12" stroke-width="2" stroke-dasharray="${reach.toFixed(1)}" stroke-dashoffset="0" style="stroke:var(--accent);--from:${reach.toFixed(1)}"/>`
      : '') +
    `${marks}</svg>`
  )
}

/**
 * Rounded chips, each with a small dot of its tone, wrapping onto a new row past `maxWidth`; measured, so the
 * caller sizes the Svg from `width` and `height`. A `hint` becomes the chip's tooltip where the surface shows one.
 */
export function pills(
  items: { label: string; tone: Tone; hint?: string }[],
  o: { maxWidth?: number; scheme?: Scheme } = {},
): { source: string; width: number; height: number } {
  const row = 22
  const gap = 6
  const maxWidth = Math.max(80, o.maxWidth ?? Number.POSITIVE_INFINITY)
  let x = 0
  let y = 0
  let width = 1
  const chips = items.map(item => {
    const w = Math.min(maxWidth, Math.round(item.label.length * 6.4 + 34))
    if (x > 0 && x + w > maxWidth) {
      x = 0
      y += row + gap
    }
    const colour = TONE_VAR[item.tone]
    const label = escapeXml(fitText(item.label, w - 30, 6.4))
    const chip =
      `<g>${item.hint !== undefined ? `<title>${escapeXml(item.hint)}</title>` : ''}` +
      `<rect x="${x + 0.5}" y="${y + 0.5}" width="${w - 1}" height="${row - 1}" rx="${(row - 1) / 2}" style="fill:${colour};stroke:${colour}" fill-opacity=".12" stroke-opacity=".5"/>` +
      `<circle cx="${x + 12}" cy="${y + row / 2}" r="3.5" style="fill:${colour}"/>` +
      `<text x="${x + 21}" y="${y + row / 2}" dominant-baseline="central" font-family="${FONT}" font-size="11" font-weight="600" style="fill:var(--text)">${label}</text></g>`
    x += w + gap
    width = Math.max(width, x - gap)
    return chip
  })
  const height = y + row
  return { source: `${open(width, height, o.scheme ?? 'auto')}${chips.join('')}</svg>`, width, height }
}

/**
 * A raised pill to lay behind a row: one flat fill, a hairline rim, a soft shadow; nothing more. Centred in its
 * drawing with a 3 px margin all round (room for the shadow). `radius` matches the container it sits in:
 * a pill inside a rounded box takes that box's radius less the gap between them, so the corners run parallel.
 */
export function pill(width: number, height: number, o: { radius?: number; scheme?: Scheme } = {}): string {
  const w = Math.max(40, Math.round(width))
  const h = Math.max(16, Math.round(height))
  const margin = 3
  const r = Math.min(o.radius ?? (h - 2 * margin) / 2, (h - 2 * margin) / 2)
  return (
    `${open(w, h, o.scheme ?? 'auto')}<defs>` +
    `<filter id="s-pill-s" x="-5%" y="-40%" width="110%" height="200%"><feDropShadow dx="0" dy="1" stdDeviation="1.5" style="flood-color:var(--shadow)" flood-opacity=".55"/></filter></defs>` +
    `<rect x="${margin}" y="${margin}" width="${w - 2 * margin}" height="${h - 2 * margin}" rx="${r}" style="fill:var(--pill1);stroke:var(--accent)" stroke-opacity=".22" filter="url(#s-pill-s)"/></svg>`
  )
}

/** The window's backdrop: the base colour, three blurred halos drifting slowly, a light grain. */
export function backdrop(o: { scheme?: Scheme } = {}): string {
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">${styleSheet(o.scheme ?? 'auto')}` +
    `<defs><filter id="s-bd-blur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="90"/></filter>` +
    `<filter id="s-bd-grain"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" stitchTiles="stitch"/>` +
    `<feColorMatrix values="0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 .09 0"/></filter></defs>` +
    `<rect width="1600" height="1000" style="fill:var(--base)"/>` +
    `<g filter="url(#s-bd-blur)" opacity=".6">` +
    `<circle class="drift1" cx="250" cy="150" r="320" style="fill:var(--halo1)"/>` +
    `<circle class="drift2" cx="1350" cy="850" r="380" style="fill:var(--halo2)"/>` +
    `<circle class="drift3" cx="800" cy="520" r="240" style="fill:var(--halo3)"/></g>` +
    `<rect width="1600" height="1000" filter="url(#s-bd-grain)"/></svg>`
  )
}

/** The WCAG contrast ratio of two #rrggbb colours. */
export function contrast(fg: string, bg: string): number {
  const luminance = (hex: string): number => {
    const value = hex.replace('#', '')
    const channels = [0, 2, 4].map(at => parseInt(value.slice(at, at + 2), 16) / 255)
    const [r = 0, g = 0, b = 0] = channels.map(c => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b
  }
  const [light = 0, dark = 0] = [luminance(fg), luminance(bg)].sort((a, b) => b - a)
  return (light + 0.05) / (dark + 0.05)
}
