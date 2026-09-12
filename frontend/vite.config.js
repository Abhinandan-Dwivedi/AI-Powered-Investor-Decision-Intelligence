import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins:  [react(), tailwindcss()],

  server: {
    port: 5173,
    // Proxy API calls to FastAPI during development so the frontend
    // can call relative paths ("/api/chat") without hardcoding
    // http://localhost:8000 everywhere or fighting CORS in dev.
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
})
