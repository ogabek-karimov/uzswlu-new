<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { LANGS, type Lang, PDF_MODES, SITE_URL } from '@/lib/constants'
import { fileSize } from '@/lib/format'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'
import MediaPicker from '@/components/MediaPicker.vue'
import PdfSlot from '@/components/PdfSlot.vue'
import RichEditor from '@/components/RichEditor.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Sahifalar daraxti: sahifa ichida sahifa, nomini o'zgartirish, tartib — sayt menyusi o'z-o'zidan yangilanadi
type Template = 'group' | 'text' | 'special' | 'link'
type Att = { file?: MediaDoc | number | null; url?: string | null; title: I18n; meta?: I18n; display: 'embed' | 'open' | 'download' | 'link'; height?: number | null }
type Page = {
  id: number; title: I18n; template: Template; parent?: number | { id: number } | null; slug?: string | null; url?: string | null; file?: MediaDoc | number | null
  groupKey?: string | null; description?: I18n; overview?: string | null; sdg?: number | null; inMenu?: boolean; published?: boolean; highlight?: boolean
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
  if (sel.value === null) {
    const first = kids(null)[0]
    if (first) { open.value.add(first.id); pick(kids(first.id)[0]?.id ?? first.id) }
  }
}
onMounted(load)

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
  description: {} as I18n, overview: '', sdg: 0, inMenu: true, published: true, highlight: false,
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
    description: { ...(p.description ?? {}) }, overview: p.overview ?? '', sdg: p.sdg ?? 0, inMenu: p.inMenu !== false, published: p.published !== false, highlight: !!p.highlight,
    lead: { ...(p.lead ?? {}) }, body: { ...(p.body ?? {}) },
    facts: (p.facts ?? []).map(f => ({ value: f.value, label: { ...f.label } })),
    timeline: (p.timeline ?? []).map(t => ({ label: { ...t.label }, text: { ...t.text }, highlight: !!t.highlight })),
    attachments: (p.attachments ?? []).map(a => ({ ...a, title: { ...(a.title ?? {}) }, meta: { ...(a.meta ?? {}) } })),
  })
}

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

async function save() {
  if (!form.title.uz?.trim()) { error.value = 'Özbekça nomi majburiy'; return }
  saving.value = true
  error.value = ''
  const data = {
    title: form.title, template: form.template, parent: form.parent, slug: form.slug.trim() || null, url: form.url.trim() || null, file: form.file?.id ?? null,
    groupKey: form.groupKey.trim() || null, description: form.description, overview: form.overview.trim() || null, sdg: form.sdg || null,
    inMenu: form.inMenu, published: form.published, highlight: form.highlight,
    lead: form.lead, body: form.body, facts: form.facts.filter(f => f.value.trim()), timeline: form.timeline,
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
  form.attachments.push({ file: m, title: { uz: file.name.replace(/\.pdf$/i, '') }, meta: {}, display: 'open', height: 680 })
  ;(e.target as HTMLInputElement).value = ''
}
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
            <div class="flex gap-2">
              <a v-if="siteUrl && sel !== null" :href="siteUrl" target="_blank" rel="noopener" class="btn-ghost h-10!">Saytda köriş ↗</a>
              <button type="submit" class="btn-primary h-10!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
            </div>
          </div>
          <div class="mt-[18px]"><I18nFields v-model="form.title" label="Nomi" required :placeholders="{ zh: '中文名称' }" /></div>
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
          </div>
          <p v-if="error" class="mt-3 rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
          <p v-else-if="saved" class="mt-3 rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — sayt menyusi va sahifa yangilandi.</p>
        </section>

        <!-- Bo'lim (menyu guruhi) -->
        <section v-if="form.template === 'group'" class="card flex flex-col gap-3 px-[22px] py-5">
          <h3 class="text-base font-bold">Menyu bölimi</h3>
          <I18nFields v-model="form.description" label="Qisqa tavsif (mega-menyuda)" textarea :rows="2" />
          <div class="grid gap-3 sm:grid-cols-3">
            <div><label for="pg-ov" class="label">Umumiy sahifasi</label><input id="pg-ov" v-model="form.overview" class="field" placeholder="/universitet-haqida"></div>
            <div><label for="pg-gurl" class="label">Bitta sahifali bölim</label><input id="pg-gurl" v-model="form.url" class="field" placeholder="/aloqa"></div>
            <div><label for="pg-key" class="label">Belgi kaliti</label><select id="pg-key" v-model="form.groupKey" class="field"><option v-for="k in ['university', 'applicants', 'activity', 'news', 'sdg', 'programs', 'video', 'contact']" :key="k" :value="k">{{ k }}</option></select></div>
          </div>
        </section>

        <!-- Maxsus sahifa -->
        <section v-else-if="form.template === 'special'" class="card flex flex-col gap-3 px-[22px] py-5">
          <h3 class="text-base font-bold">Saytning maxsus sahifasi</h3>
          <p class="text-sm leading-relaxed text-muted">Bu sahifaning dizayni saytda alohida qilingan — bu yerda faqat nomi, menyudagi örni va manzili boşqariladi.<template v-if="specialEditor"> Mazmuni <RouterLink :to="specialEditor[1]" class="font-semibold text-brand-700 underline">{{ specialEditor[2] }}</RouterLink> bölimida tahrirlanadi.</template></p>
          <div class="max-w-[200px]"><label for="pg-sdg" class="label">BRM maqsadi <span class="font-normal">(rangli plitka)</span></label><input id="pg-sdg" v-model.number="form.sdg" type="number" min="0" max="17" class="field"></div>
        </section>

        <!-- Havola / PDF -->
        <section v-else-if="form.template === 'link'" class="card flex flex-col gap-3 px-[22px] py-5">
          <h3 class="text-base font-bold">Havola yoki PDF</h3>
          <p class="text-sm text-muted">Menyuda bosilganda şu fayl yoki tashqi sahifa oçiladi. Fayl yuklansa — havola özgarmaydi, yangi versiya yuklaş mumkin.</p>
          <div class="max-w-[260px]"><PdfSlot v-model="form.file" lang="PDF fayl" note="yoki yuqoridagi havola" /></div>
        </section>

        <!-- Matnli sahifa mazmuni -->
        <template v-else>
          <section class="card flex flex-col gap-3.5 px-[22px] py-5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h3 class="text-base font-bold">Sahifa mazmuni</h3>
              <div role="tablist" aria-label="Til" class="flex gap-1">
                <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
              </div>
            </div>
            <div><label for="pg-lead" class="label">Kirish matni · {{ LANG_LABEL }} <span class="font-normal">(sarlavha ostida)</span></label><textarea id="pg-lead" v-model="form.lead[lang]" rows="2" class="field h-auto! py-2.5 leading-relaxed" /></div>
            <div>
              <span class="label">Matn · {{ LANG_LABEL }} <span class="font-normal">— rasm, jadval, video ham şu yerda; vaqt çiziği joyini [[timeline]] deb belgilang</span></span>
              <div class="overflow-hidden rounded-xl border border-field"><RichEditor :key="`${sel}-${lang}`" :model-value="form.body[lang] ?? ''" placeholder="Sahifa matni…" @update:model-value="v => (form.body[lang] = v)" /></div>
            </div>
          </section>

          <section class="card flex flex-col gap-2.5 px-[22px] py-5">
            <div class="flex items-center justify-between gap-2">
              <h3 class="text-base font-bold">Raqamlar <span class="text-[13px] font-medium text-subtle">(ixtiyoriy)</span></h3>
              <button type="button" class="btn-ghost h-9! text-xs!" @click="form.facts.push({ value: '', label: {} })">+ Raqam</button>
            </div>
            <div v-for="(f, i) in form.facts" :key="i" class="flex items-center gap-2">
              <input v-model="f.value" class="field w-[130px]! shrink-0" aria-label="Raqam" placeholder="23 168">
              <input v-model="f.label[lang]" class="field" :aria-label="`Izoh · ${lang}`" :placeholder="`Izoh · ${LANG_LABEL}`">
              <button type="button" class="grid size-9 shrink-0 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="Raqamni olib taşlaş" @click="form.facts.splice(i, 1)"><Icon name="trash" :size="14" /></button>
            </div>
          </section>

          <section class="card flex flex-col gap-2.5 px-[22px] py-5">
            <div class="flex items-center justify-between gap-2">
              <h3 class="text-base font-bold">Vaqt çiziği <span class="text-[13px] font-medium text-subtle">(ixtiyoriy)</span></h3>
              <button type="button" class="btn-ghost h-9! text-xs!" @click="form.timeline.push({ label: {}, text: {}, highlight: false })">+ Sana</button>
            </div>
            <div v-for="(t, i) in form.timeline" :key="i" class="grid items-center gap-2 sm:grid-cols-[130px_1fr_auto_auto]">
              <input v-model="t.label[lang]" class="field" :aria-label="`Yil · ${lang}`" placeholder="1949">
              <input v-model="t.text[lang]" class="field" :aria-label="`Matn · ${lang}`" :placeholder="`Matn · ${LANG_LABEL}`">
              <label class="flex items-center gap-1.5 text-xs text-muted"><input v-model="t.highlight" type="checkbox" class="accent-brand-800"> ajratilgan</label>
              <button type="button" class="grid size-9 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="Sanani olib taşlaş" @click="form.timeline.splice(i, 1)"><Icon name="trash" :size="14" /></button>
            </div>
          </section>

          <section class="card flex flex-col gap-3 px-[22px] py-5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <h3 class="text-base font-bold">PDF hujjatlar</h3>
              <span class="flex gap-1.5">
                <button type="button" class="btn-ghost h-9! text-xs!" @click="attInput?.click()">+ PDF yuklaş</button>
                <button type="button" class="btn-ghost h-9! text-xs!" @click="picker = true">Serverdan tanlaş</button>
              </span>
            </div>
            <input ref="attInput" type="file" accept="application/pdf" class="hidden" @change="onAttach">
            <MediaPicker :open="picker" kind="pdf" @close="picker = false" @pick="m => { form.attachments.push({ file: m, title: { uz: (m.filename ?? '').replace(/\.pdf$/i, '') }, meta: {}, display: 'open', height: 680 }); picker = false }" />
            <p v-if="!form.attachments.length" class="text-sm text-muted">PDF yöq.</p>
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
                <div role="radiogroup" aria-label="Saytda körinişi" class="grid grid-cols-2 gap-1 rounded-xl bg-canvas p-1 sm:grid-cols-4">
                  <button v-for="m in PDF_MODES" :key="m.value" type="button" role="radio" :aria-checked="a.display === m.value" class="min-h-9 rounded-[9px] px-1.5 text-xs font-semibold" :class="a.display === m.value ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="a.display = m.value">{{ m.label }}</button>
                </div>
                <div v-if="a.display === 'embed'" class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted">
                  Ramka balandligi:
                  <button v-for="h in [480, 680, 880]" :key="h" type="button" class="h-7 rounded-full px-2.5 font-semibold" :class="a.height === h ? 'bg-ink text-white' : 'border border-field bg-white'" :aria-pressed="a.height === h" @click="a.height = h">{{ h }} px</button>
                </div>
              </div>
            </div>
          </section>
        </template>

        <div v-if="sel !== null" class="flex justify-end">
          <button type="button" class="btn-danger h-10!" @click="remove">Sahifani öçiriş</button>
        </div>
      </form>
    </div>
  </div>
</template>
