import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// El frontend se sirve desde el mismo origen que la API (FastAPI). En desarrollo,
// Vite redirige /api al servidor local de uvicorn.
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  build: { chunkSizeWarningLimit: 1200 },
});
