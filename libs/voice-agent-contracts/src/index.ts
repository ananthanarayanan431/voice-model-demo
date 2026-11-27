/**
 * The voice agent's REST contract, generated from its OpenAPI document
 * (agents/voice_agent, `make openapi`). Import request and response shapes from
 * here instead of declaring them by hand, so a backend change that breaks the web
 * app fails type-checking.
 */
import type { components } from './schema'

export type { components, paths } from './schema'

type Schemas = components['schemas']

export type ChatRequest = Schemas['ChatRequest']
export type ChatResponse = Schemas['ChatResponse']
export type AppointmentOut = Schemas['AppointmentOut']
export type DoctorOut = Schemas['DoctorOut']
export type ReadyResponse = Schemas['ReadyResponse']
