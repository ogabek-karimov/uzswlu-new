import type { CabinetDocument } from '#shared/types/api'

// Bo'limdagi yuklangan hujjatlar (yuklash oynasidagi "Yuklanganlar" ro'yxati), yangisi birinchi
export default defineEventHandler(async (event): Promise<CabinetDocument[]> => {
  const section = readDocSection(getRouterParam(event, 'section'))
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) return listMockDocs(section)
  return backendUserFetch<CabinetDocument[]>(event, `/me/documents/${section}`)
})
