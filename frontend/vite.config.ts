import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

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
    // Cursor forwards localhost:43123 on your machine → VM:43123; pin asset URLs to that origin.
    origin: 'http://127.0.0.1:43123',
    hmr: {
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
  },
})
