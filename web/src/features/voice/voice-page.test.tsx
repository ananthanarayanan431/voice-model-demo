import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { RecognitionResultEvent } from './speech-recognition'
import { VoicePage } from './voice-page'

/** A stand-in for the browser's speech recognition that tests can speak into. */
class FakeRecognition {
  static last: FakeRecognition | null = null
  lang = ''
  continuous = false
  interimResults = false
  started = 0
  onresult: ((event: RecognitionResultEvent) => void) | null = null
  onerror: ((event: { error: string }) => void) | null = null
  onend: (() => void) | null = null

  constructor() {
    FakeRecognition.last = this
  }
  start() {
    this.started += 1
  }
  stop() {}
  abort() {}

  say(text: string, isFinal: boolean) {
    this.onresult?.({ resultIndex: 0, results: [{ isFinal, length: 1, 0: { transcript: text } }] })
  }
}

const doctors = [
  {
    id: 'dr-kavya-rao',
    name: 'Dr. Kavya Rao',
    specialty: 'Orthopaedics',
    days: ['Mon', 'Tue'],
    hours: '10:00-16:00',
  },
]

const ok = (data: unknown) => Response.json({ success: true, data, request_id: 'req-1' })

function mockApi(
  reply: { reply: string; appointments: unknown[]; audio_url?: string | null },
  speechEnabled = false,
) {
  const fetchMock = vi.fn<typeof fetch>(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/ready'))
      return ok({ status: 'ok', speech_enabled: speechEnabled, llm_model: 'claude-opus-5-5' })
    if (url.endsWith('/api/v1/doctors')) return ok(doctors)
    if (url.endsWith('/api/v1/chat')) return ok({ audio_url: null, ...reply })
    return ok({ session_id: 'x' })
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

beforeEach(() => {
  FakeRecognition.last = null
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('VoicePage', () => {
  it('shows the live transcript while speaking, then the reply, then listens again', async () => {
    vi.stubGlobal('webkitSpeechRecognition', FakeRecognition)
    const fetchMock = mockApi({ reply: 'Dr. Kavya Rao is in on Monday.', appointments: [] })
    const user = userEvent.setup()
    render(<VoicePage />)

    await user.click(screen.getByRole('button', { name: /start call/i }))
    const mic = FakeRecognition.last
    expect(mic?.lang).toBe('en-IN')
    expect(mic?.interimResults).toBe(true)
    expect(screen.getByRole('status')).toHaveTextContent('Listening')

    act(() => mic?.say('I want to see a bone', false))
    expect(screen.getByText('I want to see a bone')).toBeInTheDocument()
    expect(screen.getByText('You (speaking…)')).toBeInTheDocument()

    act(() => mic?.say('I want to see a bone doctor', true))
    expect(await screen.findByText('Dr. Kavya Rao is in on Monday.')).toBeInTheDocument()

    const chatCall = fetchMock.mock.calls.find(([url]) => String(url).endsWith('/api/v1/chat'))
    const body = JSON.parse(String(chatCall?.[1]?.body)) as { message: string }
    expect(body.message).toBe('I want to see a bone doctor')

    // Voice replies are off (no Vartaloop key), so the mic comes straight back.
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Listening'))
    expect(mic?.started).toBe(2)
    expect(screen.getByText(/Voice replies are off/)).toBeInTheDocument()
  })

  it('plays the reply from its audio link with the mic off, then listens again', async () => {
    vi.stubGlobal('webkitSpeechRecognition', FakeRecognition)
    const played: FakeAudio[] = []
    class FakeAudio {
      onended: (() => void) | null = null
      onerror: (() => void) | null = null
      readonly src: string
      constructor(src: string) {
        this.src = src
        played.push(this)
      }
      play() {
        return Promise.resolve()
      }
      pause() {}
    }
    vi.stubGlobal('Audio', FakeAudio)
    mockApi({ reply: 'Namaste!', appointments: [], audio_url: '/api/v1/speech/abc123' }, true)
    const user = userEvent.setup()
    render(<VoicePage />)

    await user.click(screen.getByRole('button', { name: /start call/i }))
    const mic = FakeRecognition.last
    act(() => mic?.say('Hello', true))

    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Speaking'))
    expect(played[0]?.src).toBe('/api/v1/speech/abc123')
    expect(mic?.started).toBe(1)

    act(() => played[0]?.onended?.())
    expect(screen.getByRole('status')).toHaveTextContent('Listening')
    expect(mic?.started).toBe(2)
  })

  it('lists appointments booked on the call', async () => {
    vi.stubGlobal('webkitSpeechRecognition', FakeRecognition)
    mockApi({
      reply: 'Booked.',
      appointments: [
        {
          id: 'SH-1001',
          doctor_name: 'Dr. Kavya Rao',
          specialty: 'Orthopaedics',
          day: '2026-11-30',
          start: '11:00:00',
          patient_name: 'Asha',
        },
      ],
    })
    const user = userEvent.setup()
    render(<VoicePage />)

    await user.type(screen.getByLabelText('Type a message'), 'Book 11 am please')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(await screen.findByText('Booking id SH-1001')).toBeInTheDocument()
    expect(screen.getByText(/11:00 am · Asha/)).toBeInTheDocument()
  })

  it('falls back to typing when the browser has no speech recognition', async () => {
    mockApi({ reply: 'Namaste!', appointments: [] })
    render(<VoicePage />)
    expect(screen.queryByRole('button', { name: /start call/i })).not.toBeInTheDocument()
    expect(screen.getByText(/This browser has no speech recognition/)).toBeInTheDocument()
    expect(await screen.findByText('Dr. Kavya Rao')).toBeInTheDocument()
  })
})
