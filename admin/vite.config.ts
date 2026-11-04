import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'

// Backend (Django/DRF) manzili. Admin bilan bitta manzildan ishlashi uchun /api proxy orqali o'tadi
// (sessiya cookie'si uchun muhim). Serverda bu ishni nginx bajaradi.
const backend = process.env.BACKEND_URL ?? 'http://localhost:8000'
const port = Number(process.env.ADMIN_PORT ?? 5173)

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port,
    strictPort: true,
    proxy: {
      '/api': { target: backend, changeOrigin: true, xfwd: true },
    },
  },
})
