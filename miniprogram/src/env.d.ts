/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string
  readonly VITE_WECHAT_TEMPLATE_NEW_ORDER?: string
  readonly VITE_WECHAT_TEMPLATE_ORDER_ACCEPTED?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
