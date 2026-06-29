import type { Citation, IngestResponse, SourceFragment, UploadFile } from './types'

// Relativo por defecto: las peticiones van al mismo origen que el frontend y el proxy de
// Vite las reenvía al backend (ver vite.config.ts). Evita CORS y los líos localhost↔::1.
// En producción, define VITE_API_BASE con la URL del backend.
const BASE = import.meta.env.VITE_API_BASE ?? '/api'

async function errorText(resp: Response): Promise<string> {
  try {
    const data = await resp.json()
    return typeof data?.detail === 'string' ? data.detail : resp.statusText
  } catch {
    return resp.statusText
  }
}

// Ficheros por petición. Lotes pequeños evitan el límite multipart del servidor y que
// el navegador (Safari) aborte peticiones enormes ("Load failed").
const UPLOAD_BATCH = 200

/** Sube ficheros (preservando su ruta relativa) y los indexa, en lotes. */
export async function ingestUpload(files: UploadFile[]): Promise<IngestResponse> {
  const total: IngestResponse = { files_indexed: 0, chunks_indexed: 0, skipped: 0, languages: {} }
  for (let i = 0; i < files.length; i += UPLOAD_BATCH) {
    const form = new FormData()
    for (const { path, file } of files.slice(i, i + UPLOAD_BATCH)) form.append('files', file, path)
    const resp = await fetch(`${BASE}/ingest/upload`, { method: 'POST', body: form })
    if (!resp.ok) throw new Error(await errorText(resp))
    const batch: IngestResponse = await resp.json()
    total.files_indexed += batch.files_indexed
    total.chunks_indexed += batch.chunks_indexed
    total.skipped += batch.skipped
    for (const [lang, n] of Object.entries(batch.languages)) {
      total.languages[lang] = (total.languages[lang] ?? 0) + n
    }
  }
  return total
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
