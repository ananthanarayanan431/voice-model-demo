import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, sendTurn, ttsUrl } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api', () => {
  it('builds a streamable TTS URL', () => {
    expect(ttsUrl('Namaste, 11 बजे')).toBe(
      `/api/v1/tts?text=${encodeURIComponent('Namaste, 11 बजे').replace(/%20/g, '+')}`,
    )
  })

  it("turns an error response into an ApiError with the server's detail", async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>(async () =>
        Response.json({ detail: 'Claude rejected the API key.' }, { status: 502 }),
      ),
    )
    const error = await sendTurn({ session_id: 'session-1', message: 'hi' }).catch(
      (e: unknown) => e,
    )
    expect(error).toBeInstanceOf(ApiError)
    expect((error as ApiError).message).toBe('Claude rejected the API key.')
    expect((error as ApiError).status).toBe(502)
  })

  it('reports an unreachable agent', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    await expect(sendTurn({ session_id: 'session-1', message: 'hi' })).rejects.toThrow(
      /Could not reach the assistant/,
    )
  })
})
