// O'z suratini olib tashlash — sayt yana HEMIS suratini ko'rsatadi
export default defineEventHandler(async (event) => {
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) {
    setMockPhoto(null)
    return { ok: true }
  }
  return backendUserFetch(event, '/me/avatar', { method: 'DELETE' })
})
