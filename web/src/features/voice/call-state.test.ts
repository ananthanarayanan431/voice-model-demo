import { describe, expect, it } from 'vitest'

import { callReducer, initialCallState, type CallState } from './call-state'

const appointment = {
  id: 'SH-1001',
  doctor_name: 'Dr. Kavya Rao',
  specialty: 'Orthopaedics',
  day: '2026-11-30',
  start: '11:00:00',
  patient_name: 'Asha',
}

function run(...actions: Parameters<typeof callReducer>[1][]): CallState {
  return actions.reduce(callReducer, initialCallState)
}

describe('callReducer', () => {
  it('shows interim words only while listening', () => {
    expect(run({ type: 'interim', text: 'hello' }).interim).toBe('')
    expect(run({ type: 'listen' }, { type: 'interim', text: 'hello' }).interim).toBe('hello')
  })

  it('turns a final sentence into a patient turn and starts thinking', () => {
    const state = run(
      { type: 'listen' },
      { type: 'interim', text: 'I want' },
      { type: 'patient_said', text: '  I want a doctor  ' },
    )
    expect(state.turns).toEqual([{ id: 1, role: 'patient', text: 'I want a doctor' }])
    expect(state.status).toBe('thinking')
    expect(state.interim).toBe('')
  })

  it('ignores an empty final sentence', () => {
    const state = run({ type: 'listen' }, { type: 'patient_said', text: '   ' })
    expect(state.turns).toEqual([])
    expect(state.status).toBe('listening')
  })

  it('speaks the reply, then listens again', () => {
    const replied = run(
      { type: 'listen' },
      { type: 'patient_said', text: 'hi' },
      { type: 'assistant_replied', text: 'Namaste', appointments: [], speak: true },
    )
    expect(replied.status).toBe('speaking')
    expect(callReducer(replied, { type: 'speech_finished' }).status).toBe('listening')
  })

  it('goes straight back to listening when the reply is not spoken', () => {
    const state = run(
      { type: 'patient_said', text: 'hi' },
      { type: 'assistant_replied', text: 'Namaste', appointments: [], speak: false },
    )
    expect(state.status).toBe('listening')
  })

  it('keeps each appointment once', () => {
    const state = run(
      { type: 'assistant_replied', text: 'Booked', appointments: [appointment], speak: false },
      {
        type: 'assistant_replied',
        text: 'Still booked',
        appointments: [appointment],
        speak: false,
      },
    )
    expect(state.appointments).toEqual([appointment])
  })

  it('records a failure and stops the call', () => {
    const state = run({ type: 'listen' }, { type: 'failed', message: 'Mic blocked' })
    expect(state.status).toBe('idle')
    expect(state.error).toBe('Mic blocked')
    expect(callReducer(state, { type: 'listen' }).error).toBeNull()
  })

  it('starts over on a new call', () => {
    const state = run({ type: 'patient_said', text: 'hi' }, { type: 'new_call' })
    expect(state).toEqual(initialCallState)
  })
})
