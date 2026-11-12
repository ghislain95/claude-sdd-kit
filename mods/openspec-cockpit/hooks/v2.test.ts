import { describe, expect, test } from 'claude-code/testing'

import { stepIndexOf } from './logic'

describe('cycle position', () => {
  test('closing walks review, then commit, then archive', () => {
    expect(stepIndexOf('apply', false, 3)).toBe(2)
    expect(stepIndexOf('closing', false, 3)).toBe(3)
    expect(stepIndexOf('closing', true, 3)).toBe(5)
    expect(stepIndexOf('closing', true, 0)).toBe(6)
    expect(stepIndexOf('post-archive', true, 0)).toBe(7)
    expect(stepIndexOf('idle', false, 0)).toBe(-1)
  })
})
