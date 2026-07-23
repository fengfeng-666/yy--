import { defineConfig, loadEnv } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig(({ command, mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  if (command === 'build' && mode === 'production') {
    const required = [
      'VITE_API_BASE_URL',
      'VITE_WECHAT_TEMPLATE_NEW_ORDER',
      'VITE_WECHAT_TEMPLATE_ORDER_ACCEPTED',
    ]
    const missing = required.filter((key) => !env[key]?.trim())
    if (missing.length) {
      throw new Error(`小程序生产构建缺少环境变量：${missing.join(', ')}`)
    }
    if (!env.VITE_API_BASE_URL.startsWith('https://')) {
      throw new Error('VITE_API_BASE_URL 必须使用 HTTPS')
    }
  }

  return { plugins: [uni()] }
})
