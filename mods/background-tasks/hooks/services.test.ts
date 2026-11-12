import { describe, expect, test } from 'claude-code/testing'

import { mergeServices, portOf } from './shared/services'

describe('services', () => {
  test('the port a command names, in its usual spellings', () => {
    expect(['npm run dev -- --port 5173', 'java -jar app.jar -p 8080', 'PORT=3000 node server.js', 'curl localhost:4443/x', 'npm run dev'].map(portOf)).toEqual([
      5173, 8080, 3000, 4443, null,
    ])
  })

  test('a turn’s end keeps the shells still in flight, each with the time first seen; the rest leave', () => {
    const first = mergeServices(
      [],
      [
        { id: 's1', type: 'shell', status: 'running', description: 'Frontend dev server', command: 'npm run dev -- --port 5173' },
        { id: 'w1', type: 'workflow', status: 'running', description: 'apply' },
        { id: 's2', type: 'shell', status: 'completed', description: 'build', command: 'npm run build' },
      ],
      1000,
    )
    expect(first).toEqual([{ id: 's1', label: 'Frontend dev server', command: 'npm run dev -- --port 5173', status: 'running', port: 5173, firstSeenAt: 1000 }])
    const later = mergeServices(first, [{ id: 's1', type: 'shell', status: 'running', description: 'Frontend dev server', command: 'npm run dev -- --port 5173' }], 9000)
    expect(later[0]?.firstSeenAt).toBe(1000)
    expect(mergeServices(later, [], 12000)).toEqual([])
  })
})
