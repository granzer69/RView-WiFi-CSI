import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Cloud Agent + Cursor port-forward: HMR WebSockets often break the embedded browser (blank page).
const cursorPreview = process.env.RVIEW_CURSOR_PREVIEW === '1'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 43123,
    strictPort: true,
    open: false,
    // 0.0.0.0 so Cursor can detect and forward the port to the in-app browser.
    host: '0.0.0.0',
    allowedHosts: true,
    hmr: cursorPreview
      ? false
      : {
          host: '127.0.0.1',
          port: 43123,
          clientPort: 43123,
          protocol: 'ws',
        },
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:45231',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'http://127.0.0.1:45231',
        ws: true,
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 43123,
    strictPort: true,
    host: '0.0.0.0',
    open: false,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:45231',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ws': {
        target: 'http://127.0.0.1:45231',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
