import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

// Backend (Payload) manzili. Admin bilan bitta manzildan ishlashi uchun /api proxy orqali o'tadi
// (cookie va CSRF uchun muhim). Serverda bu ishni nginx bajaradi.
const backend = process.env.BACKEND_URL ?? 'http://localhost:3001'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/api': { target: backend, changeOrigin: true, xfwd: true },
    },
  },
})
