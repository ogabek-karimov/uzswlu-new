<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { dateTime, fileSize } from '@/lib/format'
import { LANGS, PDF_MODES, SITE_URL } from '@/lib/constants'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'
import PdfSlot from '@/components/PdfSlot.vue'

// Me'yoriy hujjatlar: har bir tilda alohida PDF yoki tashqi havola; saytdagi ko'rinishi; qaysi sahifalarda
type Lang = 'uz' | 'ru' | 'en' | 'zh'
type Category = { id: number; title: I18n; order?: number }
type Doc = {
  id: number; title: I18n; category: number | Category; number?: string | null
  files?: Partial<Record<Lang, MediaDoc | number | null>>; url?: string | null
  display?: 'embed' | 'open' | 'download'; height?: number | null; pages?: string[] | null; downloads?: number; order?: number; updatedAt?: string
}

const DOC_MODES = PDF_MODES.filter(m => m.value !== 'link')
const MODE_BADGE: Record<string, string> = { embed: 'bg-[#ECEAFB] text-brand-800', open: 'bg-canvas text-[#3D3958]', download: 'bg-[#DDFBF0] text-[#0B5A43]' }
const PAGE_NAMES: Record<string, string> = { 'meyoriy-hujjatlar': 'Me’yoriy hujjatlar' }

const cats = ref<Category[]>([])
const docs = ref<Doc[]>([])
const cat = ref<number | null>(null)
const q = ref('')
const editing = ref<number | 'new' | null>(null)
const saving = ref(false)
const error = ref('')
const formEl = ref<HTMLElement>()

const empty = () => ({
  title: {} as I18n, category: cat.value ?? cats.value[0]?.id ?? null as number | null, number: '',
  files: { uz: null, ru: null, en: null, zh: null } as Record<Lang, MediaDoc | null>, url: '', useLink: false,
  display: 'open' as 'embed' | 'open' | 'download', height: 680, pages: ['meyoriy-hujjatlar'] as string[], pageInput: '',
})
const form = reactive(empty())

async function load() {
  const [c, d] = await Promise.all([
    api.get<Paginated<Category>>('/doc-categories', { sort: 'order', limit: 200 }),
    api.get<Paginated<Doc>>('/documents', { sort: 'order', limit: 1000, depth: 1 }),
  ])
  cats.value = c.docs
  docs.value = d.docs
  if (cat.value === null) cat.value = cats.value[0]?.id ?? null
}
onMounted(load)

const catId = (d: Doc) => (typeof d.category === 'object' ? d.category.id : d.category)
const count = (id: number) => docs.value.filter(d => catId(d) === id).length
const shown = computed(() => {
  const s = q.value.trim().toLowerCase()
  return docs.value.filter(d => (s ? LANGS.some(l => (d.title[l.code] ?? '').toLowerCase().includes(s)) : catId(d) === cat.value))
})
const catTitle = computed(() => (q.value.trim() ? 'Qidiruv natijalari' : cats.value.find(c => c.id === cat.value)?.title.uz ?? ''))
const fileObj = (v: MediaDoc | number | null | undefined) => (v && typeof v === 'object' ? v : null)
const meta = (d: Doc) => {
  const f = fileObj(d.files?.uz)
  return [d.number, f ? fileSize(f.filesize) : d.url ? 'Havola' : 'Fayl yöq', d.updatedAt ? dateTime(d.updatedAt).slice(0, 10) : null].filter(Boolean).join(' · ')
}
const pagesLabel = (d: Doc) => (d.pages ?? []).map(p => PAGE_NAMES[p] ?? p).join(', ') || '—'

async function open(id: number | 'new') {
  editing.value = id
  error.value = ''
  const d = id === 'new' ? null : docs.value.find(x => x.id === id)
  Object.assign(form, empty(), d
    ? {
        title: { ...d.title }, category: catId(d), number: d.number ?? '',
        files: Object.fromEntries(LANGS.map(l => [l.code, fileObj(d.files?.[l.code])])) as Record<Lang, MediaDoc | null>,
        url: d.url ?? '', useLink: !fileObj(d.files?.uz) && !!d.url,
        display: d.display ?? 'open', height: d.height ?? 680, pages: [...(d.pages ?? [])],
      }
    : {})
  await nextTick()
  formEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function addPage() {
  const v = form.pageInput.trim().replace(/^\/+/, '')
  if (v && !form.pages.includes(v)) form.pages.push(v)
  form.pageInput = ''
}

async function save() {
  if (!form.title.uz?.trim()) { error.value = 'Özbekça nomi majburiy'; return }
  if (!form.category) { error.value = 'Toifani tanlang'; return }
  if (form.useLink ? !form.url.trim() : !form.files.uz) { error.value = form.useLink ? 'Havolani yozing' : 'Özbekça PDF faylni yuklang'; return }
  saving.value = true
  error.value = ''
  const data = {
    title: form.title, category: form.category, number: form.number.trim() || null,
    files: form.useLink ? { uz: null, ru: null, en: null, zh: null } : Object.fromEntries(LANGS.map(l => [l.code, form.files[l.code]?.id ?? null])),
    url: form.useLink ? form.url.trim() : null,
    display: form.display, height: form.height, pages: form.pages,
  }
  try {
    if (editing.value === 'new') await api.post('/documents', { ...data, order: docs.value.length + 1 })
    else await api.patch(`/documents/${editing.value}`, data)
    cat.value = form.category
    editing.value = null
    await load()
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function remove() {
  if (typeof editing.value !== 'number' || !confirm('Hujjat saytdan olib taşlansinmi? PDF fayl media kutubxonada qoladi.')) return
  await api.del(`/documents/${editing.value}`)
  editing.value = null
  await load()
}

// "Yangi versiya": o'zbekcha PDF almashtiriladi — saytdagi havola o'zgarmaydi
const versionInput = ref<HTMLInputElement>()
const versionFor = ref<number | null>(null)
const versionBusy = ref<number | null>(null)
function newVersion(id: number) {
  versionFor.value = id
  versionInput.value?.click()
}
async function onVersion(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  const id = versionFor.value
  if (!file || !id) return
  versionBusy.value = id
  try {
    const media = await uploadMedia(file, { folder: 'docs' })
    const d = docs.value.find(x => x.id === id)
    await api.patch(`/documents/${id}`, { files: { ...Object.fromEntries(LANGS.map(l => [l.code, fileObj(d?.files?.[l.code])?.id ?? null])), uz: media.id }, url: null })
    await load()
  }
  catch (err) {
    alert((err as Error).message)
  }
  finally {
    versionBusy.value = null
    if (versionInput.value) versionInput.value.value = ''
  }
}

// Toifa qo'shish / nomini o'zgartirish
const catForm = ref<{ id: number | 'new'; title: I18n } | null>(null)
async function saveCat() {
  if (!catForm.value?.title.uz?.trim()) return
  const { id, title } = catForm.value
  if (id === 'new') {
    const res = await api.post<{ doc: Category }>('/doc-categories', { title, order: cats.value.length + 1 })
    cat.value = res.doc.id
  }
  else await api.patch(`/doc-categories/${id}`, { title })
  catForm.value = null
  await load()
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Hujjatlar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Nizom, qaror va hisobotlar. Bitta hujjatni bir neçta sahifaga biriktiriş mumkin.</p>
      </div>
      <span class="flex gap-2">
        <a :href="`${SITE_URL}/meyoriy-hujjatlar`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
        <button type="button" class="btn-primary h-[46px]" :aria-expanded="editing === 'new'" @click="editing === 'new' ? (editing = null) : open('new')"><Icon name="plus" :size="16" />Hujjat qöşiş</button>
      </span>
    </div>

    <div class="flex flex-wrap items-start gap-[18px]">
      <aside class="card min-w-0 flex-[1_1_240px] p-3 lg:max-w-[280px]">
        <p class="mx-2 mt-1 mb-2 text-[11px] font-bold tracking-[0.12em] text-subtle uppercase">Kategoriyalar</p>
        <nav aria-label="Kategoriyalar" class="flex flex-col gap-0.5">
          <div v-for="c in cats" :key="c.id" class="group flex items-center">
            <button
              type="button" :aria-current="cat === c.id && !q ? 'page' : undefined"
              class="flex min-h-10 flex-1 items-center gap-2 rounded-[10px] px-2.5 py-2 text-left text-[13px] leading-snug"
              :class="cat === c.id && !q ? 'bg-brand-50 font-semibold shadow-[inset_3px_0_0_var(--color-brand-700)]' : 'font-medium'"
              @click="cat = c.id; q = ''"
            ><span class="flex-1">{{ c.title.uz }}</span><span class="text-xs text-subtle">{{ count(c.id) }}</span></button>
            <button type="button" class="grid size-8 place-items-center rounded-lg text-subtle opacity-0 group-hover:opacity-100 focus:opacity-100" :aria-label="`${c.title.uz} — nomini özgartiriş`" @click="catForm = { id: c.id, title: { ...c.title } }"><Icon name="edit" :size="13" /></button>
          </div>
        </nav>
        <form v-if="catForm" class="mt-2.5 flex flex-col gap-2 rounded-xl bg-canvas p-2.5" @submit.prevent="saveCat">
          <I18nFields v-model="catForm.title" label="Kategoriya nomi" layout="rows" />
          <span class="flex gap-1.5"><button type="button" class="btn-ghost h-9! flex-1 text-xs!" @click="catForm = null">Bekor</button><button type="submit" class="btn-primary h-9! flex-1 text-xs!">Saqlaş</button></span>
        </form>
        <button v-else type="button" class="mx-1 mt-2.5 mb-1 h-[38px] w-[calc(100%-8px)] rounded-[10px] border border-dashed border-[#D3CFE3] text-xs font-semibold text-brand-700" @click="catForm = { id: 'new', title: {} }">+ Kategoriya</button>
      </aside>

      <div class="flex min-w-0 flex-[999_1_560px] flex-col gap-[18px]">
        <form v-if="editing !== null" ref="formEl" class="card border-2! border-brand-700! px-5 py-[18px]" :aria-label="editing === 'new' ? 'Yangi hujjat' : 'Hujjatni tahrirlaş'" @submit.prevent="save">
          <div class="flex items-center justify-between gap-2.5">
            <h2 class="text-base font-bold">{{ editing === 'new' ? 'Yangi hujjat' : 'Hujjatni tahrirlaş' }}</h2>
            <button type="button" aria-label="Yopiş" class="grid size-[34px] place-items-center rounded-full bg-canvas text-muted" @click="editing = null"><Icon name="x" :size="15" /></button>
          </div>
          <div class="mt-3.5"><I18nFields v-model="form.title" label="Nomi" required :placeholders="{ uz: 'Masalan: Ilmiy kengaş nizomi', ru: 'Положение об Учёном совете', en: 'Academic Council regulations', zh: '学术委员会章程' }" /></div>
          <div class="mt-3 grid gap-3 sm:grid-cols-2">
            <div><label for="dc-cat" class="label">Kategoriya</label><select id="dc-cat" v-model="form.category" class="field"><option v-for="c in cats" :key="c.id" :value="c.id">{{ c.title.uz }}</option></select></div>
            <div><label for="dc-num" class="label">Hujjat raqami va sanasi</label><input id="dc-num" v-model="form.number" class="field" placeholder="№ 145 · 12.09.2026"></div>
          </div>

          <div class="mt-3.5 flex flex-wrap items-center gap-4 text-[13px]">
            <label class="flex items-center gap-2"><input v-model="form.useLink" type="radio" :value="false" class="accent-brand-800"> PDF fayl</label>
            <label class="flex items-center gap-2"><input v-model="form.useLink" type="radio" :value="true" class="accent-brand-800"> Tashqi havola <span class="text-subtle">(masalan, lex.uz)</span></label>
          </div>
          <div v-if="!form.useLink" class="mt-2.5 grid grid-cols-2 gap-2 lg:grid-cols-4">
            <PdfSlot v-for="l in LANGS" :key="l.code" v-model="form.files[l.code]" :lang="l.label" :note="l.code === 'uz' ? 'majburiy' : 'ixtiyoriy'" />
          </div>
          <div v-else class="mt-2.5"><label for="dc-url" class="sr-only">Havola</label><input id="dc-url" v-model="form.url" class="field" type="url" placeholder="https://lex.uz/…"></div>

          <div v-if="!form.useLink" class="mt-3">
            <span class="label">Saytda körinişi</span>
            <div role="radiogroup" aria-label="Saytda körinişi" class="grid grid-cols-3 gap-1 rounded-xl bg-canvas p-1">
              <button v-for="m in DOC_MODES" :key="m.value" type="button" role="radio" :aria-checked="form.display === m.value" class="min-h-9 rounded-[9px] px-1.5 text-xs font-semibold" :class="form.display === m.value ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="form.display = m.value as typeof form.display">{{ m.label }}</button>
            </div>
            <p class="mt-1.5 text-xs text-subtle">{{ DOC_MODES.find(m => m.value === form.display)?.note }}</p>
            <div v-if="form.display === 'embed'" class="mt-2 flex items-center gap-2 text-xs text-muted">
              Ramka balandligi:
              <button v-for="h in [480, 680, 880]" :key="h" type="button" class="h-8 rounded-lg px-2.5 font-semibold" :class="form.height === h ? 'bg-ink text-white' : 'border border-field bg-white'" :aria-pressed="form.height === h" @click="form.height = h">{{ h }} px</button>
            </div>
          </div>

          <div class="mt-3">
            <span class="label">Qaysi sahifalarda çiqadi</span>
            <div class="flex flex-wrap gap-1.5 rounded-[10px] border border-field p-2">
              <span v-for="(p, i) in form.pages" :key="p" class="inline-flex items-center gap-1 rounded-full bg-[#F0EEF6] py-1 pr-1.5 pl-2.5 text-xs font-semibold">{{ PAGE_NAMES[p] ?? p }}<button type="button" class="grid size-5 place-items-center rounded-full hover:bg-white" :aria-label="`${PAGE_NAMES[p] ?? p} — olib taşlaş`" @click="form.pages.splice(i, 1)">✕</button></span>
              <input v-model="form.pageInput" aria-label="Sahifa qöşiş" list="dc-pages" placeholder="Sahifa manzili (masalan, korrupsiyaga-qarshi)…" class="min-w-[160px] flex-1 border-0 text-[13px] outline-none" @keydown.enter.prevent="addPage" @change="addPage">
              <datalist id="dc-pages"><option v-for="(name, key) in PAGE_NAMES" :key="key" :value="key">{{ name }}</option></datalist>
            </div>
          </div>

          <p v-if="error" class="mt-3 rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
          <div class="mt-3.5 flex flex-wrap justify-end gap-2">
            <button v-if="editing !== 'new'" type="button" class="btn-danger mr-auto h-[42px]!" @click="remove">Öçiriş</button>
            <button type="button" class="btn-ghost h-[42px]!" @click="editing = null">Bekor qiliş</button>
            <button type="submit" class="btn-primary h-[42px]!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
          </div>
        </form>

        <section class="card overflow-hidden">
          <div class="flex flex-wrap items-center gap-2.5 px-5 py-4">
            <h2 class="mr-auto text-base font-bold">{{ catTitle }}</h2>
            <label class="flex h-10 items-center gap-2 rounded-[10px] border border-field px-3 text-muted">
              <Icon name="search" :size="15" />
              <input v-model="q" aria-label="Hujjat qidiriş" placeholder="Hujjat qidiriş…" class="w-[180px] bg-transparent text-[13px] outline-none">
            </label>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full min-w-[900px] border-collapse text-sm">
              <thead>
                <tr class="bg-[#FAF9FD] text-left text-xs text-muted">
                  <th scope="col" class="px-5 py-3 font-semibold">Hujjat</th>
                  <th scope="col" class="px-3 py-3 font-semibold">Fayllar</th>
                  <th scope="col" class="px-3 py-3 font-semibold">Saytda körinişi</th>
                  <th scope="col" class="px-3 py-3 font-semibold">Sahifalarda</th>
                  <th scope="col" class="px-3 py-3 text-right font-semibold">Yuklab olindi</th>
                  <th scope="col" class="py-3 pr-5 pl-3"><span class="sr-only">Amallar</span></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!shown.length"><td colspan="6" class="px-5 py-10 text-center text-muted">Bu kategoriyada hujjat yöq.</td></tr>
                <tr v-for="d in shown" :key="d.id" class="border-t border-[#F0EEF6] hover:bg-[#FAF9FD]">
                  <td class="max-w-[420px] px-5 py-3.5">
                    <span class="flex items-start gap-3">
                      <span aria-hidden="true" class="grid h-11 w-9 shrink-0 place-items-center rounded-md text-[10px] font-extrabold" :class="fileObj(d.files?.uz) ? 'bg-[#FDECEA] text-[#B42318]' : 'bg-brand-50 text-brand-700'">{{ fileObj(d.files?.uz) ? 'PDF' : '↗' }}</span>
                      <span class="min-w-0"><b class="block leading-snug">{{ d.title.uz }}</b><span class="mt-0.5 block text-xs text-subtle">{{ meta(d) }}</span></span>
                    </span>
                  </td>
                  <td class="px-3 py-3.5 whitespace-nowrap">
                    <span v-if="fileObj(d.files?.uz)" class="flex gap-[3px]">
                      <span v-for="l in LANGS" :key="l.code" :title="`${l.short}: ${fileObj(d.files?.[l.code]) ? 'fayl bor' : 'yöq'}`" class="rounded-md px-1.5 py-[3px] text-[11px] font-bold" :class="fileObj(d.files?.[l.code]) ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-canvas text-[#B8B4C8]'">{{ l.short }}</span>
                    </span>
                    <a v-else-if="d.url" :href="d.url" target="_blank" rel="noopener" class="text-xs font-semibold text-brand-700 underline">havola ↗</a>
                  </td>
                  <td class="px-3 py-3.5 whitespace-nowrap"><span v-if="fileObj(d.files?.uz)" class="chip" :class="MODE_BADGE[d.display ?? 'open']">{{ DOC_MODES.find(m => m.value === (d.display ?? 'open'))?.label }}</span><span v-else class="text-xs text-subtle">Tashqi sahifa</span></td>
                  <td class="max-w-[220px] px-3 py-3.5 text-[13px] text-muted">{{ pagesLabel(d) }}</td>
                  <td class="px-3 py-3.5 text-right font-semibold tabular-nums">{{ (d.downloads ?? 0).toLocaleString('ru-RU') }}</td>
                  <td class="py-3.5 pr-5 pl-3 text-right whitespace-nowrap">
                    <button type="button" class="mr-1 size-[34px] rounded-[9px] border border-line text-muted hover:border-brand-700" :aria-label="`${d.title.uz} — tahrirlaş`" @click="open(d.id)">✎</button>
                    <button type="button" class="size-[34px] rounded-[9px] border border-line text-muted hover:border-brand-700" :aria-label="`${d.title.uz} — yangi versiya yuklaş`" :title="'Yangi versiya yuklaş (özbekça PDF)'" :disabled="versionBusy === d.id" @click="newVersion(d.id)">{{ versionBusy === d.id ? '…' : '↥' }}</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
        <input ref="versionInput" type="file" accept="application/pdf" class="hidden" @change="onVersion">
        <p class="text-[13px] text-muted">Hujjatning yangi versiyasi yuklansa, eski havola işlayveradi — sayt avtomatik yangisini beradi.</p>
      </div>
    </div>
  </div>
</template>
