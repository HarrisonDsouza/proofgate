import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// The API (make dev) runs on :8080. The UI runs on :4200 and proxies API paths to it, so the browser sees one origin.
const api = 'http://localhost:8080'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 4200,
    strictPort: true,
    proxy: { '/api': api, '/target': api, '/rules': api, '/metrics': api },
  },
})
