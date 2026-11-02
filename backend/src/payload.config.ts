import { postgresAdapter } from '@payloadcms/db-postgres'
import { lexicalEditor } from '@payloadcms/richtext-lexical'
import path from 'path'
import { type AfterErrorHook, buildConfig } from 'payload'
import sharp from 'sharp'
import { fileURLToPath } from 'url'

import { Activity } from './collections/Activity'
import { Categories } from './collections/Categories'
import { DocCategories, Documents } from './collections/Documents'
import { Leaders } from './collections/Leaders'
import { LoginEvents } from './collections/LoginEvents'
import { Media } from './collections/Media'
import { Pages } from './collections/Pages'
import { Posts } from './collections/Posts'
import { SdgGoals, SdgPage } from './collections/Sdg'
import { Slides } from './collections/Slides'
import { Departments, Faculties, StaffProfiles } from './collections/Structure'
import { Users } from './collections/Users'
import { VideoCategories, VideoPage, Videos } from './collections/Videos'
import { analyticsEndpoints } from './endpoints/analytics'
import { contentEndpoints } from './endpoints/content'
import { mediaEndpoints } from './endpoints/media'
import { pageEndpoints } from './endpoints/pages'
import { panelEndpoints } from './endpoints/panel'
import { siteEndpoints } from './endpoints/site'
import { sdgEndpoints } from './endpoints/sdg'
import { structureEndpoints } from './endpoints/structure'
import { Settings } from './globals/Settings'
import { Symbols } from './globals/Symbols'
import { ensureAnalyticsTable } from './lib/analytics'
import { requestInfo } from './lib/request'
import { seed } from './seed'

const filename = fileURLToPath(import.meta.url)
const dirname = path.dirname(filename)

// Admin panel (Vue) va sayt manzillari — cookie bilan so'rovlarga ruxsat
const origins = [process.env.PUBLIC_SERVER_URL, ...(process.env.TRUSTED_ORIGINS ?? '').split(',')]
  .map(o => o?.trim())
  .filter((o): o is string => !!o)

// Xato login urinishlarini kirish tarixiga yozish (to'g'ri kirish Users.afterLogin'da)
const recordFailedLogin: AfterErrorHook = async ({ error, req }) => {
  try {
    if (!req?.url || !new URL(req.url, 'http://localhost').pathname.endsWith('/api/users/login')) return
    const status = (error as { status?: number }).status
    const body = (req.data ?? {}) as { username?: string; email?: string }
    await req.payload.create({
      collection: 'login-events',
      overrideAccess: true,
      data: {
        username: String(body.username ?? body.email ?? '').slice(0, 100),
        method: 'password',
        result: status === 423 ? 'locked' : status === 403 ? 'denied' : 'bad_password',
        ...requestInfo(req),
      },
    })
  }
  catch {
    // jurnalga yozilmasa ham javob o'zgarmaydi
  }
}

export default buildConfig({
  serverURL: process.env.PUBLIC_SERVER_URL || undefined,
  admin: {
    user: Users.slug,
    meta: { titleSuffix: ' — ÖzDJTU' },
    importMap: { baseDir: path.resolve(dirname) },
  },
  collections: [Users, Media, Categories, Posts, Slides, Leaders, DocCategories, Documents, VideoCategories, Videos, Faculties, Departments, StaffProfiles, SdgGoals, Pages, LoginEvents, Activity],
  globals: [Settings, VideoPage, Symbols, SdgPage],
  endpoints: [...siteEndpoints, ...contentEndpoints, ...panelEndpoints, ...mediaEndpoints, ...structureEndpoints, ...sdgEndpoints, ...pageEndpoints, ...analyticsEndpoints],
  cors: origins,
  csrf: origins,
  editor: lexicalEditor(),
  secret: process.env.PAYLOAD_SECRET || '',
  typescript: { outputFile: path.resolve(dirname, 'payload-types.ts') },
  db: postgresAdapter({ pool: { connectionString: process.env.DATABASE_URL || '' } }),
  sharp,
  upload: { limits: { fileSize: 50 * 1024 * 1024 } },
  hooks: { afterError: [recordFailedLogin] },
  onInit: async (payload) => {
    await ensureAnalyticsTable(payload)
    await seed(payload)
  },
})
