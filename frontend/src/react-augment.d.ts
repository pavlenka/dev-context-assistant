import 'react'

// Atributos no estándar para seleccionar carpetas en el input de ficheros.
declare module 'react' {
  interface InputHTMLAttributes<T> {
    webkitdirectory?: string
    directory?: string
  }
}
