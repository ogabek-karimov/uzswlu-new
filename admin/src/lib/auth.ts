import { computed, reactive } from 'vue'
import { api, type User } from './api'

// Kirgan foydalanuvchi holati (butun ilova uchun bitta)
const state = reactive<{ user: User | null; checked: boolean }>({ user: null, checked: false })

export const auth = {
  state,
  user: computed(() => state.user),
  isSuper: computed(() => state.user?.role === 'superadmin'),

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

  async login(username: string, password: string, remember: boolean) {
    const res = await api.post<{ user: User }>('/users/login', { username, password })
    state.user = res.user
    state.checked = true
    try { localStorage.setItem('admin:remember', remember ? '1' : '0') }
    catch { /* brauzer xotirasi yopiq bo'lishi mumkin */ }
    return res.user
  },

  async logout() {
    try { await api.post('/users/logout') }
    finally { state.user = null }
  },
}

export const ROLE_LABELS: Record<User['role'], string> = {
  superadmin: 'Superadmin',
  editor: 'Kontent muharriri',
  faculty: 'Fakultet admini',
  pages: 'Sahifalar muharriri',
  sdg: 'BRM menejeri',
}

export function initials(name?: string | null) {
  return (name ?? '?').split(/\s+/).filter(Boolean).slice(0, 2).map(w => w[0]!.toUpperCase()).join('') || '?'
}
