<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type MediaDoc, type Paginated } from '@/lib/api'
import { dateTime, fromInputs, toInputs } from '@/lib/format'
import { mediaUrl } from '@/lib/posts'
import { useSortable } from '@/lib/sortable'
import { SITE_URL } from '@/lib/constants'
import Icon from '@/components/Icon.vue'
import ImageField from '@/components/ImageField.vue'
import I18nFields from '@/components/I18nFields.vue'

// Bosh sahifa karuseli: shu slaydlar xodim sahifalari pastida ham chiqadi (bitta manba)
type Slide = { id: number; name: string; image: MediaDoc | number | null; alt?: I18n; link?: string | null; startsAt?: string | null; endsAt?: string | null; order?: number | null }

const slides = ref<Slide[]>([])
const sel = ref<number | 'new' | null>(null)
const device = ref<'pc' | 'phone' | 'staff'>('pc')
const loading = ref(true)
const saving = ref(false)
const error = ref('')
const saved = ref(false)
const { bind, move, over, saving: sorting } = useSortable(slides, 'slides')

const form = reactive({ name: '', image: null as MediaDoc | null, alt: {} as I18n, link: '', fromDate: '', fromTime: '', toDate: '', toTime: '' })

async function load() {
  loading.value = true
  slides.value = (await api.get<Paginated<Slide>>('/slides', { sort: 'order', limit: 100, depth: 1 })).docs
  loading.value = false
  if (sel.value === null && slides.value[0]) pick(slides.value[0].id)
}
onMounted(load)

function pick(id: number | 'new') {
  sel.value = id
  error.value = ''
  saved.value = false
  const s = id === 'new' ? null : slides.value.find(x => x.id === id)
  const from = s?.startsAt ? toInputs(s.startsAt) : { date: '', time: '' }
  const to = s?.endsAt ? toInputs(s.endsAt) : { date: '', time: '' }
  Object.assign(form, {
    name: s?.name ?? '',
    image: s && typeof s.image === 'object' ? s.image : null,
    alt: { ...(s?.alt ?? {}) },
    link: s?.link ?? '',
    fromDate: from.date, fromTime: from.time, toDate: to.date, toTime: to.time,
  })
}

type Status = { key: 'on' | 'plan' | 'off'; label: string; cls: string }
function status(s: Pick<Slide, 'startsAt' | 'endsAt'>): Status {
  const now = Date.now()
  if (s.startsAt && new Date(s.startsAt).getTime() > now) return { key: 'plan', label: `${dateTime(s.startsAt).slice(0, 5)} dan`, cls: 'bg-[#FEF3DC] text-[#8A5A00]' }
  if (s.endsAt && new Date(s.endsAt).getTime() <= now) return { key: 'off', label: 'Muddati tugagan', cls: 'bg-[#F1F0F5] text-muted' }
  return { key: 'on', label: 'Faol', cls: 'bg-[#DDFBF0] text-[#0B5A43]' }
}
const activeCount = computed(() => slides.value.filter(s => status(s).key === 'on').length)
const current = computed(() => (typeof sel.value === 'number' ? slides.value.find(s => s.id === sel.value) : null))
const preview = computed(() => form.image ? (mediaUrl(form.image, 'hero') ?? mediaUrl(form.image, 'card')) : null)
const neighbour = (d: number) => {
  const i = slides.value.findIndex(s => s.id === sel.value)
  const s = slides.value[(i + d + slides.value.length) % slides.value.length]
  return s ? mediaUrl(s.image, 'card') : null
}

async function save() {
  if (!form.image) { error.value = 'Rasm yuklang'; return }
  if (!form.name.trim()) { error.value = 'Nomini yozing'; return }
  const startsAt = fromInputs(form.fromDate, form.fromTime)
  const endsAt = fromInputs(form.toDate, form.toTime || '23:59')
  if (startsAt && endsAt && endsAt <= startsAt) { error.value = 'Tugaş vaqti boşlaniş vaqtidan keyin bölsin'; return }
  saving.value = true
  error.value = ''
  const data = { name: form.name.trim(), image: form.image.id, alt: form.alt, link: form.link.trim() || null, startsAt, endsAt }
  try {
    if (sel.value === 'new') {
      const res = await api.post<{ doc: Slide }>('/slides', { ...data, order: slides.value.length + 1 }, { depth: 1 })
      await load()
      pick(res.doc.id)
    }
    else {
      await api.patch(`/slides/${sel.value}`, data, { depth: 1 })
      await load()
    }
    saved.value = true
  }
  catch (e) {
    error.value = (e as Error).message
  }
  finally {
    saving.value = false
  }
}

async function remove() {
  if (typeof sel.value !== 'number' || !confirm(`“${form.name}” slaydini olib taşlaysizmi? Rasm media kutubxonada qoladi.`)) return
  await api.del(`/slides/${sel.value}`)
  sel.value = null
  await load()
}

// Tez tanlash uchun saytdagi asosiy sahifalar
const LINKS = ['/qabul-20262027', '/yangiliklar', '/fakultetlar-va-kafedralar', '/brm', '/rektorat', '/meyoriy-hujjatlar', '/video-darsliklar', '/aloqa']
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Boş sahifa karuseli</h1>
        <p class="mt-1.5 text-[15px] text-muted">Boş sahifadagi va xodim sahifalari pastidagi almaşib turadigan rasmlar — bir joydan boşqariladi.</p>
      </div>
      <button type="button" class="btn-primary h-[46px]" @click="pick('new')"><Icon name="plus" :size="16" />Slayd qöşiş</button>
    </div>

    <!-- Slaydlar tartibi -->
    <section class="card px-5 py-[18px]">
      <div class="flex flex-wrap items-baseline justify-between gap-2.5">
        <h2 class="text-base font-bold">Slaydlar <span class="font-medium text-subtle">· saytda {{ activeCount }} tasi körinadi</span></h2>
        <span class="text-[13px] text-subtle">{{ sorting ? 'Tartib saqlanmoqda…' : 'Har biri 6 soniya · surib tartiblang' }}</span>
      </div>
      <p v-if="loading" class="mt-4 text-sm text-muted">Yuklanmoqda…</p>
      <ol v-else class="mt-3.5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <li
          v-for="(s, i) in slides" :key="s.id" v-bind="bind(i)"
          class="rounded-[14px] p-2.5 transition hover:-translate-y-0.5"
          :class="[sel === s.id ? 'border-2 border-brand-700 bg-brand-50' : 'border border-line bg-white', status(s).key === 'off' && 'opacity-60', over === i && 'ring-2 ring-mint']"
        >
          <button type="button" class="block w-full text-left" :aria-pressed="sel === s.id" :aria-label="`${s.name} — tanlaş`" @click="pick(s.id)">
            <span class="relative block aspect-video overflow-hidden rounded-[10px] bg-brand-800">
              <img v-if="mediaUrl(s.image, 'card')" :src="mediaUrl(s.image, 'card')!" alt="" class="size-full object-cover" draggable="false">
              <span class="absolute top-2 left-2 grid size-6 cursor-grab place-items-center rounded-lg bg-night/65 text-xs font-bold text-white" title="Surib köçiriş">{{ i + 1 }}</span>
            </span>
            <span class="mt-2.5 block truncate text-[13px] font-bold">{{ s.name }}</span>
            <span class="mt-1.5 block"><span class="chip text-[11px]!" :class="status(s).cls">{{ status(s).label }}</span></span>
          </button>
          <span class="mt-1.5 flex justify-end gap-1">
            <button type="button" class="grid size-7 place-items-center rounded-lg text-subtle hover:bg-canvas" :aria-label="`${s.name} — chapga`" :disabled="i === 0" @click="move(i, i - 1)">‹</button>
            <button type="button" class="grid size-7 place-items-center rounded-lg text-subtle hover:bg-canvas" :aria-label="`${s.name} — ongga`" :disabled="i === slides.length - 1" @click="move(i, i + 1)">›</button>
          </span>
        </li>
      </ol>
    </section>

    <div v-if="sel !== null" class="flex flex-wrap items-start gap-[18px]">
      <!-- Ko'rinishi -->
      <section class="card min-w-0 flex-[999_1_520px] px-5 py-[18px]">
        <div class="flex flex-wrap items-center justify-between gap-2.5">
          <h2 class="text-base font-bold">Saytda şunday körinadi</h2>
          <div role="tablist" aria-label="Qurilma" class="flex gap-0.5 rounded-[11px] bg-canvas p-[3px]">
            <button
              v-for="d in ([['pc', 'Kompyuter'], ['phone', 'Telefon'], ['staff', 'Xodim sahifasi']] as const)" :key="d[0]" type="button" role="tab" :aria-selected="device === d[0]"
              class="h-8 rounded-lg px-3 text-[13px] font-semibold" :class="device === d[0] ? 'bg-white text-ink shadow-sm' : 'text-muted'" @click="device = d[0]"
            >{{ d[1] }}</button>
          </div>
        </div>
        <div v-if="device !== 'staff'" class="mt-3.5 flex justify-center rounded-2xl bg-canvas p-[18px]">
          <div class="relative aspect-video overflow-hidden rounded-2xl bg-brand-800 shadow-[0_20px_40px_-24px_rgba(19,17,47,0.6)]" :class="device === 'pc' ? 'w-full' : 'w-[300px]'">
            <img v-if="preview" :src="preview" :alt="form.alt.uz ?? ''" class="size-full object-cover">
            <span v-else class="grid size-full place-items-center text-sm text-white/60">Rasm yuklanmagan</span>
            <span class="absolute inset-x-0 bottom-3.5 flex justify-center gap-1.5" aria-hidden="true">
              <span class="h-1.5 w-[22px] rounded-full bg-mint" /><span class="size-1.5 rounded-full bg-white/60" /><span class="size-1.5 rounded-full bg-white/60" />
            </span>
          </div>
        </div>
        <div v-else class="mt-3.5 rounded-2xl bg-canvas p-[18px]">
          <p class="mb-3 text-xs text-subtle">Xodim sahifasi → pastki qism</p>
          <div class="flex items-center justify-center gap-3" aria-hidden="true">
            <span class="aspect-video flex-[0_0_22%] overflow-hidden rounded-xl bg-brand-800 opacity-45"><img v-if="neighbour(-1)" :src="neighbour(-1)!" alt="" class="size-full object-cover"></span>
            <span class="aspect-video flex-[0_0_48%] overflow-hidden rounded-2xl bg-brand-800 shadow-[0_20px_40px_-24px_rgba(19,17,47,0.6)]"><img v-if="preview" :src="preview" alt="" class="size-full object-cover"></span>
            <span class="aspect-video flex-[0_0_22%] overflow-hidden rounded-xl bg-brand-800 opacity-45"><img v-if="neighbour(1)" :src="neighbour(1)!" alt="" class="size-full object-cover"></span>
          </div>
        </div>
        <p class="mt-3 rounded-xl bg-[#ECEAFB] px-3 py-2.5 text-[13px] leading-normal text-brand-800"><b>2 joyda çiqadi:</b> boş sahifaning yuqorisida va har bir xodim sahifasining pastida. Bu yerda özgartirsangiz, ikkalasi ham darhol yangilanadi.</p>
        <p class="mt-3 text-[13px] text-muted">Rasm yuklanganda öz-özidan WebP’ga ögiriladi va telefon uçun kiçraytiriladi — sayt tez oçiladi. <a :href="SITE_URL" target="_blank" rel="noopener" class="font-semibold text-brand-700 underline">Saytda köriş ↗</a></p>
      </section>

      <!-- Tanlangan slayd -->
      <form class="card flex min-w-0 flex-[1_1_380px] flex-col gap-3.5 px-5 py-[18px]" @submit.prevent="save">
        <h2 class="text-base font-bold">{{ sel === 'new' ? 'Yangi slayd' : current?.name }}</h2>
        <div><label for="cr-name" class="label">Nomi <span class="font-normal">(faqat admin panelda körinadi)</span></label><input id="cr-name" v-model="form.name" class="field" required placeholder="Masalan: Qabul – 2026/2027"></div>
        <div>
          <span class="label">Rasm <span class="font-normal">· 1920 × 1080 (16:9)</span></span>
          <ImageField v-model="form.image" folder="carousel" label="Kompyuterdan rasm yuklaş" />
        </div>
        <I18nFields v-model="form.alt" label="Rasm tavsifi (közi ojiz foydalanuvçilar uçun)" layout="rows" />
        <div>
          <label for="cr-link" class="label">Bosilganda oçiladi <span class="font-normal">(ixtiyoriy)</span></label>
          <input id="cr-link" v-model="form.link" class="field" list="cr-links" placeholder="/qabul-20262027 yoki https://…">
          <datalist id="cr-links"><option v-for="l in LINKS" :key="l" :value="l" /></datalist>
        </div>
        <div class="grid grid-cols-2 gap-2.5">
          <fieldset>
            <legend class="label">Körsatiş boşlanadi</legend>
            <div class="flex gap-1.5"><input v-model="form.fromDate" type="date" class="field px-2!" aria-label="Boşlaniş sanasi"><input v-model="form.fromTime" type="time" class="field w-[92px]! shrink-0 px-2!" aria-label="Boşlaniş vaqti"></div>
          </fieldset>
          <fieldset>
            <legend class="label">Tugaydi <span class="font-normal">(böş — muddatsiz)</span></legend>
            <div class="flex gap-1.5"><input v-model="form.toDate" type="date" class="field px-2!" aria-label="Tugaş sanasi"><input v-model="form.toTime" type="time" class="field w-[92px]! shrink-0 px-2!" aria-label="Tugaş vaqti"></div>
          </fieldset>
        </div>
        <p v-if="error" class="rounded-xl bg-red-50 px-3.5 py-2.5 text-sm text-red-800">{{ error }}</p>
        <p v-else-if="saved" class="rounded-xl bg-[#DDFBF0] px-3.5 py-2.5 text-sm text-[#0B5A43]">Saqlandi — saytda yangilandi.</p>
        <div class="mt-1 flex gap-2">
          <button type="submit" class="btn-primary flex-1" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
          <button v-if="sel !== 'new'" type="button" class="btn-danger" @click="remove">Olib taşlaş</button>
          <button v-else type="button" class="btn-ghost" @click="slides[0] ? pick(slides[0].id) : (sel = null)">Bekor qiliş</button>
        </div>
      </form>
    </div>
  </div>
</template>
