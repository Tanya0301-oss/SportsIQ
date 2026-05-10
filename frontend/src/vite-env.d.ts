/// <reference types="vite/client" />

declare module "*.module.css" {
  const content: { [key: string]: string }
  export default content
}

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_WS_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
