import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import Inspector from 'unplugin-vue-dev-locator/vite'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: '0.0.0.0',
    port: 5174,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',
        // 保留浏览器的 Host，让后端正确识别同源请求，避免 POST 被 CORS 拒绝。
        changeOrigin: false,
      },
      '/uploads': {
        target: 'http://127.0.0.1:8001',
        changeOrigin: false,
      },
    },
  },
  build: {
    sourcemap: false,
  },
  test: {
    setupFiles: ['./src/test/setup.ts'],
    clearMocks: true,
    restoreMocks: true,
  },
  plugins: [
    vue(),
    Inspector(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'), // ✅ 定义 @ = src
    },
  },
})
