import { onBeforeUnmount, reactive, watch, type WatchSource } from 'vue'
import type { Router } from 'vue-router'
import { api, setUnauthorizedHandler } from './api'
import { auth } from './auth'
import { onSessionExpired } from './session-policy'

// Sessiya tugashi (JWT 8 soat): tugagach har qanday so'rov 401 qaytaradi.
//  • Foydalanuvchi hech narsa yozmagan bo'lsa — darhol kirish sahifasiga (qaytgach shu sahifaga) yo'naltiramiz.
//  • Yozib turgan bo'lsa (saqlanmagan post, forma) — sahifa O'ZGARMAYDI: «Sessiya tugadi» oynasi chiqadi,
//    foydalanuvchi yangi oynada qayta kiradi va shu yerda «Saqlash»ni qayta bosadi. Yozganlari yo'qolmaydi.
export const session = reactive({
  expired: false,
  /** Saqlanmagan o'zgarishi bor sahifalar soni (trackUnsaved) */
  unsaved: 0,
  /** Foydalanuvchi shu sahifada biror maydonga yozgan (sahifa almashsa tozalanadi) */
  touched: false,
})

/** Sahifa saqlanmagan o'zgarishlarini bildiradi: sessiya tugasa u yo'qolmaydi, brauzerni yopishda ogohlantiriladi */
export function trackUnsaved(source: WatchSource<boolean>) {
  let counted = false
  const sync = (dirty: boolean) => {
    if (dirty && !counted) { session.unsaved++; counted = true }
    else if (!dirty && counted) { session.unsaved--; counted = false }
  }
  const warn = (e: BeforeUnloadEvent) => {
    if (!counted) return
    e.preventDefault()
    e.returnValue = ''
  }
  watch(source, sync, { immediate: true })
  window.addEventListener('beforeunload', warn)
  onBeforeUnmount(() => {
    window.removeEventListener('beforeunload', warn)
    sync(false)
  })
}

/** main.ts dan bir marta chaqiriladi */
export function installSessionGuards(router: Router) {
  document.addEventListener('input', () => { session.touched = true }, true)
  router.afterEach(() => { session.touched = false })

  setUnauthorizedHandler(() => {
    const action = onSessionExpired({ loggedIn: !!auth.state.user, expired: session.expired, unsaved: session.unsaved, touched: session.touched })
    if (action === 'modal') session.expired = true
    else if (action === 'redirect') {
      auth.state.user = null
      router.replace({ name: 'login', query: { r: router.currentRoute.value.fullPath, expired: '1' } })
    }
  })
}

/** Foydalanuvchi boshqa oynada qayta kirganmi — tekshirib, oynani yopadi. true — sessiya tiklandi */
export async function recheckSession(router: Router): Promise<boolean> {
  try {
    const res = await api.get<{ user: typeof auth.state.user }>('/users/me', { depth: 1 })
    if (!res.user) return false
    const sameUser = res.user.id === auth.state.user?.id
    auth.state.user = res.user
    session.expired = false
    if (!sameUser) await router.replace('/') // boshqa hisob bilan kirilgan: eski sahifa ruxsatlari mos kelmasligi mumkin
    return true
  }
  catch {
    return false
  }
}

/** «Hozir chiqish» — saqlanmagan o'zgarishlardan voz kechib kirish sahifasiga */
export function abandonSession(router: Router) {
  session.expired = false
  session.unsaved = 0
  auth.state.user = null
  router.replace({ name: 'login', query: { r: router.currentRoute.value.fullPath, expired: '1' } })
}
