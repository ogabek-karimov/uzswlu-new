import { computed, reactive } from 'vue'
import { api, type User } from './api'

// Kirgan foydalanuvchi holati (butun ilova uchun bitta)
const state = reactive<{ user: User | null; checked: boolean }>({ user: null, checked: false })

export const auth = {
  state,
  user: computed(() => state.user),
  isSuper: computed(() => state.user?.role === 'superadmin'),

  /** Rolga shu bo'lim ruxsat etilganmi (superadmin — hammasi) */
  can(section: string, level: 'read' | 'write' = 'read') {
    const u = state.user
    if (!u) return false
    if (u.role === 'superadmin') return true
    const got = u.permissions?.[section]
    return level === 'read' ? !!got : got === 'write'
  },

  /** Kirgandan keyin tushadigan sahifa */
  homePath() {
    const order: [string, string][] = [['dashboard', '/'], ['news', '/postlar/news'], ['announcements', '/postlar/announcements'], ['events', '/postlar/events'], ['pages', '/sahifalar'], ['faculties', '/fakultetlar'], ['departments', '/kafedralar'], ['sdg', '/brm'], ['documents', '/hujjatlar'], ['videos', '/video'], ['quick-links', '/tezkor-xizmatlar'], ['leaders', '/rahbariyat'], ['staff', '/xodimlar'], ['media', '/media']]
    return order.find(([k]) => this.can(k))?.[1] ?? '/profil'
  },

  /** Sessiyani tekshirish (sahifa yangilanganda) */
  async me() {
    try {
      const res = await api.get<{ user: User | null }>('/users/me', { depth: 1 })
      state.user = res.user
    }
    catch {
      state.user = null
    }
    state.checked = true
    return state.user
  },

  /** Parol to'g'ri bo'lsa: foydalanuvchi, yoki 2FA yoqilgan bo'lsa — kod so'raladigan `challenge` */
  async login(username: string, password: string, remember: boolean): Promise<User | { challenge: string }> {
    const res = await api.post<{ user?: User; twoFactorRequired?: boolean; challenge?: string }>('/users/login', { username, password })
    try { localStorage.setItem('admin:remember', remember ? '1' : '0') }
    catch { /* brauzer xotirasi yopiq bo'lishi mumkin */ }
    if (res.twoFactorRequired && res.challenge) return { challenge: res.challenge }
    state.user = res.user!
    state.checked = true
    return res.user!
  },

  /** Kirishning 2-qadami: authenticator kodi yoki zaxira kod */
  async verifyTwoFactor(challenge: string, code: string) {
    const res = await api.post<{ user: User }>('/users/login/2fa', { challenge, code })
    state.user = res.user
    state.checked = true
    return res.user
  },

  async logout() {
    try { await api.post('/users/logout') }
    finally { state.user = null }
  },
}

export function roleLabel(u?: User | null) {
  return u?.roleName || u?.role || ''
}

export function initials(name?: string | null) {
  return (name ?? '?').split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]!.toUpperCase()).join('') || '?'
}
