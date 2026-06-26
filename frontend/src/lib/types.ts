export interface IngestResponse {
  files_indexed: number
  chunks_indexed: number
  skipped: number
  languages: Record<string, number>
}

export interface Citation {
  path: string
  start_line: number
  end_line: number
}

export interface SourceFragment {
  path: string
  start: number
  end: number
  content: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  error?: boolean
}

export interface UploadFile {
  path: string
  file: File
}
