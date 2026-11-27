/** REST client for the voice agent. Every failure becomes an `ApiError`. */
import type {
  ChatRequest,
  ChatResponse,
  DoctorOut,
  ReadyResponse,
} from '@voiceagent/voice-agent-contracts'

import { API_BASE_URL, API_KEY, API_PREFIX } from './config'

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function headers(json: boolean): HeadersInit {
  const result: Record<string, string> = {}
  if (json) result['Content-Type'] = 'application/json'
  if (API_KEY) result['X-API-Key'] = API_KEY
  return result
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init)
  } catch {
    throw new ApiError('Could not reach the assistant. Is the agent running?', 0)
  }
  if (!response.ok) {
    let detail = `The assistant returned an error (${response.status}).`
    try {
      const body: unknown = await response.json()
      if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
        detail = body.detail
      }
    } catch {
      /* not JSON: keep the generic message */
    }
    throw new ApiError(detail, response.status)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export function sendTurn(body: ChatRequest): Promise<ChatResponse> {
  return request(`${API_PREFIX}/chat`, {
    method: 'POST',
    headers: headers(true),
    body: JSON.stringify(body),
  })
}

export function resetCall(sessionId: string): Promise<void> {
  return request(`${API_PREFIX}/chat/reset`, {
    method: 'POST',
    headers: headers(true),
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export function getDoctors(): Promise<DoctorOut[]> {
  return request(`${API_PREFIX}/doctors`, { headers: headers(false) })
}

export function getReady(): Promise<ReadyResponse> {
  return request('/ready')
}

/** A GET URL an <audio> element can stream: Ogg/Opus from Vartaloop via the agent. */
export function ttsUrl(text: string): string {
  return `${API_BASE_URL}${API_PREFIX}/tts?${new URLSearchParams({ text }).toString()}`
}
