/**
 * One voice call: microphone -> live transcript -> agent -> spoken reply -> mic.
 *
 * The microphone is off while the assistant thinks and speaks, so its own voice
 * is never transcribed back. All the decisions about state live in the pure
 * `callReducer`; this hook only wires the browser APIs to it.
 */
import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react'

import { ApiError, audioSrc, resetCall, sendTurn } from '@/lib/api'
import { callReducer, initialCallState } from './call-state'
import {
  describeError,
  getRecognitionConstructor,
  isTransientError,
  readResults,
  type Recognition,
} from './speech-recognition'

function newSessionId(): string {
  return crypto.randomUUID()
}

/** Start (or restart) recognition in `lang`; starting twice is harmless. */
function startRecognition(recognition: Recognition, lang: string): void {
  recognition.lang = lang
  try {
    recognition.start()
  } catch {
    /* already started: InvalidStateError */
  }
}

function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong. Please try again.'
}

export interface VoiceCallOptions {
  /** BCP 47 language for recognition, e.g. 'en-IN' or 'hi-IN'. */
  lang: string
}

export function useVoiceCall({ lang }: VoiceCallOptions) {
  const [state, dispatch] = useReducer(callReducer, initialCallState)
  const supported = useMemo(() => getRecognitionConstructor() !== null, [])

  const sessionRef = useRef(newSessionId())
  const recognitionRef = useRef<Recognition | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  /** A voice call is running (mic comes back after each reply). */
  const voiceModeRef = useRef(false)
  /** The microphone should be on; onend restarts it while this is true. */
  const micWantedRef = useRef(false)
  const optionsRef = useRef({ lang })

  useEffect(() => {
    optionsRef.current = { lang }
  }, [lang])

  const stopListening = useCallback(() => {
    micWantedRef.current = false
    recognitionRef.current?.abort()
  }, [])

  const stopAudio = useCallback(() => {
    const audio = audioRef.current
    audioRef.current = null
    if (audio) {
      audio.onended = null
      audio.onerror = null
      audio.pause()
    }
  }, [])

  // Declared before use through a ref, because recognition handlers, replies and
  // audio callbacks all call back into each other.
  const handlersRef = useRef({
    startListening: () => {},
    onPatientSaid: (_text: string) => {},
  })

  const afterReply = useCallback(() => {
    if (voiceModeRef.current) handlersRef.current.startListening()
    else dispatch({ type: 'hang_up' })
  }, [])

  const playReply = useCallback(
    (audioUrl: string) => {
      stopAudio()
      const audio = new Audio(audioSrc(audioUrl))
      audioRef.current = audio
      const finished = () => {
        if (audioRef.current !== audio) return
        audioRef.current = null
        dispatch({ type: 'speech_finished' })
        afterReply()
      }
      audio.onended = finished
      audio.onerror = finished
      audio.play().catch(finished)
    },
    [afterReply, stopAudio],
  )

  const respond = useCallback(
    async (text: string) => {
      const session = sessionRef.current
      try {
        const result = await sendTurn({ session_id: session, message: text })
        if (session !== sessionRef.current) return // a new call started meanwhile
        // The server sends an audio link only when speech is configured.
        const speak = result.audio_url !== null
        dispatch({
          type: 'assistant_replied',
          text: result.reply,
          appointments: result.appointments,
          speak,
        })
        if (result.audio_url) playReply(result.audio_url)
        else afterReply()
      } catch (error) {
        if (session !== sessionRef.current) return
        voiceModeRef.current = false
        dispatch({ type: 'failed', message: messageOf(error) })
      }
    },
    [afterReply, playReply],
  )

  const startListening = useCallback(() => {
    const Ctor = getRecognitionConstructor()
    if (!Ctor) return
    let recognition = recognitionRef.current
    if (!recognition) {
      recognition = new Ctor()
      recognition.continuous = true
      recognition.interimResults = true
      recognition.onresult = (event) => {
        const { final, interim } = readResults(event)
        if (interim) dispatch({ type: 'interim', text: interim })
        if (final) handlersRef.current.onPatientSaid(final)
      }
      recognition.onerror = (event) => {
        if (isTransientError(event.error)) return // onend restarts it
        micWantedRef.current = false
        voiceModeRef.current = false
        dispatch({ type: 'failed', message: describeError(event.error) })
      }
      recognition.onend = () => {
        // Chrome ends recognition after a stretch of silence; keep listening.
        const current = recognitionRef.current
        if (micWantedRef.current && current) startRecognition(current, optionsRef.current.lang)
      }
      recognitionRef.current = recognition
    }
    micWantedRef.current = true
    dispatch({ type: 'listen' })
    startRecognition(recognition, optionsRef.current.lang)
  }, [])

  const onPatientSaid = useCallback(
    (text: string) => {
      stopListening()
      dispatch({ type: 'patient_said', text })
      if (text.trim()) void respond(text.trim())
      else afterReply()
    },
    [afterReply, respond, stopListening],
  )

  useEffect(() => {
    handlersRef.current = { startListening, onPatientSaid }
  }, [startListening, onPatientSaid])

  const startCall = useCallback(() => {
    voiceModeRef.current = true
    startListening()
  }, [startListening])

  const endCall = useCallback(() => {
    voiceModeRef.current = false
    stopListening()
    stopAudio()
    dispatch({ type: 'hang_up' })
  }, [stopAudio, stopListening])

  const newCall = useCallback(() => {
    endCall()
    const previous = sessionRef.current
    sessionRef.current = newSessionId()
    dispatch({ type: 'new_call' })
    resetCall(previous).catch(() => {
      /* the old conversation expires on its own */
    })
  }, [endCall])

  /** Typed input: works in any browser, and without a microphone. */
  const sendText = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return
      stopListening()
      stopAudio()
      dispatch({ type: 'patient_said', text: trimmed })
      void respond(trimmed)
    },
    [respond, stopAudio, stopListening],
  )

  useEffect(
    () => () => {
      micWantedRef.current = false
      recognitionRef.current?.abort()
      audioRef.current?.pause()
    },
    [],
  )

  return { state, supported, startCall, endCall, newCall, sendText }
}
