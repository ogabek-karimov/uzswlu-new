import type { CabinetTasks } from '#shared/types/api'

// Xodim vazifalari (o'zimga berilgan, men bergan, kimga bera olaman). Shaxsiy — kesh yo'q.
export default defineEventHandler(async (event): Promise<CabinetTasks> => {
  const { apiBase } = useRuntimeConfig(event)
  if (!apiBase) return { mine: [], given: [], assignees: [] }
  return backendUserFetch<CabinetTasks>(event, '/me/tasks')
})
