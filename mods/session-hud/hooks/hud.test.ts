import { describe, expect, test } from 'claude-code/testing'

import type { HudFigures } from '../types'
import { backgroundLabel, bandLine, fitBand, formatDuration, formatTokens, hudItems, modelLabel } from './hud'

const MINUTE = 60 * 1000
const NOW = Date.UTC(2026, 10, 6, 10, 0)

const FIGURES: HudFigures = {
  startedAt: NOW - 72 * MINUTE,
  contextPercent: 42,
  contextTokens: 420000,
  contextWindow: 1000000,
  costUsd: null,
  rateLimit: { kind: 'five_hour', percent: 63, resetsAt: null },
  model: 'claude-opus-5-5',
  toolCalls: 87,
  toolErrors: 2,
  tasks: [{ id: "s1", kind: "service", label: "Frontend", port: 5173, command: "npm run dev -- --port 5173" }, { id: "w1", kind: "workflow", label: "apply", port: null, command: null }, { id: "a1", kind: "agent", label: "impl", port: null, command: null }],
}

describe('the band', () => {
  test('reads context, the rate limit when there is no cost, time, tools, errors and the model, left to right', () => {
    const items = hudItems(FIGURES, NOW)
    expect(items.map(item => [item.key, item.value, item.label, item.tone])).toEqual([
      ['context', '42 %', 'contexte', 'ok'],
      ['spend', '63 %', 'limite 5 h', 'warning'],
      ['time', '1 h 12', 'session', 'neutral'],
      ['tools', '87', 'outils', 'neutral'],
      ['errors', '2', 'erreurs', 'danger'],
      ['model', 'Opus 5.5', '', 'muted'],
    ])
    expect(items[0]?.hint).toBe('420 k sur 1 M tokens')
  })

  test('a cost wins over the rate limit, no error shows no error, and a context past 85 % turns red', () => {
    const items = hudItems({ ...FIGURES, costUsd: 12.4, toolErrors: 0, contextPercent: 91 }, NOW)
    expect(items.map(item => item.key)).toEqual(['context', 'spend', 'time', 'tools', 'model'])
    expect(items[1]?.value).toBe('12,40 $')
    expect(items[0]?.tone).toBe('danger')
  })

  test('the background count shows only when something runs, and the terminal gets one line', () => {
    expect(backgroundLabel(0)).toBe(null)
    expect(bandLine(hudItems(FIGURES, NOW), 3)).toBe('42 % contexte · 63 % limite 5 h · 1 h 12 session · 87 outils · 2 erreurs · Opus 5.5 · ⚙ 3 en arrière-plan')
  })

  test('formats', () => {
    expect([formatDuration(40 * 1000), formatDuration(12 * MINUTE), formatDuration(72 * MINUTE)]).toEqual(['40 s', '12 min', '1 h 12'])
    expect([formatTokens(999), formatTokens(84000), formatTokens(1000000), formatTokens(1234567)]).toEqual(['999', '84 k', '1 M', '1,2 M'])
    expect([modelLabel('claude-opus-5-5'), modelLabel('claude-haiku-5-5[1m]'), modelLabel('gpt-x')]).toEqual(['Opus 5.5', 'Haiku 5.5', 'gpt-x'])
  })

  test('a band short of room drops its labels first, then the model, and never wraps an item', () => {
    const items = hudItems({ ...FIGURES, toolErrors: 2 }, NOW)
    const extra = '⚙ 1 en arrière-plan ▴'
    expect(fitBand(items, 900, extra)).toEqual({ items, showLabels: true })
    const tight = fitBand(items, 620, extra)
    expect(tight.showLabels).toBe(false)
    expect(tight.items.map(item => item.key)).toContain('model')
    const narrow = fitBand(items, 480, extra)
    expect(narrow.showLabels).toBe(false)
    expect(narrow.items.map(item => item.key)).not.toContain('model')
  })
})
