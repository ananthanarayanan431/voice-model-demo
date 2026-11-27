import { describe, expect, it } from 'vitest'

import {
  describeError,
  isTransientError,
  readResults,
  type RecognitionResultEvent,
} from './speech-recognition'

function event(resultIndex: number, results: [string, boolean][]): RecognitionResultEvent {
  return {
    resultIndex,
    results: results.map(([transcript, isFinal]) => ({ isFinal, length: 1, 0: { transcript } })),
  }
}

describe('readResults', () => {
  it('separates settled text from the changing tail', () => {
    expect(
      readResults(
        event(0, [
          [' I need ', true],
          ['a doc', false],
        ]),
      ),
    ).toEqual({
      final: 'I need',
      interim: 'a doc',
    })
  })

  it('reads only results from resultIndex on', () => {
    expect(
      readResults(
        event(1, [
          ['old', true],
          ['new', false],
        ]),
      ),
    ).toEqual({
      final: '',
      interim: 'new',
    })
  })
})

describe('errors', () => {
  it('treats silence as transient and a blocked mic as fatal', () => {
    expect(isTransientError('no-speech')).toBe(true)
    expect(isTransientError('not-allowed')).toBe(false)
    expect(describeError('not-allowed')).toMatch(/Microphone access was blocked/)
  })
})
