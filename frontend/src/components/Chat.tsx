import { type FormEvent, useEffect, useRef, useState } from 'react'
import type { ChatMessage } from '../lib/types'

interface Props {
  messages: ChatMessage[]
  busy: boolean
  onSend: (message: string) => void
}

export function Chat({ messages, busy, onSend }: Props) {
  const [input, setInput] = useState('')
  const threadRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight })
  }, [messages])

  function submit(event: FormEvent) {
    event.preventDefault()
    const text = input.trim()
    if (!text || busy) return
    onSend(text)
    setInput('')
  }

  return (
    <section className="chat">
      <div className="thread" ref={threadRef}>
        {messages.length === 0 && (
          <p className="empty">Indexa código y pregunta lo que quieras sobre él.</p>
        )}
        {messages.map((message, index) => {
          const streaming = busy && index === messages.length - 1
          return (
            <div key={index} className={`msg ${message.role}${message.error ? ' error' : ''}`}>
              <span className="role">{message.role === 'user' ? 'Tú' : 'Asistente'}</span>
              <div className="content">
                {message.content}
                {streaming && <span className="cursor" />}
              </div>
            </div>
          )
        })}
      </div>
      <form className="composer" onSubmit={submit}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Pregunta sobre el código…"
          aria-label="Pregunta"
        />
        <button type="submit" disabled={busy || input.trim() === ''}>
          Enviar
        </button>
      </form>
    </section>
  )
}
