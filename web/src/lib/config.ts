/**
 * Runtime configuration, read from the VITE_* variables baked in at build time.
 * `VITE_API_URL` empty means "same origin as the app" (Vite proxy / nginx).
 */
export const API_BASE_URL: string = (import.meta.env.VITE_API_URL ?? '').replace(/\/+$/, '')

/** Sent as `X-API-Key`. A light gate for a private deployment, not authentication. */
export const API_KEY: string = import.meta.env.VITE_API_KEY ?? ''

export const API_PREFIX = '/api/v1'
