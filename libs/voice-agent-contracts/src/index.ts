/**
 * The voice agent's REST contract, generated from its OpenAPI document
 * (agents/voice_agent, `make openapi`). Import request and response shapes from
 * here instead of declaring them by hand, so a backend change that breaks the web
 * app fails type-checking.
 *
 * Every JSON response is an envelope: `SuccessResponse<T>` or `ErrorResponse`.
 */
import type { components } from './schema'

export type { components, paths } from './schema'

type Schemas = components['schemas']

export type ChatRequest = Schemas['ChatRequest']
export type ChatReply = Schemas['ChatReply']
export type ResetResult = Schemas['ResetResult']
export type AppointmentOut = Schemas['AppointmentOut']
export type DoctorOut = Schemas['DoctorOut']
export type ReadyStatus = Schemas['ReadyStatus']
export type ErrorResponse = Schemas['ErrorResponse']
export type FieldError = Schemas['FieldError']

/** The success envelope around `data` (the generated names are per payload). */
export interface SuccessResponse<T> {
  success: true
  data: T
  request_id: string
}
