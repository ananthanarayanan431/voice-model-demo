import type { DoctorOut } from '@voiceagent/voice-agent-contracts'
import {
  CalendarCheck,
  Info,
  Loader,
  Mic,
  PhoneOff,
  RotateCcw,
  Send,
  Stethoscope,
  Volume2,
} from 'lucide-react'
import { useEffect, useRef, useState, type FormEvent } from 'react'

import { getDoctors, getReady } from '@/lib/api'
import { formatDay, formatTime } from '@/lib/format'
import type { CallStatus } from './call-state'
import { useVoiceCall } from './use-voice-call'

const LANGUAGES = [
  { code: 'en-IN', label: 'English (India)' },
  { code: 'hi-IN', label: 'हिन्दी' },
] as const

const STATUS_LABEL: Record<CallStatus, string> = {
  idle: 'Not in a call',
  listening: 'Listening…',
  thinking: 'Thinking…',
  speaking: 'Speaking…',
}

export function VoicePage() {
  const [lang, setLang] = useState<string>('en-IN')
  const [ttsReady, setTtsReady] = useState<boolean | null>(null)
  const [doctors, setDoctors] = useState<DoctorOut[]>([])
  const [typed, setTyped] = useState('')

  const { state, supported, startCall, endCall, newCall, sendText } = useVoiceCall({
    lang,
    speakReplies: ttsReady === true,
  })

  useEffect(() => {
    getReady()
      .then((ready) => setTtsReady(ready.tts_configured))
      .catch(() => setTtsReady(false))
    getDoctors()
      .then(setDoctors)
      .catch(() => setDoctors([]))
  }, [])

  const scrollRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [state.turns.length, state.interim])

  const inCall = state.status !== 'idle'

  function submitTyped(event: FormEvent) {
    event.preventDefault()
    sendText(typed)
    setTyped('')
  }

  return (
    <div className="bg-canvas text-ink min-h-dvh">
      <header className="border-line bg-surface border-b">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-4 py-3">
          <div className="bg-accent text-on-accent grid size-9 place-items-center rounded-xl">
            <Stethoscope aria-hidden className="size-5" />
          </div>
          <div className="min-w-0">
            <h1 className="text-base leading-tight font-semibold">Sunrise Hospitals</h1>
            <p className="text-muted text-sm">Patient assistant · appointments and medicines</p>
          </div>
          <span className="bg-warning-soft text-ink ml-auto rounded-full px-3 py-1 text-xs font-medium">
            Demo · sample data
          </span>
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl gap-4 px-4 py-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        <section
          aria-label="Call"
          className="border-line bg-surface flex min-h-[70dvh] flex-col rounded-2xl border"
        >
          <div
            ref={scrollRef}
            className="flex-1 space-y-3 overflow-y-auto p-4"
            aria-live="polite"
            aria-label="Transcript"
          >
            {state.turns.length === 0 && !state.interim ? (
              <EmptyState supported={supported} />
            ) : (
              state.turns.map((turn) => (
                <Bubble key={turn.id} speaker={turn.role}>
                  {turn.text}
                </Bubble>
              ))
            )}
            {state.interim ? (
              <Bubble speaker="patient" live>
                {state.interim}
              </Bubble>
            ) : null}
            {state.status === 'thinking' ? (
              <p className="text-muted flex items-center gap-2 text-sm">
                <Loader aria-hidden className="size-4 animate-spin" /> The assistant is thinking
              </p>
            ) : null}
          </div>

          {state.error ? (
            <p
              role="alert"
              className="bg-danger-soft text-danger mx-4 mb-3 rounded-lg px-3 py-2 text-sm"
            >
              {state.error}
            </p>
          ) : null}

          <div className="border-line flex flex-wrap items-center gap-3 border-t p-4">
            {supported ? (
              inCall ? (
                <button
                  type="button"
                  onClick={endCall}
                  className="bg-danger text-on-accent inline-flex items-center gap-2 rounded-full px-5 py-3 font-medium"
                >
                  <PhoneOff aria-hidden className="size-5" /> End call
                </button>
              ) : (
                <button
                  type="button"
                  onClick={startCall}
                  className="bg-accent hover:bg-accent-hover text-on-accent inline-flex items-center gap-2 rounded-full px-5 py-3 font-medium"
                >
                  <Mic aria-hidden className="size-5" /> Start call
                </button>
              )
            ) : null}

            <StatusPill status={state.status} />

            <label className="text-muted ml-auto flex items-center gap-2 text-sm">
              <span>Language</span>
              <select
                value={lang}
                onChange={(event) => setLang(event.target.value)}
                className="border-line bg-surface text-ink rounded-lg border px-2 py-1.5"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              onClick={newCall}
              className="border-line text-muted hover:text-ink inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm"
            >
              <RotateCcw aria-hidden className="size-4" /> New call
            </button>

            <form onSubmit={submitTyped} className="flex w-full gap-2">
              <label htmlFor="typed" className="sr-only">
                Type a message
              </label>
              <input
                id="typed"
                value={typed}
                onChange={(event) => setTyped(event.target.value)}
                placeholder={supported ? 'Or type instead…' : 'Type your message…'}
                maxLength={1000}
                className="border-line bg-canvas text-ink placeholder:text-muted min-w-0 flex-1 rounded-lg border px-3 py-2"
              />
              <button
                type="submit"
                disabled={!typed.trim() || state.status === 'thinking'}
                className="bg-ink text-canvas inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium disabled:opacity-40"
              >
                <Send aria-hidden className="size-4" /> Send
              </button>
            </form>
          </div>
        </section>

        <aside className="space-y-4">
          <Panel
            title="Booked on this call"
            icon={<CalendarCheck aria-hidden className="size-4" />}
          >
            {state.appointments.length === 0 ? (
              <p className="text-muted text-sm">Appointments you book appear here.</p>
            ) : (
              <ul className="space-y-2">
                {state.appointments.map((a) => (
                  <li key={a.id} className="bg-positive-soft rounded-lg px-3 py-2 text-sm">
                    <p className="font-medium">
                      {a.doctor_name} · {a.specialty}
                    </p>
                    <p>
                      {formatDay(a.day)}, {formatTime(a.start)} · {a.patient_name}
                    </p>
                    <p className="text-muted text-xs">Booking id {a.id}</p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel title="Doctors" icon={<Stethoscope aria-hidden className="size-4" />}>
            <ul className="space-y-2 text-sm">
              {doctors.map((d) => (
                <li key={d.id}>
                  <p className="font-medium">{d.name}</p>
                  <p className="text-muted">
                    {d.specialty} · {d.days.join(', ')} · {d.hours}
                  </p>
                </li>
              ))}
            </ul>
          </Panel>

          <Panel title="Good to know" icon={<Info aria-hidden className="size-4" />}>
            <ul className="text-muted list-disc space-y-1.5 pl-4 text-sm">
              {ttsReady === false ? (
                <li>
                  Voice replies are off: add <code>VARTALOOP_API_KEY</code> to{' '}
                  <code>agents/voice_agent/.env</code>. Replies still show as text.
                </li>
              ) : (
                <li className="flex items-start gap-1.5 [list-style:none] -ml-4">
                  <Volume2 aria-hidden className="mt-0.5 size-4 shrink-0" /> Replies are spoken with
                  Vartaloop.
                </li>
              )}
              {!supported ? (
                <li>
                  This browser has no speech recognition. Use Chrome or Edge to talk, or type.
                </li>
              ) : (
                <li>
                  Live transcription uses the browser&rsquo;s speech recognition (Chrome, Edge).
                </li>
              )}
              <li>Try a sample patient: phone 9876543210 or 9123456780.</li>
              <li>The assistant never gives medical advice; emergencies go to 108.</li>
            </ul>
          </Panel>
        </aside>
      </main>
    </div>
  )
}

function EmptyState({ supported }: { supported: boolean }) {
  return (
    <div className="text-muted mx-auto max-w-md py-16 text-center">
      <p className="text-ink text-lg font-medium">Talk to the Sunrise patient assistant</p>
      <p className="mt-2 text-sm">
        {supported ? 'Press Start call and say something like' : 'Type something like'} &ldquo;I
        want to see a bone doctor on Monday&rdquo; or &ldquo;When should I take my medicines?&rdquo;
      </p>
    </div>
  )
}

function Bubble({
  speaker,
  live = false,
  children,
}: {
  speaker: 'patient' | 'assistant'
  live?: boolean
  children: string
}) {
  const mine = speaker === 'patient'
  return (
    <div className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          mine ? 'bg-patient rounded-br-md' : 'bg-raised rounded-bl-md'
        } ${live ? 'italic opacity-70' : ''}`}
        data-live={live || undefined}
      >
        <p className="text-muted mb-0.5 text-xs font-medium">
          {mine ? (live ? 'You (speaking…)' : 'You') : 'Assistant'}
        </p>
        <p className="leading-relaxed whitespace-pre-wrap">{children}</p>
      </div>
    </div>
  )
}

function StatusPill({ status }: { status: CallStatus }) {
  return (
    <span className="text-muted inline-flex items-center gap-2 text-sm" role="status">
      <span
        aria-hidden
        className={`size-2.5 rounded-full ${
          status === 'listening'
            ? 'bg-accent listening-ring'
            : status === 'speaking'
              ? 'bg-positive'
              : status === 'thinking'
                ? 'bg-muted animate-pulse'
                : 'bg-line'
        }`}
      />
      {STATUS_LABEL[status]}
    </span>
  )
}

function Panel({
  title,
  icon,
  children,
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section className="border-line bg-surface rounded-2xl border p-4">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
        {icon}
        {title}
      </h2>
      {children}
    </section>
  )
}
