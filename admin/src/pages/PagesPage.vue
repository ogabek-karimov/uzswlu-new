<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api, type I18n, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { LANGS, type Lang, PDF_MODES, SITE_URL } from '@/lib/constants'
import { setAllCollapsed } from '@/lib/collapse'
import { fileSize } from '@/lib/format'
import AlphabetButton from '@/components/AlphabetButton.vue'
import Collapsible from '@/components/Collapsible.vue'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'
import MediaPicker from '@/components/MediaPicker.vue'
import PageShowcaseField, { type Showcase } from '@/components/PageShowcaseField.vue'
import PageStaffField from '@/components/PageStaffField.vue'
import PdfSlot from '@/components/PdfSlot.vue'
import RichEditor from '@/components/RichEditor.vue'
import CamerasField from '@/components/CamerasField.vue'
import { type Camera, joinCameras, splitCameras } from '@/lib/cameras'
import VideoTourCard from '@/components/VideoTourCard.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Sahifalar daraxti: sahifa ichida sahifa, nomini o'zgartirish, tartib — sayt menyusi o'z-o'zidan yangilanadi
type Template = 'group' | 'text' | 'special' | 'link'
type Att = { file?: MediaDoc | number | null; url?: string | null; title: I18n; meta?: I18n; display: 'embed' | 'open' | 'download' | 'link'; height?: number | null }
type Page = {
  id: number; title: I18n; template: Template; parent?: number | { id: number } | null; slug?: string | null; url?: string | null; file?: MediaDoc | number | null
  groupKey?: string | null; description?: I18n; overview?: string | null; sdg?: number | null; inMenu?: boolean; published?: boolean; highlight?: boolean; showRector?: boolean; showUnits?: boolean; staffDepartment?: string; staffExtra?: string[]; staffContacts?: Record<string, { phone?: string; email?: string }>; staffHours?: I18n; ctaTitle?: I18n; ctaText?: I18n; ctaLabel?: I18n; ctaUrl?: string; icon?: string; showChildren?: boolean; showcase?: Showcase; docStyle?: boolean
  lead?: I18n; body?: I18n; facts?: { value: string; label: I18n }[]; timeline?: { label: I18n; text: I18n; highlight?: boolean }[]; attachments?: Att[]; order?: number | null
}

const TEMPLATES: { value: Template; label: string }[] = [
  { value: 'text', label: 'Matnli sahifa' },
  { value: 'group', label: 'Bölim (menyu guruhi)' },
  { value: 'special', label: 'Saytning maxsus sahifasi' },
  { value: 'link', label: 'Havola yoki PDF fayl' },
]
// Maxsus sahifaning mazmuni admin panelning qaysi bo'limida tahrirlanadi
const SPECIAL_EDITORS: [RegExp, string, string][] = [
  [/^\/rektorat$/, '/rahbariyat', 'Rahbariyat'],
  [/^\/brm(-|$)/, '/brm', 'BRM'],
  [/^\/meyoriy-hujjatlar$/, '/hujjatlar', 'Hujjatlar'],
  [/^\/video-darsliklar$/, '/video', 'Video darsliklar'],
  [/^\/fakultetlar-va-kafedralar$/, '/fakultetlar', 'Fakultetlar'],
  [/^\/staff$/, '/xodimlar', 'Xodimlar'],
  [/^\/(yangiliklar|news|announcements|events)$/, '/postlar/news', 'Yangiliklar'],
]

const pages = ref<Page[]>([])
const sel = ref<number | null>(null)
const open = ref<Set<number>>(new Set())
const q = ref('')
const lang = ref<Lang>('uz')
const saving = ref(false)
const saved = ref(false)
const error = ref('')

const pid = (p: Page) => (p.parent && typeof p.parent === 'object' ? p.parent.id : p.parent ?? null)
const kids = (id: number | null) => pages.value.filter(p => pid(p) === id).sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
const byId = (id: number | null) => pages.value.find(p => p.id === id) ?? null

async function load() {
  pages.value = (await api.get<Paginated<Page>>('/pages', { limit: 2000, depth: 0, sort: 'order' })).docs
  const want = Number(route.query.id)
  if (want && byId(want)) { pick(want); return }
  if (sel.value === null) {
    const first = kids(null)[0]
    if (first) { open.value.add(first.id); pick(kids(first.id)[0]?.id ?? first.id) }
  }
}
onMounted(load)
const route = useRoute()
// Umumiy qidiruvdan: /sahifalar?id=N — şu sahifa tanlanadi
watch(() => route.query.id, v => { if (Number(v) && byId(Number(v))) pick(Number(v)) })

// Daraxt (qidiruvda — mos sahifalar va ularning ota sahifalari)
type Row = { page: Page; depth: number; count: number }
const rows = computed<Row[]>(() => {
  const s = q.value.trim().toLowerCase()
  const match = (p: Page): boolean => LANGS.some(l => (p.title[l.code] ?? '').toLowerCase().includes(s)) || kids(p.id).some(match)
  const out: Row[] = []
  const walk = (id: number | null, depth: number) => {
    for (const p of kids(id)) {
      if (s && !match(p)) continue
      const c = kids(p.id).length
      out.push({ page: p, depth, count: c })
      if (c && (s || open.value.has(p.id))) walk(p.id, depth + 1)
    }
  }
  walk(null, 0)
  return out
})
const dot = (p: Page) => (!p.published ? ['#F79009', 'Qoralama'] : p.inMenu === false ? ['#C9C5D6', 'Menyuda yöq'] : ['#12B76A', 'Naşr qilingan'])
function toggle(id: number) {
  const s = new Set(open.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  open.value = s
}

// Tahrirlash formasi
const blank = () => ({
  title: {} as I18n, template: 'text' as Template, parent: null as number | null, slug: '', url: '', file: null as MediaDoc | null, groupKey: '',
  description: {} as I18n, overview: '', sdg: 0, inMenu: true, published: true, highlight: false, showRector: false, showUnits: false, staffDepartment: '', staffExtra: [] as string[], staffContacts: {} as Record<string, { phone?: string; email?: string }>, staffHours: {} as I18n, ctaTitle: {} as I18n, ctaText: {} as I18n, ctaLabel: {} as I18n, ctaUrl: '', icon: '', showChildren: false, showcase: {} as Showcase, docStyle: false,
  lead: {} as I18n, body: {} as I18n, facts: [] as { value: string; label: I18n }[], timeline: [] as { label: I18n; text: I18n; highlight: boolean }[], attachments: [] as Att[],
})
const form = reactive(blank())
const current = computed(() => byId(sel.value))
const obj = (v: unknown) => (v && typeof v === 'object' ? v as MediaDoc : null)

function pick(id: number) {
  sel.value = id
  saved.value = false
  error.value = ''
  const p = byId(id)
  if (!p) return
  // Ota sahifalarini ochib qo'yish
  for (let x = pid(p); x; x = pid(byId(x)!)) open.value.add(x)
  Object.assign(form, blank(), {
    title: { ...p.title }, template: p.template, parent: pid(p), slug: p.slug ?? '', url: p.url ?? '', file: obj(p.file), groupKey: p.groupKey ?? '',
    description: { ...(p.description ?? {}) }, overview: p.overview ?? '', sdg: p.sdg ?? 0, inMenu: p.inMenu !== false, published: p.published !== false, highlight: !!p.highlight, showRector: !!p.showRector, showUnits: !!p.showUnits, staffDepartment: p.staffDepartment ?? '', staffExtra: [...(p.staffExtra ?? [])], staffContacts: { ...(p.staffContacts ?? {}) }, staffHours: { ...(p.staffHours ?? {}) }, ctaTitle: { ...(p.ctaTitle ?? {}) }, ctaText: { ...(p.ctaText ?? {}) }, ctaLabel: { ...(p.ctaLabel ?? {}) }, ctaUrl: p.ctaUrl ?? '', icon: p.icon ?? '', showChildren: !!p.showChildren, showcase: JSON.parse(JSON.stringify(p.showcase ?? {})) as Showcase, docStyle: !!p.docStyle,
    lead: { ...(p.lead ?? {}) }, body: { ...(p.body ?? {}) },
    facts: (p.facts ?? []).map(f => ({ value: f.value, label: { ...f.label } })),
    timeline: (p.timeline ?? []).map(t => ({ label: { ...t.label }, text: { ...t.text }, highlight: !!t.highlight })),
    attachments: (p.attachments ?? []).map(a => ({ ...a, title: { ...(a.title ?? {}) }, meta: { ...(a.meta ?? {}) } })),
  })
  cameras.value = splitCameras(form.body, LANGS) // Onlayn kameralar — alohida panelda (saqlaşda matn oxiriga qaytadi)
}
// ─── Onlayn kameralar (Online translatsiya) ───
const cameras = ref<Camera[]>([])
const camerasOn = computed(() => form.slug === 'online-translatsiya' || cameras.value.length > 0)
const bodyOut = () => (camerasOn.value ? joinCameras(form.body, cameras.value, LANGS) : form.body)

const path = computed(() => {
  const names: string[] = []
  for (let x = form.parent; x; x = pid(byId(x)!) ?? null) names.unshift(byId(x)?.title.uz ?? '')
  return ['Sahifalar', ...names, form.title.uz || 'Yangi sahifa'].join(' / ')
})
const siteUrl = computed(() => {
  if (form.template === 'text' && form.slug) return `${SITE_URL}/${form.slug}`
  if (form.template === 'special' && form.url) return form.url.startsWith('http') ? form.url : `${SITE_URL}${form.url}`
  if (form.template === 'link') return form.file?.url ?? form.url
  if (form.template === 'group') return form.overview ? `${SITE_URL}${form.overview}` : form.url ? `${SITE_URL}${form.url}` : ''
  return ''
})
const specialEditor = computed(() => SPECIAL_EDITORS.find(([re]) => re.test(form.url)) ?? null)
// Ota sahifa sifatida o'zi va o'z ichidagilari tanlanmaydi
const parentOptions = computed(() => {
  const banned = new Set<number>()
  const mark = (id: number) => { banned.add(id); kids(id).forEach(k => mark(k.id)) }
  if (sel.value) mark(sel.value)
  const out: { id: number; label: string }[] = []
  const walk = (id: number | null, depth: number) => kids(id).forEach((p) => {
    if (banned.has(p.id) || p.template === 'link' || p.template === 'special') return
    out.push({ id: p.id, label: `${'— '.repeat(depth)}${p.title.uz}` })
    walk(p.id, depth + 1)
  })
  walk(null, 0)
  return out
})

// Yaşiriş oldidan tasdiq oynasi, körsatiş — darhol
const hiding = ref<Page | null>(null)
async function toggleVisible(p: Page, sure = false) {
  const v = p.published === false
  if (!v && !sure) { hiding.value = p; return }
  hiding.value = null
  await api.patch(`/pages/${p.id}`, { published: v }, { depth: 0 })
  p.published = v
  if (sel.value === p.id) form.published = v
  pages.value = [...pages.value]
}

async function save() {
  if (!form.title.uz?.trim()) { error.value = 'Özbekça nomi majburiy'; return }
  saving.value = true
  error.value = ''
  const data = {
    title: form.title, template: form.template, parent: form.parent, slug: form.slug.trim() || null, url: form.url.trim() || null, file: form.file?.id ?? null,
    groupKey: form.groupKey.trim() || null, description: form.description, overview: form.overview.trim() || null, sdg: form.sdg || null,
    inMenu: form.inMenu, published: form.published, highlight: form.highlight, showRector: form.showRector, showUnits: form.showUnits, staffDepartment: form.staffDepartment.trim(), staffExtra: form.staffExtra, staffContacts: form.staffContacts, staffHours: form.staffHours, ctaTitle: form.ctaTitle, ctaText: form.ctaText, ctaLabel: form.ctaLabel, ctaUrl: form.ctaUrl.trim(), icon: form.icon.trim(), showChildren: form.showChildren, showcase: form.showcase, docStyle: form.docStyle,
    lead: form.lead, body: bodyOut(), facts: form.facts.filter(f => f.value.trim()), timeline: form.timeline,
    attachments: form.attachments.map(a => ({ file: obj(a.file)?.id ?? (typeof a.file === 'number' ? a.file : null), url: a.url?.trim() || null, title: a.title, meta: a.meta, display: a.display, height: a.height })),
  }
  try {
    if (sel.value === null) {
      const res = await api.post<{ doc: Page }>('/pages', { ...data, order: kids(form.parent).length + 1 })
      sel.value = res.doc.id
    }
    else await api.patch(`/pages/${sel.value}`, data)
    await load()
    pick(sel.value!)
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

function addPage() {
  const parent = current.value ? (current.value.template === 'group' ? current.value.id : pid(current.value)) : null
  sel.value = null
  saved.value = false
  error.value = ''
  Object.assign(form, blank(), { parent, published: false, title: { uz: '' } })
}

async function remove() {
  if (!current.value) return
  if (kids(current.value.id).length) { error.value = 'Avval içidagi sahifalarni köçiring yoki öçiring'; return }
  if (!confirm(`“${current.value.title.uz}” sahifasi öçirilsinmi?`)) return
  try {
    await api.del(`/pages/${current.value.id}`)
    sel.value = null
    await load()
  }
  catch (e) {
    error.value = (e as Error).message
  }
}

// Tartib: bir ota ichida yuqoriga/pastga
async function move(p: Page, d: number) {
  const sibs = kids(pid(p))
  const i = sibs.findIndex(x => x.id === p.id)
  const j = i + d
  if (j < 0 || j >= sibs.length) return
  const [it] = sibs.splice(i, 1)
  sibs.splice(j, 0, it!)
  await Promise.all(sibs.map((s, k) => {
    if (s.order === k + 1) return null
    s.order = k + 1
    return api.patch(`/pages/${s.id}`, { order: k + 1 }, { depth: 0 })
  }))
  pages.value = [...pages.value]
}

// PDF / havolalar
const picker = ref(false)
const attInput = ref<HTMLInputElement>()
async function onAttach(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const m = await uploadMedia(file, { folder: 'docs' })
  form.attachments.push({ file: m, title: { uz: file.name.replace(/\.pdf$/i, '') }, meta: {}, display: 'embed', height: 680 })
  ;(e.target as HTMLInputElement).value = ''
}
// «Saytda qanday körinadi» izohi — sahifalarda «Içi körinadi» PDF ko'rgiçda (varaqlar 1 2 3 …) oçiladi
const PAGE_PDF_NOTE: Record<string, string> = {
  embed: 'PDF sahifada oçilib turadi: birinçi varaq körinadi, ostida 1 2 3 … — bosilganda faqat varaq almaşadi. Telefonda ham işlaydi.',
  open: 'Karta körinişida; bosilganda PDF yangi oynada oçiladi.',
  download: 'Karta körinişida; bosilganda fayl yuklab olinadi.',
  link: 'Matn ostida faqat nomi (havola); bosilganda PDF oçiladi.',
}
// «Havola / PDF» sahifasini matnli sahifaga aylantiriş: yuklangan PDF «Içi körinadi» bölib o'tadi (taşqi havola — olib taşlanadi)
function toEmbeddedPage() {
  if (form.file) form.attachments.push({ file: form.file, title: { ...form.title }, meta: {}, display: 'embed', height: 680 })
  form.template = 'text'
  form.file = null
  form.url = ''
}
// Karta belgilari uçun tez tanlov (istalgan Lucide nomi ham bölaveradi)
const ICONS = ['brain', 'chess-knight', 'puzzle', 'goal', 'target', 'volleyball', 'book-open-text', 'lightbulb', 'trophy', 'medal', 'music', 'palette', 'mic', 'camera', 'globe', 'heart-handshake', 'users-round', 'sparkles']
const LANG_LABEL = computed(() => LANGS.find(l => l.code === lang.value)?.label)
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Sahifalar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Sahifa içida sahifa yarating, nomini özgartiring, tartibini almaştiring — sayt menyusi öz-özidan yangilanadi.</p>
      </div>
      <button type="button" class="btn-primary h-[46px]" @click="addPage"><Icon name="plus" :size="16" />Yangi sahifa</button>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <!-- Daraxt -->
      <section class="card min-w-0 flex-[1_1_340px] p-3.5 xl:max-w-[400px]">
        <label class="flex h-10 items-center gap-2 rounded-[10px] border border-field px-3 text-muted">
          <Icon name="search" :size="15" />
          <input v-model="q" aria-label="Sahifa qidiriş" placeholder="Sahifa qidiriş…" class="min-w-0 flex-1 bg-transparent text-[13px] outline-none">
        </label>
        <ul role="tree" aria-label="Sayt sahifalari" class="mt-3 flex max-h-[70dvh] flex-col gap-px overflow-y-auto">
          <li
            v-for="r in rows" :key="r.page.id" role="treeitem" :aria-expanded="r.count ? open.has(r.page.id) : undefined" :aria-selected="sel === r.page.id"
            class="group flex min-h-[38px] items-center gap-1 rounded-[10px] pr-2" :class="sel === r.page.id && 'bg-brand-50 shadow-[inset_3px_0_0_var(--color-brand-700)]'"
            :style="{ paddingLeft: `${6 + r.depth * 20}px` }"
          >
            <button type="button" class="size-[22px] shrink-0 text-xs text-muted" :aria-label="r.count ? (open.has(r.page.id) ? 'Yiğiş' : 'Oçiş') : 'Iç sahifa yöq'" :disabled="!r.count" @click="toggle(r.page.id)">{{ r.count ? (open.has(r.page.id) || q ? '▾' : '▸') : '' }}</button>
            <button type="button" class="min-w-0 flex-1 truncate px-1 py-2 text-left text-sm" :class="r.depth === 0 ? 'font-bold' : sel === r.page.id ? 'font-semibold' : 'font-medium'" @click="pick(r.page.id)">{{ r.page.title.uz }}</button>
            <span class="hidden shrink-0 group-hover:flex">
              <button type="button" class="h-6 px-0.5 text-[10px] text-subtle" :aria-label="`${r.page.title.uz} — yuqoriga`" @click="move(r.page, -1)">▲</button>
              <button type="button" class="h-6 px-0.5 text-[10px] text-subtle" :aria-label="`${r.page.title.uz} — pastga`" @click="move(r.page, 1)">▼</button>
            </span>
            <button type="button" class="grid size-7 shrink-0 place-items-center rounded-lg transition-colors hover:bg-brand-50" :class="r.page.published === false ? 'text-[#F79009]' : 'text-subtle hover:text-brand-700'" :title="r.page.published === false ? 'Saytda körinmaydi — körsatiş' : 'Saytda körinadi — yaşiriş'" :aria-label="`${r.page.title.uz} — ${r.page.published === false ? 'saytda körsatiş' : 'saytdan yaşiriş'}`" :aria-pressed="r.page.published !== false" @click="toggleVisible(r.page)"><Icon :name="r.page.published === false ? 'eye-off' : 'eye'" :size="15" /></button>
            <span :title="dot(r.page)[1]" class="size-[7px] shrink-0 rounded-full" :style="{ background: dot(r.page)[0] }" />
            <span class="min-w-[22px] shrink-0 text-right text-[11px] text-subtle">{{ r.count || '' }}</span>
          </li>
        </ul>
        <p class="mx-1 mt-3 flex flex-wrap gap-3.5 text-xs text-subtle">
          <span class="flex items-center gap-1.5"><span class="size-[7px] rounded-full bg-[#12B76A]" />naşr qilingan</span>
          <span class="flex items-center gap-1.5"><span class="size-[7px] rounded-full bg-[#F79009]" />qoralama</span>
          <span class="flex items-center gap-1.5"><span class="size-[7px] rounded-full bg-[#C9C5D6]" />menyuda yöq</span>
        </p>
      </section>

      <!-- Tanlangan sahifa -->
      <form class="flex min-w-0 flex-[999_1_520px] flex-col gap-[18px]" @submit.prevent="save">
        <section class="card px-[22px] py-5">
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="min-w-0">
              <p class="text-xs text-subtle">{{ path }}</p>
              <h2 class="mt-1 text-[22px] font-bold">{{ form.title.uz || 'Yangi sahifa' }}</h2>
            </div>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="btn-ghost h-10! px-3!" title="Barça bölimlarni yiğiş" @click="setAllCollapsed(true)">Hammasini yiğiş</button>
              <button type="button" class="btn-ghost h-10! px-3!" title="Barça bölimlarni yoyiş" @click="setAllCollapsed(false)">Yoyiş</button>
              <a v-if="siteUrl && sel !== null" :href="siteUrl" target="_blank" rel="noopener" class="btn-ghost h-10!">Saytda köriş ↗</a>
              <button type="submit" class="btn-primary h-10!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
            </div>
          </div>
          <div class="mt-[18px]"><I18nFields v-model="form.title" label="Nomi" required :placeholders="{ zh: '中文名称' }" /></div>
          <!-- Nomi, tavsif, kiriş matni va sahifa matnining özbekçasi — bir bosişda yangi alifboga -->
          <AlphabetButton class="mt-3.5" :target="form" />
          <div class="mt-3 grid gap-3 sm:grid-cols-3">
            <div v-if="form.template === 'text' || form.template === 'group'">
              <label for="pg-slug" class="label">Manzil</label>
              <div class="flex items-center rounded-xl border border-field pl-3 focus-within:border-brand-700"><span class="text-sm text-subtle">/</span><input id="pg-slug" v-model="form.slug" class="h-11 min-w-0 flex-1 bg-transparent px-1 text-sm outline-none" :placeholder="form.template === 'text' ? 'nomidan öz-özidan' : 'ixtiyoriy'"></div>
            </div>
            <div v-else>
              <label for="pg-url" class="label">{{ form.template === 'special' ? 'Saytdagi yöl' : 'Havola' }}</label>
              <input id="pg-url" v-model="form.url" class="field" :placeholder="form.template === 'special' ? '/rektorat' : 'https://…'">
            </div>
            <div>
              <label for="pg-parent" class="label">Ota sahifa</label>
              <select id="pg-parent" v-model="form.parent" class="field"><option :value="null">— Yuqori daraja —</option><option v-for="o in parentOptions" :key="o.id" :value="o.id">{{ o.label }}</option></select>
            </div>
            <div>
              <label for="pg-tpl" class="label">Şablon</label>
              <select id="pg-tpl" v-model="form.template" class="field"><option v-for="t in TEMPLATES" :key="t.value" :value="t.value">{{ t.label }}</option></select>
            </div>
          </div>
          <div class="mt-3.5 flex flex-wrap gap-[18px] text-sm font-semibold">
            <label class="flex items-center gap-2.5"><ToggleSwitch v-model="form.inMenu" label="Menyuda körsatiş" />Menyuda körsatiş</label>
            <label class="flex items-center gap-2.5"><ToggleSwitch v-model="form.published" label="Naşr qilingan" />Naşr qilingan</label>
            <label v-if="form.template !== 'group'" class="flex items-center gap-2.5"><ToggleSwitch v-model="form.highlight" label="Menyuda ajratib körsatiş" />Ajratib körsatiş</label>
            <label v-if="form.template === 'text'" class="flex items-center gap-2.5" title="Rektor surati va ma’lumoti «Rahbariyat» bölimidan avtomatik olinadi — rektor almashsa sahifa özi yangilanadi"><ToggleSwitch v-model="form.showRector" label="Matndan keyin rektor kartasi" />Matndan keyin rektor kartasi</label>
            <label v-if="form.template === 'text'" class="flex items-center gap-2.5" title="Kartalar «Bölimlar» bölimidan (surat, F.I.Sh., lavozim, telefon)"><ToggleSwitch v-model="form.showUnits" label="Matndan keyin bölimlar kartalari" />Bölimlar kartalari</label>
            <label v-if="form.template === 'text'" class="flex items-center gap-2.5" title="Times New Roman shrifti, sarlavhalar markazda — rasmiy hujjat (tarix, nizom) uçun"><ToggleSwitch v-model="form.docStyle" label="Hujjat uslubi" />Hujjat uslubi (Times New Roman)</label>
            <label v-if="form.template === 'text'" class="flex items-center gap-2.5" title="Shu sahifa ichidagi sahifalar (masalan, Yoshlar ittifoqi → Zakovat, Futbol) — belgi, nom va hujjatlari bilan kartalar"><ToggleSwitch v-model="form.showChildren" label="Ichki sahifalar kartalari" />Ichki sahifalar kartalari</label>
          </div>
          <div v-if="form.template === 'text'" class="mt-3.5 max-w-[360px]">
            <label for="pg-icon" class="label">Belgi <span class="font-normal">(ota sahifadagi karta uçun)</span></label>
            <input id="pg-icon" v-model="form.icon" class="field" placeholder="masalan: brain, chess-knight, volleyball" list="pg-icon-list">
            <datalist id="pg-icon-list"><option v-for="i in ICONS" :key="i" :value="i" /></datalist>
            <p class="mt-1 text-xs text-muted">Lucide belgisi nomi — <a href="https://lucide.dev/icons" target="_blank" rel="noopener" class="font-semibold text-brand-700 underline">lucide.dev/icons</a></p>
          </div>
          <PageStaffField v-if="form.template === 'text'" v-model:department="form.staffDepartment" v-model:extra="form.staffExtra" v-model:contacts="form.staffContacts" v-model:hours="form.staffHours" class="mt-4" />
          <PageShowcaseField v-if="form.template === 'text'" v-model="form.showcase" class="mt-4" />
          <!-- Matndan keyin animatsiyali chaqiruv bloki (masalan, ARM → uzlib.uz) -->
          <Collapsible v-if="form.template === 'text'" id="page-cta" variant="inner" class="mt-4" title="Chaqiruv bloki" hint="Matndan keyin, animatsiyali tugma" :default-open="!!form.ctaUrl" body-class="">
            <div>
              <label for="pg-cta-url" class="label">Havola</label>
              <input id="pg-cta-url" v-model="form.ctaUrl" class="field" placeholder="https://uzlib.uz/ yoki /sahifa-manzili">
              <p class="mt-1 text-xs text-muted">Havola va tugma yozuvi kiritilsa — blok saytda çiqadi; böş qolsa körinmaydi. Taşqi sayt yangi oynada oçiladi.</p>
            </div>
            <div class="mt-3.5 grid gap-3.5">
              <I18nFields v-model="form.ctaTitle" label="Sarlavha" layout="rows" />
              <I18nFields v-model="form.ctaText" label="Matn" textarea :rows="2" />
              <I18nFields v-model="form.ctaLabel" label="Tugma yozuvi" layout="rows" />
            </div>
          </Collapsible>
          <p v-if="error" class="mt-3 rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
          <p v-else-if="saved" class="mt-3 rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — sayt menyusi va sahifa yangilandi.</p>
        </section>

        <!-- «Universitet haqida» bo'limi: bosh sahifadagi video tur (media va ma'lumot faqat shu yerdan) -->
        <VideoTourCard v-if="form.slug === 'universitet-haqida' || (form.template === 'group' && form.groupKey === 'university')" />

        <!-- Bo'lim (menyu guruhi) -->
        <Collapsible v-if="form.template === 'group'" id="page-group" title="Menyu bölimi">
          <I18nFields v-model="form.description" label="Qisqa tavsif (mega-menyuda)" textarea :rows="2" />
          <div class="grid gap-3 sm:grid-cols-3">
            <div><label for="pg-ov" class="label">Umumiy sahifasi</label><input id="pg-ov" v-model="form.overview" class="field" placeholder="/universitet-haqida"></div>
            <div><label for="pg-gurl" class="label">Bitta sahifali bölim</label><input id="pg-gurl" v-model="form.url" class="field" placeholder="/aloqa"></div>
            <div><label for="pg-key" class="label">Belgi kaliti</label><select id="pg-key" v-model="form.groupKey" class="field"><option v-for="k in ['university', 'applicants', 'activity', 'news', 'sdg', 'programs', 'video', 'contact']" :key="k" :value="k">{{ k }}</option></select></div>
          </div>
        </Collapsible>

        <!-- Maxsus sahifa -->
        <Collapsible v-else-if="form.template === 'special'" id="page-special" title="Saytning maxsus sahifasi">
          <p class="text-sm leading-relaxed text-muted">Bu sahifaning dizayni saytda alohida qilingan — bu yerda faqat nomi, menyudagi örni va manzili boşqariladi.<template v-if="specialEditor"> Mazmuni <RouterLink :to="specialEditor[1]" class="font-semibold text-brand-700 underline">{{ specialEditor[2] }}</RouterLink> bölimida tahrirlanadi.</template></p>
          <div class="max-w-[200px]"><label for="pg-sdg" class="label">BRM maqsadi <span class="font-normal">(rangli plitka)</span></label><input id="pg-sdg" v-model.number="form.sdg" type="number" min="0" max="17" class="field"></div>
        </Collapsible>

        <!-- Havola / PDF -->
        <Collapsible v-else-if="form.template === 'link'" id="page-link" title="Havola yoki PDF">
          <p class="text-sm text-muted">Menyuda bosilganda şu fayl yoki tashqi sahifa oçiladi. Fayl yuklansa — havola özgarmaydi, yangi versiya yuklaş mumkin.</p>
          <div class="max-w-[260px]"><PdfSlot v-model="form.file" lang="PDF fayl" note="yoki yuqoridagi havola" /></div>
          <!-- PDF'ni saytning öz sahifasida (varaqlab) körsatiş: sahifa matnli sahifaga aylanadi, PDF — «Içi körinadi» -->
          <div class="rounded-xl border border-dashed border-brand-200 bg-brand-50/50 px-4 py-3.5">
            <p class="text-sm font-semibold">PDF sayt sahifasi içida oçilsinmi?</p>
            <p class="mt-1 text-xs text-muted">Hozir menyuda bosilganda PDF alohida oçiladi. Tugma bosilsa — bu sahifa matnli sahifaga aylanadi: PDF sayt içida birinçi varaq bilan oçilib turadi, ostida 1 2 3 … varaqlar. Keyin «Saqlaş» ni bosing.</p>
            <button type="button" class="btn-primary mt-2.5 h-9! text-xs!" @click="toEmbeddedPage">PDF sahifa içida körinsin</button>
          </div>
        </Collapsible>

        <!-- Matnli sahifa mazmuni -->
        <template v-else>
          <Collapsible id="page-content" title="Sahifa mazmuni" body-class="flex flex-col gap-3.5">
            <template #actions>
              <div role="tablist" aria-label="Til" class="flex gap-1">
                <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
              </div>
            </template>
            <div><label for="pg-lead" class="label">Kirish matni · {{ LANG_LABEL }} <span class="font-normal">(sarlavha ostida)</span></label><textarea id="pg-lead" v-model="form.lead[lang]" rows="2" class="field h-auto! py-2.5 leading-relaxed" /></div>
            <div>
              <span class="label">Matn · {{ LANG_LABEL }} <span class="font-normal">— rasm, jadval, video ham şu yerda; vaqt çiziği joyini [[timeline]], kartali bloklar joyini [[kartalar-1]], [[kartalar-2]]… deb belgilang</span></span>
              <div class="overflow-hidden rounded-xl border border-field"><RichEditor :key="`${sel}-${lang}`" :model-value="form.body[lang] ?? ''" placeholder="Sahifa matni…" @update:model-value="v => (form.body[lang] = v)" /></div>
            </div>
            <CamerasField v-if="camerasOn" v-model="cameras" />
          </Collapsible>

          <Collapsible id="page-facts" title="Raqamlar" hint="Ixtiyoriy" :count="form.facts.length" :default-open="false" body-class="flex flex-col gap-2.5">
            <template #actions><button type="button" class="btn-ghost h-9! text-xs!" @click="form.facts.push({ value: '', label: {} })">+ Raqam</button></template>
            <div v-for="(f, i) in form.facts" :key="i" class="flex items-center gap-2">
              <input v-model="f.value" class="field w-[130px]! shrink-0" aria-label="Raqam" placeholder="23 168">
              <input v-model="f.label[lang]" class="field" :aria-label="`Izoh · ${lang}`" :placeholder="`Izoh · ${LANG_LABEL}`">
              <button type="button" class="grid size-9 shrink-0 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="Raqamni olib taşlaş" @click="form.facts.splice(i, 1)"><Icon name="trash" :size="14" /></button>
            </div>
          </Collapsible>

          <Collapsible id="page-timeline" title="Vaqt çiziği" hint="Ixtiyoriy" :count="form.timeline.length" :default-open="false" body-class="flex flex-col gap-2.5">
            <template #actions><button type="button" class="btn-ghost h-9! text-xs!" @click="form.timeline.push({ label: {}, text: {}, highlight: false })">+ Sana</button></template>
            <div v-for="(t, i) in form.timeline" :key="i" class="grid items-center gap-2 sm:grid-cols-[130px_1fr_auto_auto]">
              <input v-model="t.label[lang]" class="field" :aria-label="`Yil · ${lang}`" placeholder="1949">
              <input v-model="t.text[lang]" class="field" :aria-label="`Matn · ${lang}`" :placeholder="`Matn · ${LANG_LABEL}`">
              <label class="flex items-center gap-1.5 text-xs text-muted"><input v-model="t.highlight" type="checkbox" class="accent-brand-800"> ajratilgan</label>
              <button type="button" class="grid size-9 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="Sanani olib taşlaş" @click="form.timeline.splice(i, 1)"><Icon name="trash" :size="14" /></button>
            </div>
          </Collapsible>

          <Collapsible id="page-pdf" title="PDF hujjatlar" hint="Matndan keyin çiqadi. Har bir PDF uçun saytda qanday körinişini tanlang." :count="form.attachments.length">
            <template #actions>
              <button type="button" class="btn-ghost h-9! text-xs!" @click="attInput?.click()">+ PDF yuklaş</button>
              <button type="button" class="btn-ghost h-9! text-xs!" @click="picker = true">Serverdan tanlaş</button>
            </template>
            <input ref="attInput" type="file" accept="application/pdf" class="hidden" @change="onAttach">
            <MediaPicker :open="picker" kind="pdf" @close="picker = false" @pick="m => { form.attachments.push({ file: m, title: { uz: (m.filename ?? '').replace(/\.pdf$/i, '') }, meta: {}, display: 'embed', height: 680 }); picker = false }" />
            <p v-if="!form.attachments.length" class="rounded-xl bg-canvas px-3.5 py-3 text-sm text-muted">PDF yöq. «+ PDF yuklaş» bilan qöşing — keyin uning ostida <b>«Saytda qanday körinadi»</b> tanlanadi (masalan, «Içi körinadi» — PDF sahifada oçilib turadi va 1 2 3 … bilan varaqlanadi).</p>
            <div v-for="(a, i) in form.attachments" :key="i" class="rounded-[14px] border border-line p-3.5">
              <div class="flex items-start gap-3">
                <span aria-hidden="true" class="grid h-11 w-9 shrink-0 place-items-center rounded-md bg-[#FDECEA] text-[10px] font-extrabold text-[#B42318]">PDF</span>
                <div class="grid min-w-0 flex-1 gap-2 sm:grid-cols-2">
                  <input v-model="a.title[lang]" class="field" :aria-label="`Nomi · ${lang}`" :placeholder="`Nomi · ${LANG_LABEL}`">
                  <input v-model="a.meta![lang]" class="field" :aria-label="`Izoh · ${lang}`" placeholder="Izoh (ixtiyoriy)">
                  <p v-if="obj(a.file)" class="text-xs text-subtle sm:col-span-2">{{ obj(a.file)?.filename }} · {{ fileSize(obj(a.file)?.filesize) }}</p>
                  <input v-else v-model="a.url" class="field sm:col-span-2" aria-label="Havola" placeholder="https://…">
                </div>
                <button type="button" class="grid size-8 shrink-0 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="PDF ni olib taşlaş" @click="form.attachments.splice(i, 1)"><Icon name="trash" :size="14" /></button>
              </div>
              <div v-if="obj(a.file)" class="mt-3">
                <p class="mb-1.5 text-[13px] font-semibold">Saytda qanday körinadi:</p>
                <div role="radiogroup" aria-label="Saytda qanday körinadi" class="grid grid-cols-2 gap-1 rounded-xl bg-canvas p-1 sm:grid-cols-4">
                  <button v-for="m in PDF_MODES" :key="m.value" type="button" role="radio" :aria-checked="a.display === m.value" class="min-h-9 rounded-[9px] px-1.5 text-xs font-semibold" :class="a.display === m.value ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="a.display = m.value">{{ m.label }}</button>
                </div>
                <!-- Tanlangan körinişning izohi (sahifalar uçun) -->
                <p class="mt-1.5 text-xs text-muted">{{ PAGE_PDF_NOTE[a.display] }}</p>
              </div>
            </div>
          </Collapsible>
        </template>

        <div v-if="sel !== null" class="flex justify-end">
          <button type="button" class="btn-danger h-10!" @click="remove">Sahifani öçiriş</button>
        </div>
      </form>
    </div>
  </div>
  <div v-if="hiding" class="fixed inset-0 z-[90] grid place-items-center bg-night/55 p-4" @click.self="hiding = null" @keydown.esc="hiding = null">
    <section role="alertdialog" aria-modal="true" aria-labelledby="hide-title" aria-describedby="hide-text" class="w-full max-w-[440px] rounded-[22px] bg-white p-6 shadow-2xl">
      <span class="grid size-11 place-items-center rounded-2xl bg-[#FEF3DC] text-[#B54708]"><Icon name="eye-off" :size="20" /></span>
      <h2 id="hide-title" class="mt-4 text-xl font-bold tracking-tight">Sahifa yaşirilsinmi?</h2>
      <p id="hide-text" class="mt-2 text-[15px] leading-relaxed text-muted">«{{ hiding.title.uz }}» saytda körinmay qoladi (qoralamaga ötadi). Uni istalgan payt ko'z belgisi orqali qayta körsatiş mumkin.</p>
      <div class="mt-5 flex flex-wrap justify-end gap-3">
        <button type="button" class="btn-ghost" @click="hiding = null">Bekor qiliş</button>
        <button type="button" class="btn-primary" @click="toggleVisible(hiding!, true)">Ha, yaşiriş</button>
      </div>
    </section>
  </div>
</template>
