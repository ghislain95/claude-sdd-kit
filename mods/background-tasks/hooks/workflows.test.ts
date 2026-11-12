import { describe, expect, test } from 'claude-code/testing'

import { formatTokens, modelLabel } from './shared/format'
import {
  agentFiguresLine,
  countFindings,
  journalDetail,
  liveRun,
  orderRuns,
  parseJournal,
  phaseRows,
  phasesLine,
  runsToAnnounce,
  scriptMeta,
  transcriptFacts,
} from './shared/workflows'

// Moved from openspec-cockpit, whose copies of these functions now live in shared/workflows.ts.

const MINUTE = 60 * 1000

describe('workflows', () => {
  const journal = [
    '{"type":"launched"}',
    '{"type":"started","label":"impl:13","phase":"Group 13"}',
    '{"type":"result","result":{}}',
    '{"type":"started","label":"verify:13","phase":"Group 13"}',
    'not json',
  ].join('\n')

  test('the journal counts agents and keeps the last label', () => {
    expect(parseJournal(journal)).toEqual({ started: 2, done: 1, lastLabel: 'verify:13', lastPhase: 'Group 13' })
  })

  test('a run whose folder is quiet for 20 minutes is silent', () => {
    const facts = parseJournal(journal)
    const now = 100 * MINUTE
    expect(liveRun({ id: 'a', sessionId: 's', journal: facts, startedAt: 0, lastActivityAt: now - 5 * MINUTE, now }).status).toBe('running')
    expect(liveRun({ id: 'a', sessionId: 's', journal: facts, startedAt: 0, lastActivityAt: now - 25 * MINUTE, now }).status).toBe('silent')
  })

  test('runs order running, then silent, then finished newest first', () => {
    const now = 2 * 24 * 60 * MINUTE
    const runs = orderRuns(
      [
        { id: 'old', sessionId: 's', status: 'completed', agentsStarted: 1, agentsDone: 1, finishedAt: now - 60 * MINUTE },
        { id: 'new', sessionId: 's', status: 'completed', agentsStarted: 1, agentsDone: 1, finishedAt: now - MINUTE },
        { id: 'run', sessionId: 's', status: 'running', agentsStarted: 1, agentsDone: 0, lastActivityAt: now },
        { id: 'dead', sessionId: 's', status: 'silent', agentsStarted: 1, agentsDone: 0, lastActivityAt: 0 },
      ],
      now,
      8,
    )
    expect(runs.map(run => run.id)).toEqual(['run', 'new', 'old'])
  })

  test('a finished run is announced once, and only while recent', () => {
    const now = 100 * MINUTE
    const done = { sessionId: 's', status: 'completed' as const, agentsStarted: 3, agentsDone: 3 }
    const runs = [
      { ...done, id: 'recent', finishedAt: now - 2 * MINUTE },
      { ...done, id: 'old', finishedAt: now - 30 * MINUTE },
      { ...done, id: 'seen', finishedAt: now - MINUTE },
    ]
    expect(runsToAnnounce(runs, ['seen'], now).map(run => run.id)).toEqual(['recent'])
  })
})

describe('agent figures', () => {
  test('models read by family and version, whatever the id looks like', () => {
    expect(modelLabel('claude-opus-5-5')).toBe('Opus 5.5')
    expect(modelLabel('claude-haiku-5-5[1m]')).toBe('Haiku 5.5')
    expect(modelLabel('claude-opus-4-1-20250805')).toBe('Opus 4.1')
    expect(modelLabel('claude-3-5-sonnet-20241022')).toBe('Sonnet 3.5')
    expect(modelLabel('gpt-x')).toBe('gpt-x')
  })

  test('tokens read in thousands or millions, with a French decimal comma', () => {
    expect([999, 443491, 1234567].map(formatTokens)).toEqual(['999', '443,5 k', '1,2 M'])
  })

  test('the line under an agent joins what is known, the tool only while it runs', () => {
    expect(agentFiguresLine({ model: 'claude-opus-5-5', tokens: 443491, lastTool: 'Bash' })).toBe('Opus 5.5 · 443,5 k tokens · Bash')
    expect(agentFiguresLine({ tokens: 1200 })).toBe('1,2 k tokens')
    expect(agentFiguresLine({})).toBe('')
  })
})


describe('workflow traces', () => {
  test('the script meta gives the run name, its purpose, its phase titles in order and their details', () => {
    const script = [
      'export const meta = {',
      "  name: 'offline-catalog-s4',",
      "  description: 'Apply groups 14-15, then review',",
      '  phases: [',
      "    { title: 'Group 14' },",
      `    { title: "Group 15", detail: "the planner's wiring, then tests" },`,
      "    { title: 'Review', detail: 'four lenses in parallel' },",
      '  ],',
      '}',
      "const name = 'not the meta'",
    ].join('\n')
    expect(scriptMeta(script)).toEqual({
      name: 'offline-catalog-s4',
      description: 'Apply groups 14-15, then review',
      phases: ['Group 14', 'Group 15', 'Review'],
      phaseDetails: { 'Group 15': "the planner's wiring, then tests", Review: 'four lenses in parallel' },
    })
  })

  test('the journal gives the agents, normalized findings and the last suite line', () => {
    const journal = [
      '{"type":"started","agentId":"a1","label":"impl:14","phase":"Group 14"}',
      '{"type":"result","agentId":"a1","result":{"openQuestions":["q1","q2"]}}',
      '{"type":"started","agentId":"a2","label":"verify:14","phase":"Group 14"}',
      '{"type":"result","agentId":"a2","result":{"findings":[{"severity":"MINEUR"},{"severity":"BLOCKING"},{"severity":"MAJOR"}],"fullVitest":"187 files / 2905 tests passed"}}',
      '{"type":"started","agentId":"a3","label":"impl:15","phase":"Group 15"}',
    ].join('\n')
    const detail = journalDetail(journal)
    expect(detail.agents.map(agent => [agent.id, agent.label, agent.state])).toEqual([
      ['a1', 'impl:14', 'done'],
      ['a2', 'verify:14', 'done'],
      ['a3', 'impl:15', 'running'],
    ])
    expect(detail.findings).toEqual({ blocking: 1, major: 1, minor: 1 })
    expect(detail.tests).toBe('187 files / 2905 tests passed')
    expect(detail.openQuestions).toBe(2)
    expect(detail.phaseCounts).toEqual({ 'Group 14': { started: 2, done: 2 }, 'Group 15': { started: 1, done: 0 } })
  })

  test('phases read done, running, upcoming, or skipped when a later one started first', () => {
    const run = {
      id: 'wf',
      sessionId: 's',
      status: 'running' as const,
      agentsStarted: 4,
      agentsDone: 3,
      phases: ['Group 17', 'Group 18a', 'Group 18b', 'Review', 'Fix'],
      phaseDetails: { 'Group 18b': 'search cases', Fix: 'fix confirmed findings' },
      phaseCounts: { 'Group 17': { started: 2, done: 2 }, 'Group 18b': { started: 2, done: 1 } },
      agents: [{ id: 'a3', label: 'impl:18b', phase: 'Group 18b', state: 'running' as const }],
    }
    expect(phaseRows(run).map(row => [row.title, row.state, `${row.done}/${row.started}`])).toEqual([
      ['Group 17', 'done', '2/2'],
      ['Group 18a', 'skipped', '0/0'],
      ['Group 18b', 'running', '1/2'],
      ['Review', 'upcoming', '0/0'],
      ['Fix', 'upcoming', '0/0'],
    ])
    expect(phaseRows(run)[4]?.detail).toBe('fix confirmed findings')
    expect(phasesLine(phaseRows(run))).toBe('✓ Group 17 · – Group 18a · ▶ Group 18b · ○ Review · ○ Fix')
    // Between two agents of the furthest phase (a verify loop), that phase is still the running one.
    const between = { ...run, phaseCounts: { 'Group 17': { started: 2, done: 2 } }, agents: [] }
    expect(phaseRows(between).map(row => row.state)).toEqual(['running', 'upcoming', 'upcoming', 'upcoming', 'upcoming'])
  })

  test("a transcript's tail gives the last turn's model and context, and the last tool, even cut mid-line", () => {
    const tail = [
      'tokens":12,"cut":"mid-line"}}',
      '{"type":"assistant","message":{"model":"claude-sonnet-5-5","id":"m1","content":[{"type":"tool_use","id":"t1","name":"Read","input":{}}],"usage":{"input_tokens":1,"output_tokens":9}}}',
      '{"type":"user","message":{"content":[{"type":"tool_result","content":"\\"input_tokens\\":999 quoted in a file"}]}}',
      '{"type":"assistant","message":{"model":"claude-opus-5-5","id":"m2","content":[{"type":"tool_use","id":"t2","name":"Bash","input":{}}],"usage":{"input_tokens":2,"cache_creation_input_tokens":2728,"cache_read_input_tokens":170046,"cache_creation":{"ephemeral_5m_input_tokens":2728,"ephemeral_1h_input_tokens":0},"output_tokens":671,"output_tokens_details":{"thinking_tokens":555}}}}',
    ].join('\n')
    expect(transcriptFacts(tail)).toEqual({ model: 'claude-opus-5-5', tokens: 173447, lastTool: 'Bash' })
    expect(transcriptFacts('{"type":"user","message":{"content":"a long tool result"}}')).toEqual({ model: undefined, tokens: undefined, lastTool: undefined })
  })

  test('findings are counted anywhere in a result', () => {
    expect(countFindings({ reviews: [{ findings: [{ severity: 'BLOQUANT' }] }], x: { severity: 'MAJEUR' } })).toEqual({ blocking: 1, major: 1, minor: 0 })
  })
})
