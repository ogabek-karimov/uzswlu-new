import path from 'path'
import type { Payload } from 'payload'
import { fileURLToPath } from 'url'
import data from './content-seed.json' with { type: 'json' }
import { hemis } from '../hemis'
import sdg from './sdg-seed.json' with { type: 'json' }

// Saytdagi hozirgi ma'lumotlar (frontend mock'laridan): karusel, rektorat, hujjatlar, video toifalari, ramzlar.
// Har bir kolleksiya faqat bo'sh bo'lsa to'ldiriladi.

type L = { uz: string; ru: string; en: string; zh: string }
const ctx = { seed: true }
const dir = path.dirname(fileURLToPath(import.meta.url))

type Folder = 'posts' | 'carousel' | 'docs' | 'staff' | 'logos' | 'audio'

async function upload(payload: Payload, file: string, folder: Folder, alt?: L) {
  const doc = await payload.create({ collection: 'media', overrideAccess: true, context: ctx, filePath: path.join(dir, 'files', file), data: { folder, alt } })
  return doc.id as number
}

const isEmpty = async (payload: Payload, collection: 'slides' | 'leaders' | 'doc-categories' | 'video-categories' | 'faculties' | 'sdg-goals') =>
  !(await payload.count({ collection, overrideAccess: true })).totalDocs

export async function seedContent(payload: Payload) {
  if (await isEmpty(payload, 'slides')) {
    for (const [i, s] of (data.slides as { image: string; alt: L }[]).entries()) {
      const file = path.basename(s.image)
      const image = await upload(payload, file, 'carousel', s.alt)
      await payload.create({ collection: 'slides', overrideAccess: true, context: ctx, data: { name: s.alt.uz.slice(0, 60), image, alt: s.alt, order: i + 1 } })
    }
    payload.logger.info('Karusel yuklandi')
  }

  if (await isEmpty(payload, 'leaders')) {
    type Leader = { kind: string; staffId?: string | null; name: string; role: L; hours?: L; phone?: string | null; ext?: string | null; email?: string | null }
    for (const [i, l] of (data.leaders as Leader[]).entries()) {
      await payload.create({
        collection: 'leaders',
        overrideAccess: true,
        context: ctx,
        data: { kind: l.kind as 'rector', name: l.name, staffId: l.staffId ?? undefined, role: l.role, hours: l.hours, phone: l.phone ?? undefined, ext: l.ext ?? undefined, email: l.email ?? undefined, reception: l.kind !== 'press', order: i + 1 },
      })
    }
    payload.logger.info('Rektorat yuklandi')
  }

  if (await isEmpty(payload, 'doc-categories')) {
    const ids: Record<string, number> = {}
    for (const [i, [key, title]] of Object.entries(data.docCategories as Record<string, L>).entries()) {
      ids[key] = (await payload.create({ collection: 'doc-categories', overrideAccess: true, context: ctx, data: { title, order: i + 1 } })).id as number
    }
    // PDF fayllar hali yuklanmagan — eski saytdagi sahifaga havola bo'lib turadi (admin PDF yuklaguncha)
    for (const [i, d] of (data.docs as { category: string; title: L; url: string }[]).entries()) {
      await payload.create({ collection: 'documents', overrideAccess: true, context: ctx, data: { title: d.title, category: ids[d.category]!, url: d.url, display: 'open', pages: ['meyoriy-hujjatlar'], order: i + 1 } })
    }
    payload.logger.info('Hujjatlar yuklandi')
  }

  if (await isEmpty(payload, 'video-categories')) {
    const ids: Record<string, number> = {}
    for (const [i, c] of (data.videoCategories as { id: string; greeting: string; title: L }[]).entries()) {
      ids[c.id] = (await payload.create({ collection: 'video-categories', overrideAccess: true, context: ctx, data: { key: c.id, title: c.title, greeting: c.greeting, order: i + 1 } })).id as number
    }
    // Darslar — NAMUNA (kanalga havola); admin haqiqiy YouTube videolari bilan almashtiradi
    for (const [i, v] of (data.lessons as { cat: string; title: L }[]).entries()) {
      await payload.create({ collection: 'videos', overrideAccess: true, context: ctx, data: { url: data.channel, title: v.title, category: ids[v.cat]!, order: i + 1 } })
    }
    await payload.updateGlobal({ slug: 'video-page', overrideAccess: true, context: ctx, data: { channelUrl: data.channel, liveUrl: `${data.channel}/live` } })
    payload.logger.info('Video darsliklar yuklandi')
  }

  // Fakultetlar: nomi va logosi (matn va aloqa bo'sh — saytda HEMIS/namuna ma'lumoti ko'rinadi)
  if (await isEmpty(payload, 'faculties')) {
    for (const f of hemis.faculties) {
      const logo = f.logo ? await upload(payload, `faculties/${path.basename(f.logo)}`, 'logos', f.name) : undefined
      await payload.create({ collection: 'faculties', overrideAccess: true, context: ctx, data: { slug: f.slug, name: f.name, logo, order: f.order } })
    }
    payload.logger.info('Fakultetlar yuklandi')
  }

  // BRM: 17 maqsad (nomlari, tavsifi, THE Impact natijasi, BRM 6 bo'limlari va hujjat havolalari)
  if (await isEmpty(payload, 'sdg-goals')) {
    for (const g of sdg.goals as any[]) {
      await payload.create({ collection: 'sdg-goals', overrideAccess: true, context: ctx, data: { ...g, highlight: g.highlight ?? undefined, reports: g.reports.map((r: any) => ({ ...r, display: 'open' })) } })
    }
    await payload.updateGlobal({ slug: 'sdg-page', overrideAccess: true, context: ctx, data: { impactYear: sdg.impactYear } })
    payload.logger.info('BRM maqsadlari yuklandi')
  }

  const symbols = await payload.findGlobal({ slug: 'symbols', depth: 0, overrideAccess: true })
  if (!symbols.flag?.image) {
    const flag = await upload(payload, 'flag.webp', 'logos', { uz: 'Özbekiston bayroği', ru: 'Флаг Узбекистана', en: 'Flag of Uzbekistan', zh: '乌兹别克斯坦国旗' })
    const emblem = await upload(payload, 'emblem.webp', 'logos', { uz: 'Özbekiston gerbi', ru: 'Герб Узбекистана', en: 'Emblem of Uzbekistan', zh: '乌兹别克斯坦国徽' })
    await payload.updateGlobal({ slug: 'symbols', overrideAccess: true, context: ctx, data: { flag: { ...symbols.flag, image: flag }, emblem: { ...symbols.emblem, image: emblem } } })
    payload.logger.info('Ramzlar yuklandi')
  }
}
