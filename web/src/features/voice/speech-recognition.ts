/**
 * The browser's speech recognition (Web Speech API). TypeScript's DOM library
 * does not declare it, so the small surface this app uses is typed here.
 * Chrome and Edge implement it (as webkitSpeechRecognition) and send the audio
 * to the browser vendor's servers for recognition.
 */

export interface RecognitionAlternative {
  readonly transcript: string
}

export interface RecognitionResult {
  readonly isFinal: boolean
  readonly length: number
  readonly [index: number]: RecognitionAlternative | undefined
}

export interface RecognitionResultEvent {
  readonly resultIndex: number
  readonly results: {
    readonly length: number
    readonly [index: number]: RecognitionResult | undefined
  }
}

export interface RecognitionErrorEvent {
  readonly error: string
}

export interface Recognition {
  lang: string
  continuous: boolean
  interimResults: boolean
  onresult: ((event: RecognitionResultEvent) => void) | null
  onerror: ((event: RecognitionErrorEvent) => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
  abort(): void
}

export type RecognitionConstructor = new () => Recognition

export function getRecognitionConstructor(): RecognitionConstructor | null {
  if (typeof window === 'undefined') return null
  const w = window as unknown as Record<string, RecognitionConstructor | undefined>
  return w['SpeechRecognition'] ?? w['webkitSpeechRecognition'] ?? null
}

/** Split one result event into the settled text and the still-changing tail. */
export function readResults(event: RecognitionResultEvent): { final: string; interim: string } {
  let final = ''
  let interim = ''
  for (let i = event.resultIndex; i < event.results.length; i++) {
    const result = event.results[i]
    const text = result?.[0]?.transcript ?? ''
    if (result?.isFinal) final += text
    else interim += text
  }
  return { final: final.trim(), interim: interim.trim() }
}

/** Errors that mean "try again", not "stop the call". */
export function isTransientError(error: string): boolean {
  return error === 'no-speech' || error === 'aborted' || error === 'network'
}

export function describeError(error: string): string {
  if (error === 'not-allowed' || error === 'service-not-allowed') {
    return 'Microphone access was blocked. Allow it in the browser and start the call again.'
  }
  if (error === 'audio-capture') return 'No microphone was found.'
  return `Speech recognition stopped (${error}).`
}
