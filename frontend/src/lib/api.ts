import type { Citation, IngestResponse, SourceFragment, UploadFile } from './types'

// 127.0.0.1 explícito (no "localhost"): en macOS "localhost" resuelve primero a ::1
// (IPv6) y el backend escucha en IPv4, lo que provoca "Load failed" en Safari/WebKit.
const BASE = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

async function errorText(resp: Response): Promise<string> {
  try {
    const data = await resp.json()
    return typeof data?.detail === 'string' ? data.detail : resp.statusText
  } catch {
    return resp.statusText
  }
}

/** Sube ficheros (preservando su ruta relativa) y los indexa. */
export async function ingestUpload(files: UploadFile[]): Promise<IngestResponse> {
  const form = new FormData()
  for (const { path, file } of files) form.append('files', file, path)
  const resp = await fetch(`${BASE}/ingest/upload`, { method: 'POST', body: form })
  if (!resp.ok) throw new Error(await errorText(resp))
  return resp.json()
}

/** Devuelve el fragmento exacto de un fichero indexado (panel de citas). */
export async function fetchSource(path: string, start: number, end: number): Promise<SourceFragment> {
  const params = new URLSearchParams({ path, start: String(start), end: String(end) })
  const resp = await fetch(`${BASE}/source?${params.toString()}`)
  if (!resp.ok) throw new Error(await errorText(resp))
  return resp.json()
}

export interface ChatHandlers {
  onToken: (text: string) => void
  onDone: (sessionId: string, citations: Citation[]) => void
  onError: (detail: string) => void
}

/** Envía una pregunta y consume la respuesta en streaming (SSE sobre fetch). */
export async function streamChat(
  message: string,
  sessionId: string | null,
  handlers: ChatHandlers,
): Promise<void> {
  const resp = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!resp.ok || !resp.body) {
    handlers.onError(await errorText(resp))
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() ?? ''
    for (const block of blocks) {
      const line = block.trim()
      if (!line.startsWith('data:')) continue
      const event = JSON.parse(line.slice('data:'.length).trim())
      if (event.type === 'token') handlers.onToken(event.content)
      else if (event.type === 'done') handlers.onDone(event.session_id, event.citations ?? [])
      else if (event.type === 'error') handlers.onError(event.detail)
    }
  }
}

/** Extensiones de código que el backend sabe indexar. */
export const CODE_EXTENSIONS = ['.py', '.pyi', '.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx']

export function isCodeFile(name: string): boolean {
  return CODE_EXTENSIONS.some((ext) => name.toLowerCase().endsWith(ext))
}
