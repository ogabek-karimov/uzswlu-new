import type { Endpoint } from 'payload'
import { hemis, hemisFaculty } from '../hemis'
import { isEditor } from '../lib/access'
import { type I18n, type Lang, pick } from '../lib/i18n'
import { imageOf, json, langOf } from '../lib/public'
import { summary, visibleWhere } from './site'

// Fakultetlar, kafedralar va xodimlar: HEMIS ma'lumoti + admin panelda to'ldirilgan qism

type Doc = Record<string, any>
const tr = (value: I18n | null | undefined, lang: Lang) => pick(value, lang) ?? pick(value, 'uz')

/** GET /api/site/faculties?lang= — fakultetlar ro'yxati (admin tartibida) */
const faculties: Endpoint = {
  path: '/site/faculties',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const res = await req.payload.find({ collection: 'faculties', sort: 'order', limit: 100, depth: 1, overrideAccess: true })
    return json({
      items: (res.docs as Doc[]).map((f) => {
        const h = hemisFaculty(f.slug)
        return { id: String(f.id), slug: f.slug, name: tr(f.name, lang) ?? '', logo: imageOf(f.logo, 'thumb'), departments: h?.stats.departments ?? 0, programs: h?.stats.programs ?? 0 }
      }),
      summary: { faculties: res.docs.length, departments: hemis.summary.departments },
    })
  },
}

/** GET /api/site/faculties/:slug?lang= — fakultet sahifasi */
const faculty: Endpoint = {
  path: '/site/faculties/:slug',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const slug = String(req.routeParams?.slug ?? '')
    const [res, all] = await Promise.all([
      req.payload.find({ collection: 'faculties', where: { slug: { equals: slug } }, limit: 1, depth: 1, overrideAccess: true }),
      req.payload.find({ collection: 'faculties', sort: 'order', limit: 100, depth: 0, overrideAccess: true, select: { slug: true } }),
    ])
    const f = res.docs[0] as Doc | undefined
    if (!f) return json({ message: 'Not found' }, 404)
    const h = hemisFaculty(slug)
    const deptIds = h?.departments.map(d => d.id) ?? []
    const [depts, news] = await Promise.all([
      deptIds.length ? req.payload.find({ collection: 'departments', where: { hemisId: { in: deptIds } }, limit: 200, depth: 0, overrideAccess: true }) : { docs: [] },
      req.payload.find({ collection: 'posts', where: visibleWhere(lang, [{ type: { equals: 'news' } }]), sort: '-publishedAt', limit: 2, depth: 1, overrideAccess: true }),
    ])
    const own = new Map((depts.docs as Doc[]).map(d => [d.hemisId, d]))
    const contact = h?.contact[lang]
    return json({
      id: String(f.id),
      slug,
      name: tr(f.name, lang) ?? '',
      logo: imageOf(f.logo, 'thumb'),
      number: all.docs.findIndex(x => x.id === f.id) + 1,
      about: tr(f.about, lang) ?? h?.about[lang] ?? '',
      stats: h?.stats ?? { students: 0, departments: 0, programs: 0, teachers: 0 },
      dean: h?.dean[lang] ?? { name: '', role: '' },
      programs: h?.programs[lang] ?? [],
      departments: (h?.departments ?? []).map(d => ({ id: d.id, name: tr(own.get(d.id)?.name, lang) ?? d.name[lang], head: d.head })),
      deanery: h?.deanery[lang] ?? [],
      news: news.docs.map(d => summary(d, lang)),
      contact: {
        address: tr(f.address, lang) ?? contact?.address ?? '',
        phone: f.phone || contact?.phone || '',
        email: f.email || contact?.email || null,
        mapUrl: f.mapUrl || contact?.mapUrl || null,
      },
    })
  },
}

const SCIENCE: [field: string, network: string, url: (v: string) => string][] = [
  ['orcid', 'orcid', v => (/^https?:/.test(v) ? v : `https://orcid.org/${v}`)],
  ['scholar', 'scholar', v => v],
  ['scopus', 'scopus', v => (/^https?:/.test(v) ? v : `https://www.scopus.com/authid/detail.uri?authorId=${v}`)],
  ['researchgate', 'researchgate', v => v],
]

/** GET /api/site/staff/:id?lang= — admin to'ldirgan qism: bio, ilmiy profillar, yashirilganmi */
const staffOverlay: Endpoint = {
  path: '/site/staff/:id',
  method: 'get',
  handler: async (req) => {
    const lang = langOf(req)
    const res = await req.payload.find({ collection: 'staff-profiles', where: { hemisId: { equals: String(req.routeParams?.id ?? '') } }, limit: 1, depth: 0, overrideAccess: true })
    const p = res.docs[0] as Doc | undefined
    if (!p) return json({ hidden: false, about: null, science: [] })
    return json({
      hidden: !!p.hidden,
      about: tr(p.bio, lang),
      science: SCIENCE.filter(([f]) => p[f]?.trim()).map(([f, network, url]) => ({ network, url: url(p[f].trim()) })),
    })
  },
}

/** GET /api/site/staff-hidden — saytda yashirilgan xodimlar */
const staffHidden: Endpoint = {
  path: '/site/staff-hidden',
  method: 'get',
  handler: async (req) => {
    const res = await req.payload.find({ collection: 'staff-profiles', where: { hidden: { equals: true } }, pagination: false, depth: 0, overrideAccess: true, select: { hemisId: true } })
    return json({ ids: res.docs.map(d => (d as Doc).hemisId) })
  },
}

/** GET /api/panel/hemis — admin panel uchun HEMIS ma'lumoti (faqat o'qish) */
const panelHemis: Endpoint = {
  path: '/panel/hemis',
  method: 'get',
  handler: async (req) => {
    if (!isEditor(req.user as never)) return json({ message: 'Unauthorized' }, 401)
    return json({
      syncedAt: hemis.syncedAt,
      faculties: hemis.faculties.map(f => ({
        slug: f.slug,
        name: f.name.uz,
        stats: f.stats,
        dean: (f.dean.uz as { name?: string }).name ?? '',
        departments: f.departments.map(d => ({ id: d.id, name: d.name.uz, head: d.head })),
      })),
      staff: hemis.staff,
      staffDepartments: hemis.staffDepartments,
    })
  },
}

export const structureEndpoints: Endpoint[] = [faculties, faculty, staffOverlay, staffHidden, panelHemis]
