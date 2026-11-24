import type { CabinetNotifications } from '#shared/types/api'

// Kabinet qo'ng'iroqchasi: xodimning o'z bildirishnomalari (foydalanuvchi backendda sessiyadan aniqlanadi). Keshlanmaydi.
// Kirmagan mehmon yoki xato — bo'sh ro'yxat (qo'ng'iroqcha jim turadi).
const NONE: CabinetNotifications = { unread: 0, docs: [], signedIn: false }

export default defineEventHandler(async (event): Promise<CabinetNotifications> => {
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) return NONE
  try {
    // Backend javob berdi — xodim kirgan: sarlavhadagi qo'ng'iroqcha ko'rinadi (mehmonda — yashirin)
    return { ...await backendUserFetch<CabinetNotifications>(event, '/me/notifications'), signedIn: true }
  }
  catch {
    return NONE
  }
})
