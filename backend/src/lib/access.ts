import type { Access, PayloadRequest } from 'payload'

export type Role = 'superadmin' | 'editor' | 'faculty' | 'pages' | 'sdg'

type MaybeUser = { id?: number | string; role?: string | null; status?: string | null } | null | undefined

export const roleOf = (user: MaybeUser): Role | null => (user?.role as Role) ?? null

export const isSuper = (user: MaybeUser) => user?.role === 'superadmin'

/** Kontent bilan işlaydigan barça faol adminlar */
export const isEditor = (user: MaybeUser) =>
  !!user && user.status !== 'disabled' && ['superadmin', 'editor', 'faculty', 'pages'].includes(user.role ?? '')

/** Media (rasm, PDF) yuklay oladiganlar: kontent bilan ishlaydigan adminlar va BRM menejeri */
export const canUseMedia = (user: MaybeUser) => isEditor(user) || (!!user && user.status !== 'disabled' && user.role === 'sdg')

/** BRM sahifalarini tahrirlay oladiganlar: superadmin va BRM menejeri */
export const isSdgManager = (user: MaybeUser) => isSuper(user) || (!!user && user.status !== 'disabled' && user.role === 'sdg')

export const loggedIn: Access = ({ req }) => !!req.user
export const superOnly: Access = ({ req }) => isSuper(req.user as MaybeUser)
export const editorsOnly: Access = ({ req }) => isEditor(req.user as MaybeUser)
export const mediaUsers: Access = ({ req }) => canUseMedia(req.user as MaybeUser)
export const sdgManagers: Access = ({ req }) => isSdgManager(req.user as MaybeUser)

/** Superadmin — hammasi, qolganlar — faqat özi */
export const superOrSelf: Access = ({ req }) => {
  const user = req.user as MaybeUser
  if (!user) return false
  if (isSuper(user)) return true
  return { id: { equals: user.id } }
}

export const userOf = (req: PayloadRequest) => req.user as (MaybeUser & { name?: string | null; username?: string | null }) | null
