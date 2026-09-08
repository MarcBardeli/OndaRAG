import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/chat': 'http://127.0.0.1:8000',
      '/upload': 'http://127.0.0.1:8000',
      '/audio': 'http://127.0.0.1:8000',
      '/debug': 'http://127.0.0.1:8000',
    },
  },
});