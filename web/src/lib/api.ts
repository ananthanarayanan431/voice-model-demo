/**
 * REST client for the voice agent. Every response is an envelope; this unwraps
 * `data` on success and turns any failure into an `ApiError` carrying the
 * server's error code, a message fit to show a user, and the request id.
 */
import type {
  ChatReply,
  ChatRequest,
  DoctorOut,
  ErrorResponse,
  ReadyStatus,
  ResetResult,
  SuccessResponse,
} from '@voiceagent/voice-agent-contracts'

import { API_BASE_URL, API_KEY, API_PREFIX } from './config'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId: string | null

  constructor(message: string, status: number, code: string, requestId: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

function isErrorResponse(body: unknown): body is ErrorResponse {
  return (
    typeof body === 'object' &&
    body !== null &&
    'success' in body &&
    body.success === false &&
    'error' in body
  )
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
    throw new ApiError('Could not reach the assistant. Is the agent running?', 0, 'network_error')
  }

  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    /* not JSON (e.g. a proxy error page): handled below */
  }

  if (!response.ok || !body || typeof body !== 'object' || !('success' in body)) {
    if (isErrorResponse(body)) {
      throw new ApiError(body.error.message, response.status, body.error.code, body.request_id)
    }
    throw new ApiError(
      `The assistant returned an error (${response.status}).`,
      response.status,
      'http_error',
    )
  }
  return (body as SuccessResponse<T>).data
}

export function sendTurn(body: ChatRequest): Promise<ChatReply> {
  return request(`${API_PREFIX}/chat`, {
    method: 'POST',
    headers: headers(true),
    body: JSON.stringify(body),
  })
}

export function resetCall(sessionId: string): Promise<ResetResult> {
  return request(`${API_PREFIX}/chat/reset`, {
    method: 'POST',
    headers: headers(true),
    body: JSON.stringify({ session_id: sessionId }),
  })
}

export function getDoctors(): Promise<DoctorOut[]> {
  return request(`${API_PREFIX}/doctors`, { headers: headers(false) })
}

export function getReady(): Promise<ReadyStatus> {
  return request('/ready')
}

/** The reply's audio link from `/chat` is relative to the API's origin. */
export function audioSrc(audioUrl: string): string {
  return `${API_BASE_URL}${audioUrl}`
}
