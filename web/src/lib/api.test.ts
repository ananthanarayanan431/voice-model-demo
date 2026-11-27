import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, audioSrc, getDoctors, sendTurn } from './api'

afterEach(() => {
  vi.unstubAllGlobals()
})

function stubFetch(response: () => Response | Promise<Response>) {
  vi.stubGlobal(
    'fetch',
    vi.fn<typeof fetch>(async () => response()),
  )
}

describe('api', () => {
  it('unwraps data from the success envelope', async () => {
    stubFetch(() => Response.json({ success: true, data: [{ id: 'dr-1' }], request_id: 'req-1' }))
    await expect(getDoctors()).resolves.toEqual([{ id: 'dr-1' }])
  })

  it('turns the error envelope into an ApiError with code and request id', async () => {
    stubFetch(() =>
      Response.json(
        {
          success: false,
          error: { code: 'rate_limited', message: 'Too many requests.', fields: [] },
          request_id: 'req-9',
        },
        { status: 429 },
      ),
    )
    const error = await sendTurn({ session_id: 'session-1', message: 'hi' }).catch(
      (e: unknown) => e,
    )
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      message: 'Too many requests.',
      status: 429,
      code: 'rate_limited',
      requestId: 'req-9',
    })
  })

  it('handles a non-JSON error page from a proxy', async () => {
    stubFetch(() => new Response('<html>Bad gateway</html>', { status: 502 }))
    await expect(getDoctors()).rejects.toMatchObject({ status: 502, code: 'http_error' })
  })

  it('reports an unreachable agent', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn<typeof fetch>(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    await expect(sendTurn({ session_id: 'session-1', message: 'hi' })).rejects.toMatchObject({
      code: 'network_error',
    })
  })

  it('resolves audio links against the API origin', () => {
    expect(audioSrc('/api/v1/speech/abc')).toBe('/api/v1/speech/abc')
  })
})
