import { describe, expect, test } from 'claude-code/testing'

import { NATIVE, backdrop, bar, contrast, dot, pill, pills, ring, ribbon, timeline } from './shared/sienne'

const ids = (svg: string): string[] => [...svg.matchAll(/\bid="([^"]+)"/g)].map(match => match[1] ?? '')

describe('the Terre de Sienne palette', () => {
  test('every native colour stays legible on both bases', () => {
    for (const colour of [NATIVE.accent, NATIVE.ok, NATIVE.danger]) {
      expect(contrast(colour, '#f4ece0')).toBeGreaterThanOrEqual(3)
      expect(contrast(colour, '#ffffff')).toBeGreaterThanOrEqual(3)
      expect(contrast(colour, '#17110d')).toBeGreaterThanOrEqual(3)
    }
  })

  test('every drawing carries both schemes and reduced motion', () => {
    const drawings = [
      dot('running', { pulse: true }),
      ring(0.4),
      bar(200, 0.5, { running: true }),
      ribbon(400, { id: 'r', icon: 'commit', title: 'Commit' }),
      timeline(300, ['a', 'b', 'c'], 1),
      backdrop(),
    ]
    for (const svg of drawings) {
      expect(svg).toContain('prefers-color-scheme: dark')
      expect(svg).toContain('prefers-reduced-motion')
    }
    const fixed = ring(0.4, { scheme: 'dark' })
    expect(fixed).not.toContain('prefers-color-scheme')
    expect(fixed).toContain('#e8ae62')
    expect(backdrop({ scheme: 'dark' })).toContain('#17110d')
    expect(backdrop({ scheme: 'light' })).toContain('#f4ece0')
  })

  test('a ribbon never goes below the minimum width and escapes its title', () => {
    const svg = ribbon(100, { id: 'a', icon: 'commit', title: 'a < b & "c"' })
    expect(svg).toContain('width="240"')
    expect(svg).toContain('a &lt; b &amp; &quot;c&quot;')
    expect(svg).not.toContain('a < b')
  })

  test('two drawings never share an id', () => {
    const pairs: [string, string][] = [
      [ribbon(400, { id: 'x1', icon: 'qa', title: 'QA' }), ribbon(400, { id: 'x2', icon: 'qa', title: 'QA' })],
      [ring(0.3, { id: 'x1' }), ring(0.3, { id: 'x2' })],
      [bar(200, 0.3, { id: 'x1', running: true }), bar(200, 0.3, { id: 'x2', running: true })],
      [timeline(300, ['a', 'b'], 0, { id: 'x1' }), timeline(300, ['a', 'b'], 0, { id: 'x2' })],
    ]
    for (const [first, second] of pairs) {
      const shared = ids(first).filter(id => ids(second).includes(id))
      expect(shared).toEqual([])
    }
  })

  test('a waiting ribbon shimmers in CSS for as long as it waits, with a rest between passes; a settled one does not', () => {
    const waiting = ribbon(400, { id: 'q', icon: { badge: 'Q1' }, title: 'Question', waiting: true })
    expect(waiting).toContain('class="shimmer motion"')
    expect(waiting).not.toContain('<animate')
    expect(waiting).toMatch(/\.shimmer\{animation:sweep [\d.]+s [^;}]*infinite\}/)
    expect(waiting).toMatch(/@keyframes sweep\{0%\{[^}]*\}\d+%,100%\{/)
    expect(ribbon(400, { id: 'q', icon: { badge: 'Q1' }, title: 'Question', waiting: false })).not.toContain('class="shimmer')
  })

  test('a running bar carries its light in CSS, never SMIL (images do not run SMIL)', () => {
    const running = bar(200, 0.5, { running: true })
    expect(running).toContain('class="glide motion"')
    expect(running).not.toContain('<animate')
  })

  test('pill labels are drawn in the text colour, the tone stays on the dot and the rim', () => {
    const drawn = pills([{ label: 'graph périmé', tone: 'warning' }]).source
    expect(drawn).toMatch(/<text[^>]*style="fill:var\(--text\)"[^>]*>graph périmé</)
  })

  test('past the last step, the timeline shows every step done and nothing pulsing', () => {
    const svg = timeline(300, ['a', 'b', 'c'], 3)
    expect(svg).not.toContain('class="wave')
    expect(svg.match(/style="fill:var\(--accent\)"/g)?.length).toBe(3)
  })

  test('a ribbon can round its top corners to follow the card it heads', () => {
    const rounded = ribbon(400, { id: 'c', icon: 'commit', title: 'Commit', radius: 10 })
    expect(rounded).toContain('<clipPath id="s-c-r"><rect width="400" height="46" rx="10"/></clipPath>')
    expect(rounded).toContain('clip-path="url(#s-c-r)"')
    expect(ribbon(400, { id: 'c', icon: 'commit', title: 'Commit' })).not.toContain('s-c-r')
  })

  test('ring and bar clamp their fraction', () => {
    expect(ring(1.7)).toEqual(ring(1))
    expect(bar(200, -1)).toEqual(bar(200, 0))
  })

  test('a hollow dot is a ring for a step still ahead', () => {
    expect(dot('muted', { hollow: true })).toContain('fill="none"')
    expect(dot('muted')).not.toContain('fill="none"')
  })

  test('pills wrap onto a second row when the width runs out, and carry a hint', () => {
    const items = ['graphe à jour', 'arbre sale', 'revue faite', 'tests verts'].map(label => ({ label, tone: 'ok' as const, hint: `${label} !` }))
    const wide = pills(items, { maxWidth: 1000 })
    const narrow = pills(items, { maxWidth: 240 })
    expect(narrow.height).toBeGreaterThan(wide.height)
    expect(narrow.width).toBeLessThanOrEqual(240)
    expect(wide.source).toContain('<title>graphe à jour !</title>')
  })

  test('a pill is minimal: one flat fill, a hairline rim, a soft shadow for relief', () => {
    const svg = pill(600, 40)
    expect(svg).toContain('width="600"')
    expect(svg).not.toContain('<linearGradient')
    expect(svg).not.toContain('var(--highlight)')
    expect(svg).toContain('feDropShadow')
    expect(svg).toContain('style="fill:var(--pill1)')
    expect(svg).toContain('prefers-color-scheme: dark')
  })

  test('a pill takes the radius it is given and sits centred in its drawing', () => {
    const svg = pill(600, 40, { radius: 6 })
    expect(svg).toContain('rx="6"')
    const rect = /<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"/.exec(svg)
    const [x = NaN, y = NaN, w = NaN, h = NaN] = (rect ?? []).slice(1).map(Number)
    expect(y).toBe(40 - (y + h))
    expect(x).toBe(600 - (x + w))
  })

  test('the timeline keeps its first and last labels inside the drawing', () => {
    const svg = timeline(300, ['cadrage', 'ff', 'archive'], 1)
    const xs = [...svg.matchAll(/<text x="([\d.]+)"/g)].map(match => Number(match[1]))
    expect(xs[0]).toBeGreaterThanOrEqual(('cadrage'.length * 5.6) / 2)
    expect(300 - (xs.at(-1) ?? 0)).toBeGreaterThanOrEqual(('archive'.length * 5.6) / 2)
  })

  test('sizes stay under the Svg limit', () => {
    expect(backdrop().length).toBeLessThan(131072)
  })
})
