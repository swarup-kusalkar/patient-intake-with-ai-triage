import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Dev server runs on port 3000 — matches CORS_ORIGINS_RAW in .env.example
    port: 3000,
    host: true, // Allow connections from outside the container (Docker)
    proxy: {
      // Proxy /api to the backend — avoids CORS in dev and mirrors nginx in prod.
      // This means the frontend never needs to know the backend URL directly;
      // all API calls are relative (/api/v1/...).
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
        // Fallback for local dev (outside Docker): override VITE_API_TARGET env var
        // e.g., VITE_API_TARGET=http://localhost:8000 npm run dev
        ...(process.env.VITE_API_TARGET
          ? { target: process.env.VITE_API_TARGET }
          : {}),
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable in prod to avoid exposing source
  },
})
