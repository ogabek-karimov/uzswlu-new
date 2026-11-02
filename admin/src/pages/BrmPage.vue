<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated, uploadMedia } from '@/lib/api'
import { auth } from '@/lib/auth'
import { LANGS, type Lang, PDF_MODES, SDG_COLORS, SITE_URL } from '@/lib/constants'
import { fileSize } from '@/lib/format'
import { mediaUrl } from '@/lib/posts'
import Icon from '@/components/Icon.vue'
import MediaPicker from '@/components/MediaPicker.vue'
import RichEditor from '@/components/RichEditor.vue'

// BRM — 17 maqsad sahifasi: tavsif, ichki bo'limlar (saytdagi tablar), hisobotlar va THE Impact natijasi.
// Yangilik qo'shilganda BRM tanlansa, u maqsad sahifasining "Faoliyat" qismida o'z-o'zidan chiqadi.
type Section = { id?: string; key?: string | null; title: I18n; body: I18n; images: (MediaDoc | number)[] }
type Report = { id?: string; file?: MediaDoc | number | null; url?: string | null; title: I18n; meta?: string | null; display: 'embed' | 'open' | 'download'; height?: number | null }
type Goal = { id: number; n: number; url: string; title: I18n; subtitle?: I18n; impactRank?: string | null; impactScore?: string | null; highlight?: { label?: string | null; value?: I18n }; sections?: Section[]; reports?: Report[] }

const goals = ref<Goal[]>([])
const counts = ref<Record<number, number>>({})
const sel = ref(6)
const lang = ref<Lang>('uz')
const impactYear = ref<number | null>(null)
const saving = ref(false)
const saved = ref(false)
const error = ref('')
const openSection = ref<number | null>(null)
const DOC_MODES = PDF_MODES.filter(m => m.value !== 'link')

const blank = () => ({ title: {} as I18n, subtitle: {} as I18n, impactRank: '', impactScore: '', hlLabel: '', hlValue: {} as I18n, sections: [] as Section[], reports: [] as Report[] })
const form = reactive(blank())
const current = computed(() => goals.value.find(g => g.n === sel.value) ?? null)
const obj = (v: unknown) => (v && typeof v === 'object' ? v as MediaDoc : null)

async function load() {
  const [g, c, page] = await Promise.all([
    api.get<Paginated<Goal>>('/sdg-goals', { sort: 'n', limit: 17, depth: 1 }),
    api.get<Record<number, number>>('/panel/sdg-counts'),
    api.get<{ impactYear?: number }>('/globals/sdg-page'),
  ])
  goals.value = g.docs
  counts.value = c
  impactYear.value = page.impactYear ?? null
  pick(sel.value)
}
onMounted(load)

function pick(n: number) {
  sel.value = n
  saved.value = false
  error.value = ''
  openSection.value = null
  const g = goals.value.find(x => x.n === n)
  if (!g) return
  Object.assign(form, {
    title: { ...g.title }, subtitle: { ...(g.subtitle ?? {}) }, impactRank: g.impactRank ?? '', impactScore: g.impactScore ?? '',
    hlLabel: g.highlight?.label ?? '', hlValue: { ...(g.highlight?.value ?? {}) },
    sections: (g.sections ?? []).map(s => ({ key: s.key, title: { ...s.title }, body: { ...(s.body ?? {}) }, images: [...(s.images ?? [])] })),
    reports: (g.reports ?? []).map(r => ({ file: r.file ?? null, url: r.url ?? '', title: { ...(r.title ?? {}) }, meta: r.meta ?? '', display: r.display ?? 'open', height: r.height ?? 680 })),
  })
}

async function save() {
  if (!current.value || !form.title.uz?.trim()) { error.value = 'Özbekça nomi majburiy'; return }
  saving.value = true
  error.value = ''
  try {
    await Promise.all([
      api.patch(`/sdg-goals/${current.value.id}`, {
        title: form.title, subtitle: form.subtitle, impactRank: form.impactRank.trim() || null, impactScore: form.impactScore.trim() || null,
        highlight: { label: form.hlLabel.trim() || null, value: form.hlValue },
        sections: form.sections.map(s => ({ key: s.key ?? null, title: s.title, body: s.body, images: s.images.map(m => (typeof m === 'object' ? m.id : m)) })),
        reports: form.reports.map(r => ({ file: obj(r.file)?.id ?? (typeof r.file === 'number' ? r.file : null), url: r.url?.trim() || null, title: r.title, meta: r.meta?.trim() || null, display: r.display, height: r.height })),
      }),
      api.post('/globals/sdg-page', { impactYear: impactYear.value }),
    ])
    await load()
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

// Ichki bo'limlar
function addSection() {
  form.sections.push({ title: { uz: 'Yangi bölim' }, body: {}, images: [] })
  openSection.value = form.sections.length - 1
}
function moveSection(i: number, d: number) {
  const j = i + d
  if (j < 0 || j >= form.sections.length) return
  const [s] = form.sections.splice(i, 1)
  form.sections.splice(j, 0, s!)
  openSection.value = openSection.value === i ? j : openSection.value
}
function removeSection(i: number) {
  if (!confirm(`“${form.sections[i]?.title.uz}” bölimi olib taşlansinmi?`)) return
  form.sections.splice(i, 1)
  openSection.value = null
}
const sectionMeta = (s: Section) => [s.body.uz?.replace(/<[^>]+>/g, '').trim() ? 'matn' : 'böş', s.images.length ? `${s.images.length} rasm` : null].filter(Boolean).join(' · ')
const imgInput = ref<HTMLInputElement>()
const imgFor = ref<number | null>(null)
async function onImages(e: Event) {
  const files = [...((e.target as HTMLInputElement).files ?? [])]
  const i = imgFor.value
  if (i === null) return
  for (const f of files) form.sections[i]!.images.push(await uploadMedia(f, { folder: 'posts' }))
  ;(e.target as HTMLInputElement).value = ''
}

// Hisobotlar (PDF yoki havola)
const picker = ref(false)
const reportInput = ref<HTMLInputElement>()
const uploading = ref(false)
async function onReport(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const m = await uploadMedia(file, { folder: 'docs' })
    form.reports.push({ file: m, title: { uz: file.name.replace(/\.pdf$/i, '') }, display: 'open', height: 680 })
  }
  finally {
    uploading.value = false
    ;(e.target as HTMLInputElement).value = ''
  }
}
function addLink() {
  form.reports.push({ file: null, url: 'https://', title: {}, display: 'open', height: 680 })
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">BRM — Barqaror rivojlaniş maqsadlari</h1>
        <p class="mt-1.5 text-[15px] text-muted">17 ta maqsad sahifasi. Yangilik qöşilganda BRM tanlansa, u şu maqsad sahifasida öz-özidan çiqadi.</p>
      </div>
      <a :href="`${SITE_URL}/brm`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">BRM sahifasi ↗</a>
    </div>

    <!-- 17 maqsad -->
    <section class="card p-4">
      <ul class="grid grid-cols-6 gap-2 sm:grid-cols-9 xl:grid-cols-[repeat(17,minmax(0,1fr))]">
        <li v-for="g in goals" :key="g.n">
          <button
            type="button" :aria-pressed="sel === g.n" :aria-label="`BRM ${g.n} — ${g.title.uz}`" :title="g.title.uz ?? undefined"
            class="flex aspect-square w-full flex-col justify-between rounded-xl p-2 text-left text-white" :class="sel === g.n && 'shadow-[0_0_0_3px_#fff,0_0_0_5px_#13112F]'"
            :style="{ background: SDG_COLORS[g.n - 1] }" @click="pick(g.n)"
          >
            <b class="text-lg leading-none">{{ g.n }}</b>
            <span class="text-[10px] leading-tight opacity-90">{{ counts[g.n] ?? 0 }} post</span>
          </button>
        </li>
      </ul>
    </section>

    <form v-if="current" class="flex flex-col gap-[18px]" @submit.prevent="save">
      <section class="card flex flex-wrap items-center gap-4 overflow-hidden p-0!">
        <span class="grid size-[92px] shrink-0 place-items-center text-[40px] font-extrabold text-white" :style="{ background: SDG_COLORS[current.n - 1] }">{{ current.n }}</span>
        <div class="min-w-0 flex-1 py-3">
          <p class="text-xs text-muted">Maqsad {{ current.n }} · {{ current.url }}</p>
          <h2 class="text-xl font-bold">{{ form.title.uz }}</h2>
        </div>
        <a :href="`${SITE_URL}${current.url}`" target="_blank" rel="noopener" class="btn-ghost mr-5 h-10!">Saytda köriş ↗</a>
      </section>

      <div class="flex flex-wrap items-start gap-[18px]">
        <div class="flex min-w-0 flex-[999_1_560px] flex-col gap-[18px]">
          <!-- Matnlar -->
          <section class="card flex flex-col gap-3 px-5 py-[18px]">
            <div class="flex items-center justify-between gap-2">
              <h3 class="text-base font-bold">Matnlar</h3>
              <div role="tablist" aria-label="Til" class="flex gap-1">
                <button v-for="l in LANGS" :key="l.code" type="button" role="tab" :aria-selected="lang === l.code" class="h-7 min-w-[38px] rounded-lg px-2 text-[11px] font-bold" :class="lang === l.code ? 'bg-ink text-white' : 'border border-field bg-white text-muted'" @click="lang = l.code">{{ l.short }}</button>
              </div>
            </div>
            <div><label for="sdg-t" class="label">Nomi · {{ LANGS.find(l => l.code === lang)?.label }}</label><input id="sdg-t" v-model="form.title[lang]" class="field" :required="lang === 'uz'"></div>
            <div><label for="sdg-d" class="label">Maqsad tavsifi · {{ LANGS.find(l => l.code === lang)?.label }}</label><textarea id="sdg-d" v-model="form.subtitle[lang]" rows="3" class="field h-auto! py-2.5 leading-relaxed" /></div>
          </section>

          <!-- Ichki bo'limlar -->
          <section class="card flex flex-col gap-2.5 px-5 py-[18px]">
            <div class="flex items-center justify-between gap-2">
              <h3 class="text-base font-bold">Içki bölimlar <span class="text-[13px] font-medium text-subtle">(saytdagi tablar)</span></h3>
              <button type="button" class="btn-ghost h-9! text-xs!" @click="addSection">+ Bölim</button>
            </div>
            <p v-if="!form.sections.length" class="text-sm text-muted">Bölim yöq.</p>
            <div v-for="(s, i) in form.sections" :key="i" class="rounded-[14px] border" :class="openSection === i ? 'border-brand-700' : 'border-line'">
              <div class="flex items-center gap-2.5 px-3.5 py-2.5">
                <span class="flex flex-col">
                  <button type="button" class="h-4 text-[10px] text-subtle" :aria-label="`${s.title.uz} — yuqoriga`" :disabled="i === 0" @click="moveSection(i, -1)">▲</button>
                  <button type="button" class="h-4 text-[10px] text-subtle" :aria-label="`${s.title.uz} — pastga`" :disabled="i === form.sections.length - 1" @click="moveSection(i, 1)">▼</button>
                </span>
                <span class="min-w-0 flex-1"><b class="block truncate text-sm">{{ s.title.uz || 'Nomsiz bölim' }}</b><span class="text-xs text-subtle">{{ sectionMeta(s) }}</span></span>
                <button type="button" class="btn-ghost h-8! px-3! text-xs!" :aria-expanded="openSection === i" @click="openSection = openSection === i ? null : i">{{ openSection === i ? 'Yopiş' : 'Tahrirlaş' }}</button>
                <button type="button" class="grid size-8 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" :aria-label="`${s.title.uz} — olib taşlaş`" @click="removeSection(i)"><Icon name="trash" :size="14" /></button>
              </div>
              <div v-if="openSection === i" class="flex flex-col gap-3 border-t border-line px-3.5 py-3">
                <div><label :for="`sec-t-${i}`" class="label">Bölim nomi · {{ LANGS.find(l => l.code === lang)?.label }}</label><input :id="`sec-t-${i}`" v-model="s.title[lang]" class="field"></div>
                <div>
                  <span class="label">Matn · {{ LANGS.find(l => l.code === lang)?.label }}</span>
                  <div class="overflow-hidden rounded-xl border border-field"><RichEditor :key="`${i}-${lang}`" :model-value="s.body[lang] ?? ''" placeholder="Bölim matni…" @update:model-value="v => (s.body[lang] = v)" /></div>
                </div>
                <div>
                  <span class="label">Rasmlar</span>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="(m, k) in s.images" :key="k" class="relative size-20 overflow-hidden rounded-lg bg-canvas">
                      <img v-if="mediaUrl(m as MediaDoc)" :src="mediaUrl(m as MediaDoc)!" alt="" class="size-full object-cover">
                      <button type="button" class="absolute top-1 right-1 grid size-5 place-items-center rounded-full bg-night/70 text-[10px] text-white" aria-label="Rasmni olib taşlaş" @click="s.images.splice(k, 1)">✕</button>
                    </span>
                    <button type="button" class="grid size-20 place-items-center rounded-lg border-2 border-dashed border-[#D3CFE3] text-xs font-semibold text-brand-700" @click="imgFor = i; imgInput?.click()">+ Rasm</button>
                  </div>
                </div>
              </div>
            </div>
            <input ref="imgInput" type="file" accept="image/*" multiple class="hidden" @change="onImages">
          </section>

          <!-- Hisobotlar -->
          <section class="card flex flex-col gap-3 px-5 py-[18px]">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div><h3 class="text-base font-bold">Hisobotlar (PDF)</h3><p class="text-xs text-muted">Har bir PDF saytda qanday körinişini tanlang.</p></div>
              <span class="flex flex-wrap gap-1.5">
                <button type="button" class="btn-ghost h-9! text-xs!" :disabled="uploading" @click="reportInput?.click()">{{ uploading ? 'Yuklanmoqda…' : '+ PDF yuklaş' }}</button>
                <button type="button" class="btn-ghost h-9! text-xs!" @click="picker = true">Serverdan tanlaş</button>
                <button type="button" class="btn-ghost h-9! text-xs!" @click="addLink">+ Havola</button>
              </span>
            </div>
            <input ref="reportInput" type="file" accept="application/pdf" class="hidden" @change="onReport">
            <MediaPicker :open="picker" kind="pdf" @close="picker = false" @pick="m => { form.reports.push({ file: m, title: { uz: (m.filename ?? '').replace(/\.pdf$/i, '') }, display: 'open', height: 680 }); picker = false }" />
            <p v-if="!form.reports.length" class="text-sm text-muted">Hisobot yöq.</p>
            <div v-for="(r, i) in form.reports" :key="i" class="rounded-[14px] border border-line p-3.5">
              <div class="flex items-start gap-3">
                <span aria-hidden="true" class="grid h-11 w-9 shrink-0 place-items-center rounded-md text-[10px] font-extrabold" :class="obj(r.file) ? 'bg-[#FDECEA] text-[#B42318]' : 'bg-brand-50 text-brand-700'">{{ obj(r.file) ? 'PDF' : '↗' }}</span>
                <div class="grid min-w-0 flex-1 gap-2 sm:grid-cols-[1fr_160px]">
                  <input v-model="r.title[lang]" class="field" :aria-label="`Hisobot nomi · ${lang}`" :placeholder="`Nomi · ${LANGS.find(l => l.code === lang)?.label}`">
                  <input v-model="r.meta" class="field" aria-label="Izoh" placeholder="Izoh: 22.02.2023">
                  <input v-if="!obj(r.file)" v-model="r.url" class="field sm:col-span-2" type="url" aria-label="Havola" placeholder="https://…">
                  <p v-else class="text-xs text-subtle sm:col-span-2">{{ obj(r.file)?.filename }} · {{ fileSize(obj(r.file)?.filesize) }}</p>
                </div>
                <button type="button" class="grid size-8 shrink-0 place-items-center rounded-lg text-subtle hover:bg-red-50 hover:text-red-700" aria-label="Hisobotni olib taşlaş" @click="form.reports.splice(i, 1)"><Icon name="trash" :size="14" /></button>
              </div>
              <div v-if="obj(r.file)" class="mt-3">
                <div role="radiogroup" aria-label="Saytda körinişi" class="grid grid-cols-3 gap-1 rounded-xl bg-canvas p-1">
                  <button v-for="m in DOC_MODES" :key="m.value" type="button" role="radio" :aria-checked="r.display === m.value" class="min-h-9 rounded-[9px] px-1.5 text-xs font-semibold" :class="r.display === m.value ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="r.display = m.value as Report['display']">{{ m.label }}</button>
                </div>
                <div v-if="r.display === 'embed'" class="mt-2 flex flex-wrap items-center gap-1.5 text-xs text-muted">
                  Ramka balandligi:
                  <button v-for="z in [[480, 'Kiçik'], [680, 'Örta'], [880, 'Katta']] as const" :key="z[0]" type="button" class="h-7 rounded-full px-2.5 font-semibold" :class="r.height === z[0] ? 'bg-ink text-white' : 'border border-field bg-white'" :aria-pressed="r.height === z[0]" @click="r.height = z[0]">{{ z[1] }} · {{ z[0] }}px</button>
                </div>
                <p class="mt-1.5 text-xs text-subtle">{{ DOC_MODES.find(m => m.value === r.display)?.note }}</p>
              </div>
            </div>
          </section>
        </div>

        <div class="flex min-w-0 flex-[1_1_320px] flex-col gap-[18px]">
          <section class="card flex flex-col gap-3 px-5 py-[18px]">
            <h3 class="text-base font-bold">THE Impact Rankings</h3>
            <div class="grid grid-cols-3 gap-2">
              <div><label for="sdg-y" class="label">Yil</label><input id="sdg-y" v-model.number="impactYear" type="number" min="2019" max="2100" class="field"></div>
              <div><label for="sdg-r" class="label">Örni</label><input id="sdg-r" v-model="form.impactRank" class="field" placeholder="401–600"></div>
              <div><label for="sdg-s" class="label">Ball</label><input id="sdg-s" v-model="form.impactScore" class="field" placeholder="43.5"></div>
            </div>
            <p class="text-xs text-subtle">BRM boş sahifasidagi ğildirak va jadvalda körinadi. Yil barça maqsadlar uçun umumiy.</p>
          </section>

          <section class="card flex flex-col gap-3 px-5 py-[18px]">
            <h3 class="text-base font-bold">Ajratilgan natija <span class="text-[13px] font-medium text-subtle">(ixtiyoriy)</span></h3>
            <div><label for="sdg-hl" class="label">Sarlavha</label><input id="sdg-hl" v-model="form.hlLabel" class="field" placeholder="GreenMetric 2026 · Water"></div>
            <div><label for="sdg-hv" class="label">Natija · {{ LANGS.find(l => l.code === lang)?.label }}</label><input id="sdg-hv" v-model="form.hlValue[lang]" class="field" placeholder="Özbekistonda #1"></div>
          </section>

          <section class="card flex flex-col gap-2 px-5 py-[18px]">
            <h3 class="text-base font-bold">Boğlangan postlar</h3>
            <p class="text-[13px] leading-normal text-muted"><b class="text-ink">{{ counts[current.n] ?? 0 }} ta</b> yangilik bu maqsadga boğlangan — ular sahifaning “Faoliyat” qismida öz-özidan çiqadi.</p>
            <RouterLink v-if="auth.user.value?.role !== 'sdg'" :to="{ path: '/postlar/news', query: { sdg: String(current.n) } }" class="btn-ghost h-10!">Postlar röyxatida köriş</RouterLink>
          </section>

          <div class="sticky bottom-4 flex flex-col gap-2">
            <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
            <p v-else-if="saved" class="rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — saytda yangilandi.</p>
            <button type="submit" class="btn-primary h-[46px]" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : `BRM ${current.n} ni saqlaş` }}</button>
          </div>
        </div>
      </div>
    </form>
  </div>
</template>
