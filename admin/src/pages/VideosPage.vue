<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type Paginated } from '@/lib/api'
import { fromInputs, toInputs } from '@/lib/format'
import { SITE_URL } from '@/lib/constants'
import { useSortable } from '@/lib/sortable'
import I18nFields from '@/components/I18nFields.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Video darsliklar: videolar YouTube'da turadi, sayt faqat ko'rsatadi
type Category = { id: number; key: string; title: I18n; greeting?: string | null; order?: number }
type Video = { id: number; url: string; title: I18n; category: number | Category; teacher?: string | null; duration?: string | null; thumbnail?: string | null; order?: number | null }
type Page = { live?: boolean; liveUrl?: string | null; nextTitle?: I18n; nextAt?: string | null; channelUrl?: string | null }

const cats = ref<Category[]>([])
const videos = ref<Video[]>([])
const tab = ref<number | 'all'>('all')
const editing = ref<number | 'new'>('new')
const formEl = ref<HTMLElement>()

const empty = () => ({ url: '', title: {} as I18n, category: null as number | null, teacher: '', duration: '', thumbnail: '' })
const form = reactive(empty())
const fetchState = ref<'idle' | 'busy' | 'ok' | 'error'>('idle')
const fetchMsg = ref('')
const saving = ref(false)
const error = ref('')

const catId = (v: Video) => (typeof v.category === 'object' ? v.category.id : v.category)
const shown = computed(() => (tab.value === 'all' ? videos.value : videos.value.filter(v => catId(v) === tab.value)))
// Surib tartiblash faqat bitta toifa ichida: yangi tartib raqamlari bo'yicha umumiy ro'yxat qayta saralanadi
const sortList = computed<Video[]>({
  get: () => shown.value,
  set: () => { videos.value = [...videos.value].sort((a, b) => (a.order ?? 0) - (b.order ?? 0)) },
})
const { bind, over } = useSortable(sortList, 'videos')

async function load() {
  const [c, v, p] = await Promise.all([
    api.get<Paginated<Category>>('/video-categories', { sort: 'order', limit: 100 }),
    api.get<Paginated<Video>>('/videos', { sort: 'order', limit: 1000, depth: 0 }),
    api.get<Page>('/globals/video-page'),
  ])
  cats.value = c.docs
  videos.value = v.docs
  Object.assign(live, { on: !!p.live, liveUrl: p.liveUrl ?? '', nextTitle: { ...(p.nextTitle ?? {}) }, channelUrl: p.channelUrl ?? '', ...(() => { const t = p.nextAt ? toInputs(p.nextAt) : { date: '', time: '' }; return { nextDate: t.date, nextTime: t.time } })() })
  if (form.category === null) form.category = cats.value[0]?.id ?? null
}
onMounted(load)

async function edit(v: Video | null) {
  editing.value = v ? v.id : 'new'
  error.value = ''
  fetchState.value = 'idle'
  Object.assign(form, empty(), v ? { url: v.url, title: { ...v.title }, category: catId(v), teacher: v.teacher ?? '', duration: v.duration ?? '', thumbnail: v.thumbnail ?? '' } : { category: tab.value === 'all' ? cats.value[0]?.id ?? null : tab.value })
  await nextTick()
  formEl.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function fetchYoutube() {
  if (!form.url.trim()) return
  fetchState.value = 'busy'
  try {
    const r = await api.get<{ url: string; title: string | null; thumbnail: string; duration: string | null }>('/panel/youtube', { url: form.url.trim() })
    form.url = r.url
    form.thumbnail = r.thumbnail
    if (r.duration) form.duration = r.duration
    if (r.title && !form.title.uz) form.title = { ...form.title, uz: r.title }
    const got = ['nom', r.duration ? 'davomiylik' : null, 'muqova'].filter(Boolean).join(', ')
    fetchMsg.value = `✓ YouTube’dan olindi: ${got}${r.duration ? '' : ' · davomiylikni qölda yozing'}`
    fetchState.value = 'ok'
  }
  catch (e) {
    fetchMsg.value = (e as Error).message
    fetchState.value = 'error'
  }
}

async function save() {
  if (!form.url.trim() || !form.title.uz?.trim() || !form.category) { error.value = 'Havola, özbekça nomi va toifa majburiy'; return }
  saving.value = true
  error.value = ''
  const data = { url: form.url.trim(), title: form.title, category: form.category, teacher: form.teacher.trim() || null, duration: form.duration.trim() || null, thumbnail: form.thumbnail || null }
  try {
    if (editing.value === 'new') await api.post('/videos', { ...data, order: videos.value.length + 1 })
    else await api.patch(`/videos/${editing.value}`, data)
    await load()
    edit(null)
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function remove() {
  if (typeof editing.value !== 'number' || !confirm('Video saytdan olib taşlansinmi? (YouTube’dagi videoga tegilmaydi)')) return
  await api.del(`/videos/${editing.value}`)
  await load()
  edit(null)
}

// Jonli efir va kanal
const live = reactive({ on: false, liveUrl: '', nextTitle: {} as I18n, nextDate: '', nextTime: '', channelUrl: '' })
const liveSaved = ref(false)
async function saveLive() {
  await api.post('/globals/video-page', { live: live.on, liveUrl: live.liveUrl.trim() || null, nextTitle: live.nextTitle, nextAt: fromInputs(live.nextDate, live.nextTime), channelUrl: live.channelUrl.trim() || null })
  liveSaved.value = true
  setTimeout(() => (liveSaved.value = false), 2500)
}

// Toifa qo'shish
const catForm = ref<{ key: string; title: I18n; greeting: string } | null>(null)
async function saveCat() {
  if (!catForm.value?.key.trim() || !catForm.value.title.uz?.trim()) return
  const res = await api.post<{ doc: Category }>('/video-categories', { ...catForm.value, key: catForm.value.key.trim().toLowerCase(), order: cats.value.length + 1 })
  catForm.value = null
  await load()
  tab.value = res.doc.id
}

const COLORS = ['#382B85', '#C5192D', '#0A97D9', '#13112F', '#DD1367', '#0E7A5A']
const catColor = (id: number) => COLORS[cats.value.findIndex(c => c.id === id) % COLORS.length]
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Video darsliklar</h1>
        <p class="mt-1.5 text-[15px] text-muted">Videolar YouTube’da turadi — sayt ularni körsatadi, server yuklanmaydi.</p>
      </div>
      <a :href="`${SITE_URL}/video-darsliklar`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
    </div>

    <div class="flex flex-wrap items-stretch gap-[18px]">
      <!-- Video qo'shish / tahrirlash -->
      <form ref="formEl" class="card min-w-0 flex-[999_1_520px] px-5 py-[18px]" @submit.prevent="save">
        <div class="flex items-center justify-between gap-2">
          <h2 class="text-base font-bold">{{ editing === 'new' ? 'Video qöşiş' : 'Videoni tahrirlaş' }}</h2>
          <button v-if="editing !== 'new'" type="button" class="text-xs font-semibold text-brand-700 underline" @click="edit(null)">+ yangi video</button>
        </div>
        <div class="mt-3.5 flex gap-2">
          <label class="flex h-[46px] flex-1 items-center gap-2 rounded-xl border border-field px-3 focus-within:border-brand-700 focus-within:ring-4 focus-within:ring-brand-700/10">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="#E5243B" aria-hidden="true"><path d="M23 7.2a3 3 0 0 0-2.1-2.1C19 4.6 12 4.6 12 4.6s-7 0-8.9.5A3 3 0 0 0 1 7.2 31 31 0 0 0 .5 12a31 31 0 0 0 .5 4.8 3 3 0 0 0 2.1 2.1c1.9.5 8.9.5 8.9.5s7 0 8.9-.5a3 3 0 0 0 2.1-2.1 31 31 0 0 0 .5-4.8 31 31 0 0 0-.5-4.8zM9.7 15.1V8.9l5.8 3.1z" /></svg>
            <input v-model="form.url" aria-label="YouTube havolasi" placeholder="https://youtu.be/…" class="min-w-0 flex-1 bg-transparent text-sm font-medium outline-none" @keydown.enter.prevent="fetchYoutube">
          </label>
          <button type="button" class="btn-primary h-[46px]" :disabled="fetchState === 'busy' || !form.url" @click="fetchYoutube">{{ fetchState === 'busy' ? 'Olinmoqda…' : 'Olib keliş' }}</button>
        </div>
        <div class="mt-3.5 flex flex-wrap gap-4">
          <div class="relative grid aspect-video flex-[0_0_240px] place-items-center overflow-hidden rounded-xl bg-brand-700">
            <img v-if="form.thumbnail" :src="form.thumbnail" alt="" class="absolute inset-0 size-full object-cover">
            <span aria-hidden="true" class="relative grid size-12 place-items-center rounded-full bg-white/92 text-lg text-brand-700">▶</span>
            <span v-if="form.duration" class="absolute right-2 bottom-2 rounded-md bg-night/80 px-1.5 py-0.5 text-[11px] font-semibold text-white">{{ form.duration }}</span>
          </div>
          <div class="flex min-w-0 flex-[1_1_260px] flex-col gap-2.5">
            <p v-if="fetchState === 'ok' || fetchState === 'error'" class="rounded-[10px] px-2.5 py-2 text-xs font-semibold" :class="fetchState === 'ok' ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-red-50 text-red-800'">{{ fetchMsg }}</p>
            <I18nFields v-model="form.title" label="Nomi" required />
            <div class="grid grid-cols-2 gap-2.5">
              <div><label for="vd-c" class="label">Toifa</label><select id="vd-c" v-model="form.category" class="field"><option v-for="c in cats" :key="c.id" :value="c.id">{{ c.title.uz }}</option></select></div>
              <div><label for="vd-teacher" class="label">Öqituvçi</label><input id="vd-teacher" v-model="form.teacher" class="field" placeholder="F.I.Ş."></div>
              <div><label for="vd-dur" class="label">Davomiyligi</label><input id="vd-dur" v-model="form.duration" class="field" placeholder="24:15"></div>
            </div>
          </div>
        </div>
        <p v-if="error" class="mt-3 rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <div class="mt-3.5 flex justify-end gap-2">
          <button v-if="editing !== 'new'" type="button" class="btn-danger mr-auto h-[42px]!" @click="remove">Olib taşlaş</button>
          <button type="submit" class="btn-primary h-[42px]!" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
        </div>
      </form>

      <!-- Jonli efir -->
      <form class="card flex min-w-0 flex-[1_1_320px] flex-col gap-3 px-5 py-[18px]" @submit.prevent="saveLive">
        <div class="flex items-center justify-between gap-2.5">
          <h2 id="vd-live-l" class="text-base font-bold">Jonli efir</h2>
          <ToggleSwitch v-model="live.on" label="Jonli efir" on="#E5243B" />
        </div>
        <p class="rounded-xl px-3 py-2.5 text-[13px] leading-normal" :class="live.on ? 'bg-[#FDECEA] text-[#8F2219]' : 'bg-canvas text-muted'">{{ live.on ? '● Hozir efirda — saytdagi Video sahifasida qizil “Jonli” belgisi körinadi.' : 'Efir yöq. Yoqilsa, saytda “Jonli efir” bloki çiqadi.' }}</p>
        <div><label for="vd-lurl" class="label">Efir havolasi</label><input id="vd-lurl" v-model="live.liveUrl" class="field" placeholder="https://youtube.com/live/…"></div>
        <fieldset>
          <legend class="label">Keyingi efir</legend>
          <div class="flex gap-1.5"><input v-model="live.nextDate" type="date" class="field px-2!" aria-label="Keyingi efir sanasi"><input v-model="live.nextTime" type="time" class="field w-[92px]! shrink-0 px-2!" aria-label="Keyingi efir vaqti"></div>
          <input v-model="live.nextTitle.uz" class="field mt-2" aria-label="Keyingi efir nomi" placeholder="Efir nomi (özbekça)">
        </fieldset>
        <div><label for="vd-ch" class="label">YouTube kanal</label><input id="vd-ch" v-model="live.channelUrl" class="field"></div>
        <div class="mt-auto flex items-center justify-end gap-2.5">
          <span v-if="liveSaved" class="text-xs font-semibold text-mint-text">Saqlandi ✓</span>
          <button type="submit" class="btn-primary h-[42px]!">Saqlaş</button>
        </div>
      </form>
    </div>

    <!-- Videolar -->
    <section class="card px-5 py-4">
      <div role="tablist" aria-label="Toifalar" class="flex flex-wrap gap-1.5">
        <button type="button" role="tab" :aria-selected="tab === 'all'" class="h-9 rounded-full px-3.5 text-[13px] font-semibold" :class="tab === 'all' ? 'bg-ink text-white' : 'border border-field text-[#3D3958]'" @click="tab = 'all'">Hammasi <span class="opacity-70">{{ videos.length }}</span></button>
        <button v-for="c in cats" :key="c.id" type="button" role="tab" :aria-selected="tab === c.id" class="h-9 rounded-full px-3.5 text-[13px] font-semibold" :class="tab === c.id ? 'bg-ink text-white' : 'border border-field text-[#3D3958]'" @click="tab = c.id">{{ c.title.uz }} <span class="opacity-70">{{ videos.filter(v => catId(v) === c.id).length }}</span></button>
        <button type="button" class="h-9 rounded-full border border-dashed border-[#D3CFE3] px-3.5 text-[13px] font-semibold text-brand-700" @click="catForm = { key: '', title: {}, greeting: '' }">+ Toifa</button>
      </div>
      <form v-if="catForm" class="mt-3.5 grid gap-3 rounded-2xl bg-canvas p-4" @submit.prevent="saveCat">
        <div class="grid gap-3 sm:grid-cols-2">
          <div><label for="vc-key" class="label">Til kodi *</label><input id="vc-key" v-model="catForm.key" class="field" required pattern="[a-zA-Z-]{2,10}" placeholder="it, ko, ar…"></div>
          <div><label for="vc-gr" class="label">Bezak söz (kartada)</label><input id="vc-gr" v-model="catForm.greeting" class="field" placeholder="Ciao"></div>
        </div>
        <I18nFields v-model="catForm.title" label="Nomi" required />
        <span class="flex justify-end gap-2"><button type="button" class="btn-ghost h-10!" @click="catForm = null">Bekor qiliş</button><button type="submit" class="btn-primary h-10!">Toifani saqlaş</button></span>
      </form>
      <p v-if="!shown.length" class="py-10 text-center text-sm text-muted">Bu toifada video yöq.</p>
      <ul class="mt-4 grid grid-cols-2 gap-3.5 md:grid-cols-3 xl:grid-cols-4">
        <li v-for="(v, i) in shown" :key="v.id" v-bind="tab === 'all' ? {} : bind(i)" class="overflow-hidden rounded-[14px] border transition hover:-translate-y-0.5" :class="[editing === v.id ? 'border-2 border-brand-700' : 'border-[#F0EEF6]', over === i && 'ring-2 ring-mint']">
          <button type="button" class="block w-full text-left" :aria-label="`${v.title.uz} — tahrirlaş`" @click="edit(v)">
            <span class="relative grid aspect-video place-items-center overflow-hidden" :style="{ background: catColor(catId(v)) }">
              <img v-if="v.thumbnail" :src="v.thumbnail" alt="" class="absolute inset-0 size-full object-cover" draggable="false" loading="lazy">
              <span aria-hidden="true" class="relative grid size-9 place-items-center rounded-full bg-white/90 text-[13px]" :style="{ color: catColor(catId(v)) }">▶</span>
              <span v-if="v.duration" class="absolute right-1.5 bottom-1.5 rounded-md bg-night/80 px-1.5 py-0.5 text-[11px] text-white">{{ v.duration }}</span>
              <span class="absolute top-1.5 left-1.5 rounded-md bg-night/60 px-1.5 py-0.5 text-[11px] text-white" :class="tab !== 'all' && 'cursor-grab'">{{ tab !== 'all' ? '⋮⋮ ' : '' }}{{ i + 1 }}</span>
            </span>
            <span class="block px-3 py-2.5">
              <span class="block text-[13px] leading-snug font-bold">{{ v.title.uz }}</span>
              <span class="mt-1 block text-xs text-subtle">{{ v.teacher || 'Öqituvçi körsatilmagan' }}</span>
            </span>
          </button>
        </li>
      </ul>
      <p v-if="tab === 'all' && shown.length" class="mt-3 text-xs text-subtle">Tartibni özgartiriş uçun toifani tanlang va kartalarni surib qöying.</p>
    </section>
  </div>
</template>
