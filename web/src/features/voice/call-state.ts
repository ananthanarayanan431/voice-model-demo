/**
 * The call as a pure state machine: what the patient said, what the assistant
 * replied, and which half of the conversation is happening now. No DOM, no
 * microphone, no network: the hook drives it, and the tests run it directly.
 */
import type { AppointmentOut } from '@voiceagent/voice-agent-contracts'

export type CallStatus = 'idle' | 'listening' | 'thinking' | 'speaking'

export interface Turn {
  id: number
  role: 'patient' | 'assistant'
  text: string
}

export interface CallState {
  status: CallStatus
  turns: Turn[]
  /** Words recognised so far in the patient's current sentence, shown live. */
  interim: string
  appointments: AppointmentOut[]
  error: string | null
  nextId: number
}

export type CallAction =
  | { type: 'listen' }
  | { type: 'interim'; text: string }
  | { type: 'patient_said'; text: string }
  | { type: 'assistant_replied'; text: string; appointments: AppointmentOut[]; speak: boolean }
  | { type: 'speech_finished' }
  | { type: 'failed'; message: string }
  | { type: 'hang_up' }
  | { type: 'new_call' }

export const initialCallState: CallState = {
  status: 'idle',
  turns: [],
  interim: '',
  appointments: [],
  error: null,
  nextId: 1,
}

function addTurn(state: CallState, role: Turn['role'], text: string): CallState {
  return {
    ...state,
    turns: [...state.turns, { id: state.nextId, role, text }],
    nextId: state.nextId + 1,
  }
}

export function callReducer(state: CallState, action: CallAction): CallState {
  switch (action.type) {
    case 'listen':
      return { ...state, status: 'listening', interim: '', error: null }
    case 'interim':
      return state.status === 'listening' ? { ...state, interim: action.text } : state
    case 'patient_said': {
      const text = action.text.trim()
      if (!text) return { ...state, interim: '' }
      return { ...addTurn(state, 'patient', text), status: 'thinking', interim: '' }
    }
    case 'assistant_replied': {
      const known = new Set(state.appointments.map((a) => a.id))
      const added = action.appointments.filter((a) => !known.has(a.id))
      return {
        ...addTurn(state, 'assistant', action.text),
        status: action.speak ? 'speaking' : 'listening',
        appointments: [...state.appointments, ...added],
      }
    }
    case 'speech_finished':
      return state.status === 'speaking' ? { ...state, status: 'listening' } : state
    case 'failed':
      return { ...state, status: 'idle', interim: '', error: action.message }
    case 'hang_up':
      return { ...state, status: 'idle', interim: '' }
    case 'new_call':
      return initialCallState
  }
}
