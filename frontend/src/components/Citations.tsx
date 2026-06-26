import { useState } from 'react'
import { fetchSource } from '../lib/api'
import type { Citation, SourceFragment } from '../lib/types'

interface Props {
  citations: Citation[]
}

export function Citations({ citations }: Props) {
  const [fragment, setFragment] = useState<SourceFragment | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function open(citation: Citation) {
    setLoading(true)
    setError(null)
    setFragment(null)
    try {
      setFragment(await fetchSource(citation.path, citation.start_line, citation.end_line))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo leer el fragmento.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <aside className="citations">
      <h2>Citas</h2>
      {citations.length === 0 && (
        <p className="empty">Las fuentes citadas aparecerán aquí.</p>
      )}
      <ul>
        {citations.map((citation, index) => (
          <li key={index}>
            <button type="button" onClick={() => open(citation)}>
              {citation.path}:{citation.start_line}-{citation.end_line}
            </button>
          </li>
        ))}
      </ul>
      {loading && <p className="hint">Cargando fragmento…</p>}
      {error && <p className="error">{error}</p>}
      {fragment && (
        <figure className="fragment">
          <figcaption>
            {fragment.path}:{fragment.start}-{fragment.end}
          </figcaption>
          <pre>{fragment.content}</pre>
        </figure>
      )}
    </aside>
  )
}
