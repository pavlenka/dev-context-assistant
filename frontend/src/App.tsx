import { useRef, useState } from 'react'
import { Chat } from './components/Chat'
import { Citations } from './components/Citations'
import { FileDrop } from './components/FileDrop'
import { streamChat } from './lib/api'
import type { ChatMessage, Citation } from './lib/types'
import './App.css'

function updateLast(messages: ChatMessage[], patch: Partial<ChatMessage>): ChatMessage[] {
  const next = [...messages]
  next[next.length - 1] = { ...next[next.length - 1], ...patch }
  return next
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [busy, setBusy] = useState(false)
  const [citations, setCitations] = useState<Citation[]>([])
  const sessionId = useRef<string>(crypto.randomUUID())

  function handleSend(message: string) {
    setBusy(true)
    setCitations([])
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: message },
      { role: 'assistant', content: '' },
    ])

    void streamChat(message, sessionId.current, {
      onToken: (text) =>
        setMessages((prev) => updateLast(prev, { content: prev[prev.length - 1].content + text })),
      onDone: (sid, cites) => {
        sessionId.current = sid
        setCitations(cites)
        setMessages((prev) => updateLast(prev, { citations: cites }))
        setBusy(false)
      },
      onError: (detail) => {
        setMessages((prev) => updateLast(prev, { content: `Error: ${detail}`, error: true }))
        setBusy(false)
      },
    })
  }

  return (
    <div className="app">
      <header className="topbar">
        <h1>Dev Context Assistant</h1>
        <p>RAG sobre tu código, con citas verificables al fichero y línea.</p>
      </header>
      <main className="layout">
        <FileDrop onIndexed={() => undefined} />
        <Chat messages={messages} busy={busy} onSend={handleSend} />
        <Citations citations={citations} />
      </main>
    </div>
  )
}
