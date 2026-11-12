import { describe, expect, test } from 'claude-code/testing'

import { spinnerSuffix, toolCard, toolTail } from './logic'

describe('spinner', () => {
  test('the suffix names the context, or nothing', () => {
    expect(spinnerSuffix(41.6)).toBe(' · contexte 42 %')
    expect(spinnerSuffix(null)).toBe('')
  })
})

describe('tool cards', () => {
  test('each tool reads by what it acts on, and Edit stays native', () => {
    expect(toolCard('Bash', { command: 'git status', description: 'Show status' }, '/r')).toEqual({ icon: '❯', title: 'Show status', detail: 'git status', tone: 'tool' })
    expect(toolCard('Bash', { command: 'ls' }, '/r')?.title).toBe('ls')
    expect(toolCard('Read', { file_path: '/r/src/a.ts', offset: 10, limit: 20 }, '/r')).toMatchObject({ title: 'src/a.ts', detail: 'l. 10+20' })
    expect(toolCard('Agent', { description: 'impl:14', subagent_type: 'frontend-dev' }, '/r')).toMatchObject({ title: 'impl:14', detail: 'frontend-dev', tone: 'agent' })
    expect(toolCard('Workflow', { script: "export const meta = { name: 'review-close-out', description: 'x' }" }, '/r')?.title).toBe('review-close-out')
    expect(toolCard('Edit', { file_path: '/r/a.ts' }, '/r')).toBe(null)
  })

  test('the tail says running, error, interrupted or the duration', () => {
    const base = { isRunning: false, isErrored: false, isInterrupted: false, durationMs: undefined }
    expect(toolTail({ ...base, isRunning: true }).text).toBe('en cours')
    expect(toolTail({ ...base, isErrored: true }).tone).toBe('error')
    expect(toolTail({ ...base, isInterrupted: true }).text).toBe('interrompu')
    expect(toolTail({ ...base, durationMs: 420 }).text).toBe('0,4 s ✓')
    expect(toolTail({ ...base, durationMs: 125 * 1000 }).text).toBe('2 min ✓')
  })
})

