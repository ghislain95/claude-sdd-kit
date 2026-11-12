import { type Engine, expect, mock, test } from 'claude-code/testing'
import type { FsEntry, On } from 'claude-code'

const MINUTE = 60 * 1000
const NOW = Date.UTC(2026, 10, 6, 10, 0)
const PROJECT = '/home/.claude/projects/-repo'
const RUN = `${PROJECT}/S1/subagents/workflows/wf_live`
const PANE = {
  component: 'Pane' as const,
  requestId: 'background',
  props: { title: 'En arrière-plan', isFocused: false, bodyColumns: 62, placement: 'dock' as const, scroll: { offset: 0, bodyRows: 40 }, view: {} },
}

type Node = { kind: 'file' | 'dir'; text?: string; mtimeMs: number }
const file = (text: string, mtimeMs: number): Node => ({ kind: 'file', text, mtimeMs })
const dir = (mtimeMs: number): Node => ({ kind: 'dir', mtimeMs })

function projectTree(): Record<string, Node> {
  return {
    [`${PROJECT}/S1/workflows`]: dir(NOW - 30 * MINUTE),
    [`${PROJECT}/S1/workflows/scripts`]: dir(NOW - 30 * MINUTE),
    [`${PROJECT}/S1/workflows/scripts/apply-s5-wf_live.js`]: file(
      [
        'export const meta = {',
        "  name: 'apply-s5',",
        "  description: 'Apply groups 17-18, then a review',",
        '  phases: [',
        "    { title: 'Group 17', detail: 'engine and bridge' },",
        "    { title: 'Review', detail: 'four lenses in parallel' },",
        '  ],',
        '}',
      ].join('\n'),
      NOW - 30 * MINUTE,
    ),
    [RUN]: dir(NOW - MINUTE),
    [`${RUN}/journal.jsonl`]: file('{"type":"launched"}\n{"type":"started","agentId":"a","label":"impl:17","phase":"Group 17"}\n', NOW - MINUTE),
    [`${RUN}/agent-a.meta.json`]: file('{"agentType":"rendering-dev","description":"impl:17"}', NOW - 30 * MINUTE),
    [`${RUN}/agent-a.jsonl`]: file(
      '{"type":"assistant","message":{"model":"claude-opus-5-5","id":"m","content":[{"type":"tool_use","id":"t","name":"Bash","input":{}}],"usage":{"input_tokens":2,"cache_read_input_tokens":170046,"output_tokens":671}}}',
      NOW - MINUTE,
    ),
    [`${PROJECT}/S2/workflows/wf_done.json`]: file(
      JSON.stringify({ runId: 'wf_done', workflowName: 'review-close-out', status: 'completed', durationMs: 59 * MINUTE, agentCount: 3, timestamp: new Date(NOW - 3 * MINUTE).toISOString() }),
      NOW - 3 * MINUTE,
    ),
  }
}

type Seen = { open: string[]; toasts: string[]; store: Map<string, unknown>; clock: ReturnType<typeof mock.clock> }

function world(on: On, tree: Record<string, Node>): Seen {
  const seen: Seen = { open: [], toasts: [], store: new Map(), clock: mock.clock(on, { now: NOW }) }
  mock.env(on, { HOME: '/home' })
  on('session.start', ($, e) => ({ cwd: e.cwd }))
  on('session.root', () => ({ value: '/repo' }))
  on('session.id', () => ({ value: 'S1' }))
  on('store.get', ($, e) => ({ value: seen.store.get(e.key) }))
  on('store.set', ($, e) => {
    seen.store.set(e.key, e.value)
    return { value: undefined }
  })
  on('agent.list', () => ({ value: [] as never }))
  on('command.register', ($, e) => ({ value: { command: e.name } }))
  on('ui.panes', () => ({ value: seen.open.map(id => ({ id, title: id })) as never }))
  on('ui.open', ($, e) => {
    seen.open.push(e.id)
    return { value: { isPlaced: true as const } }
  })
  on('ui.close', ($, e) => {
    seen.open = seen.open.filter(id => id !== e.id)
    return { value: undefined } as never
  })
  on('ui.toast', ($, e) => {
    seen.toasts.push(String(e.text))
    return { value: undefined }
  })
  on('ui.notify', () => ({ value: { isSent: false as const, reason: 'no-surface' as const } }))
  on('classic.Stop', () => ({}))
  const isUnder = (path: string, parent: string) => path.startsWith(`${parent}/`) && !path.slice(parent.length + 1).includes('/')
  on('fs.exists', ($, e) => ({ value: e.path in tree }))
  on('fs.stat', ($, e) => {
    const node = tree[e.path]
    if (node === undefined) return { deny: `ENOENT ${e.path}` }
    return { value: { kind: node.kind, size: node.text?.length ?? 0, mtimeMs: node.mtimeMs, isLink: false } }
  })
  on('fs.read', ($, e) => {
    const node = tree[e.path]
    if (node?.text === undefined) return { deny: `ENOENT ${e.path}` }
    return { value: node.text }
  })
  on('fs.list', ($, e) => {
    if (!(e.path in tree)) return { deny: `ENOENT ${e.path}` }
    return {
      value: Object.entries(tree)
        .filter(([path]) => isUnder(path, e.path))
        .map(([path, node]): FsEntry => ({ name: path.slice(e.path.length + 1), kind: node.kind, size: node.text?.length ?? 0, mtimeMs: node.mtimeMs, isLink: false })),
    }
  })
  on('process.run', ($, e) => {
    const ok = (stdout: string) => ({ value: { exitCode: 0, stdout, stderr: '', isStdoutTruncated: false, isStderrTruncated: false } })
    if (e.argv[0] === '/usr/bin/tail') return ok(tree[e.argv[3] ?? '']?.text ?? '')
    if (e.argv[0] === '/usr/bin/find') return ok(Object.keys(tree).filter(path => /journal\.jsonl$|\/workflows\/wf_[^/]+\.json$/.test(path)).join('\n'))
    return { value: { exitCode: 1, stdout: '', stderr: 'unexpected', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  return seen
}

const ORIGIN = { kind: 'composer' as const }
const PRESENTATION = { isFullscreen: true, columns: 120 }

function start($: Engine) {
  return $.session.start({ cwd: '/repo', surface: 'desktop', isInteractive: true })
}

test('the pane opens by itself at start, so the tasks show at a glance', async ($, on) => {
  const seen = world(on, projectTree())
  await start($)
  await seen.clock.advance(2000)
  expect(seen.open).toEqual(['background'])
})

test('in an OpenSpec project the pane stays shut: the cockpit shows the tasks', async ($, on) => {
  const tree = projectTree()
  tree['/repo/openspec'] = dir(NOW)
  const seen = world(on, tree)
  await start($)
  await seen.clock.advance(2000)
  expect(seen.open).toEqual([])
})

test('a pane the person closed stays closed in the next sessions, until /arriere-plan opens it again', async ($, on) => {
  const seen = world(on, projectTree())
  await start($)
  await seen.clock.advance(2000)
  await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })
  expect(seen.store.get('pane')).toBe('off')
  seen.open = []
  await start($)
  await seen.clock.advance(2000)
  expect(seen.open).toEqual([])
  await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })
  expect(seen.open).toEqual(['background'])
  expect(seen.store.get('pane')).toBe('on')
})

test('the command opens and closes the pane', async ($, on) => {
  const seen = world(on, projectTree())
  await start($)
  await seen.clock.advance(2000)
  await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })
  seen.open = []
  expect((await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })).text).toContain('ouvert')
  expect(seen.open).toEqual(['background'])
  expect((await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })).text).toContain('fermé')
  expect(seen.open).toEqual([])
})

test('a running workflow shows its phases, the running one with its agent, model and tokens; a finished run one line', async ($, on) => {
  world(on, projectTree())
  await start($)
  await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })
  const ui = await $.ui.mount({ plugin: 'background-tasks', surface: 'desktop', ...PANE })
  expect(await ui.find({ type: 'Text', text: 'apply-s5' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: 'Apply groups 17-18, then a review' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: 'impl:17' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: 'Opus 5.5 · 170,7 k tokens · Bash' })).toBeDefined()
  // A phase ahead is one line, its detail beside it.
  expect(await ui.find({ type: 'Text', text: 'four lenses in parallel' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: 'review-close-out' })).toBeDefined()
})

test('a service Claude left running appears at the turn’s end, with its port and command', async ($, on) => {
  world(on, {})
  await start($)
  const ui = await $.ui.mount({ plugin: 'background-tasks', surface: 'desktop', ...PANE })
  expect(await ui.find({ type: 'Text', text: 'Rien ne tourne en arrière-plan.' })).toBeDefined()
  await $.classic.Stop({
    stop_hook_active: false,
    background_tasks: [{ id: 's1', type: 'shell', status: 'running', description: 'Frontend dev server', command: 'npm run dev -- --port 5173' }],
  } as never)
  expect(await ui.find({ type: 'Text', text: 'Frontend dev server' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: ':5173' })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: 'npm run dev -- --port 5173' })).toBeDefined()
})

const NORD_COLOURS = ['#88C0D0', '#A3BE8C', '#EBCB8B', '#BF616A', '#B48EAD', '#7B88A1', '#4C566A', '#D8DEE9']

test('the pane wears Sienne: drawings follow the theme, a running bar moves, no Nord colour is left', async ($, on) => {
  world(on, projectTree())
  await start($)
  await $.command.run({ command: 'arriere-plan', args: '', origin: ORIGIN, presentation: PRESENTATION })
  const ui = await $.ui.mount({ plugin: 'background-tasks', surface: 'desktop', ...PANE })
  const drawings = await ui.findAll({ type: 'Svg' })
  expect(drawings.length).toBeGreaterThan(0)
  for (const drawing of drawings) expect(String(drawing.props.source)).toContain('prefers-color-scheme: dark')
  expect(drawings.some(drawing => /<animate|class="grow"/.test(String(drawing.props.source)))).toBe(true)
  const everything = JSON.stringify([...(await ui.findAll({ type: 'Box' })), ...(await ui.findAll({ type: 'Text' })), ...drawings].map(found => found.props))
  for (const colour of NORD_COLOURS) expect(everything.toUpperCase()).not.toContain(colour)
})
