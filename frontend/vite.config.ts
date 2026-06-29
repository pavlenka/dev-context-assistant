import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Proxy de desarrollo: el navegador solo habla con el dev server (mismo origen) y Vite
// reenvía /api/* al backend por IPv4 desde Node. Evita los líos de localhost↔::1 (IPv6)
// y el CORS al subir/chatear. En producción se usa VITE_API_BASE con la URL real.
// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
