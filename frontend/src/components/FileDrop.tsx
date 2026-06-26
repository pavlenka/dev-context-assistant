import { type ChangeEvent, type DragEvent, useState } from 'react'
import { ingestUpload, isCodeFile } from '../lib/api'
import type { IngestResponse, UploadFile } from '../lib/types'

function readEntries(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
  return new Promise((resolve, reject) => reader.readEntries(resolve, reject))
}

async function readAllEntries(reader: FileSystemDirectoryReader): Promise<FileSystemEntry[]> {
  const all: FileSystemEntry[] = []
  for (;;) {
    const batch = await readEntries(reader)
    if (batch.length === 0) break
    all.push(...batch)
  }
  return all
}

function entryToFile(entry: FileSystemFileEntry): Promise<File> {
  return new Promise((resolve, reject) => entry.file(resolve, reject))
}

async function walk(entry: FileSystemEntry, prefix: string, out: UploadFile[]): Promise<void> {
  if (entry.isFile) {
    const file = await entryToFile(entry as FileSystemFileEntry)
    if (isCodeFile(file.name)) out.push({ path: prefix + entry.name, file })
  } else if (entry.isDirectory) {
    const reader = (entry as FileSystemDirectoryEntry).createReader()
    for (const child of await readAllEntries(reader)) {
      await walk(child, `${prefix}${entry.name}/`, out)
    }
  }
}

async function gatherFromDrop(dt: DataTransfer): Promise<UploadFile[]> {
  const entries = Array.from(dt.items)
    .map((item) => item.webkitGetAsEntry?.())
    .filter((entry): entry is FileSystemEntry => entry != null)
  if (entries.length > 0) {
    const out: UploadFile[] = []
    for (const entry of entries) await walk(entry, '', out)
    return out
  }
  return Array.from(dt.files)
    .filter((file) => isCodeFile(file.name))
    .map((file) => ({ path: file.name, file }))
}

function gatherFromInput(files: FileList): UploadFile[] {
  return Array.from(files)
    .filter((file) => isCodeFile(file.name))
    .map((file) => ({ path: file.webkitRelativePath || file.name, file }))
}

interface Props {
  onIndexed: (result: IngestResponse) => void
}

export function FileDrop({ onIndexed }: Props) {
  const [busy, setBusy] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [stats, setStats] = useState<IngestResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function upload(files: UploadFile[]) {
    if (files.length === 0) {
      setError('No se encontraron ficheros de código.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const result = await ingestUpload(files)
      setStats(result)
      onIndexed(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al indexar.')
    } finally {
      setBusy(false)
    }
  }

  async function onDrop(event: DragEvent) {
    event.preventDefault()
    setDragging(false)
    await upload(await gatherFromDrop(event.dataTransfer))
  }

  function onPick(event: ChangeEvent<HTMLInputElement>) {
    if (event.target.files) void upload(gatherFromInput(event.target.files))
  }

  return (
    <aside className="filedrop">
      <h2>Código</h2>
      <div
        className={`dropzone${dragging ? ' over' : ''}`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        {busy ? (
          <p>Indexando…</p>
        ) : (
          <>
            <p>Arrastra una carpeta o ficheros de código</p>
            <label className="pick">
              o selecciona una carpeta
              <input type="file" multiple webkitdirectory="" onChange={onPick} hidden />
            </label>
          </>
        )}
      </div>
      {error && <p className="error">{error}</p>}
      {stats && (
        <dl className="stats">
          <div>
            <dt>Ficheros</dt>
            <dd>{stats.files_indexed}</dd>
          </div>
          <div>
            <dt>Chunks</dt>
            <dd>{stats.chunks_indexed}</dd>
          </div>
          <div>
            <dt>Lenguajes</dt>
            <dd>{Object.keys(stats.languages).join(', ') || '—'}</dd>
          </div>
        </dl>
      )}
    </aside>
  )
}
