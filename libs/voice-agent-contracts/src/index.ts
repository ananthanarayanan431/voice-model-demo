/**
 * The voice agent's REST contract, generated from its OpenAPI document
 * (agents/voice_agent, `make openapi`). Import request and response shapes from
 * here instead of declaring them by hand, so a backend change that breaks the web
 * app fails type-checking.
 *
 * Add friendly aliases as schemas appear, e.g.
 *   export type HealthResponse = components['schemas']['HealthResponse']
 */
export type { components, paths } from './schema'
