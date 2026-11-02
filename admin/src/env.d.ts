/// <reference types="vite/client" />

import 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    public?: boolean
    superOnly?: boolean
  }
}

interface ImportMetaEnv {
  readonly VITE_SITE_URL?: string
}
