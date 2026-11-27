import { describe, expect, it } from 'vitest'

import { formatDay, formatTime } from './format'

describe('format', () => {
  it('formats API times on a 12-hour clock', () => {
    expect(formatTime('11:00:00')).toBe('11:00 am')
    expect(formatTime('14:20:00')).toBe('2:20 pm')
    expect(formatTime('00:05')).toBe('12:05 am')
    expect(formatTime('noon')).toBe('noon')
  })

  it('formats API dates without a time zone shift', () => {
    expect(formatDay('2026-11-30')).toMatch(/30/)
    expect(formatDay('2026-11-30')).toMatch(/Nov/)
    expect(formatDay('bad')).toBe('bad')
  })
})
