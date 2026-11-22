<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type I18n, type Paginated } from '@/lib/api'
import { SITE_URL } from '@/lib/constants'
import Icon from '@/components/Icon.vue'
import I18nFields from '@/components/I18nFields.vue'
import ToggleSwitch from '@/components/ToggleSwitch.vue'

// Qabul yillari: qoralama → faol (bittasi, saytning hamma joyida) → arxiv (saytda ko'rsatish/yashirish).
// Faol qilish oldingi faol yilni arxivga o'tkazadi va o'sha paytdagi yo'nalishlar/narxlarni saqlaydi.
type Status = 'draft' | 'active' | 'archive'
type DateRow = { title: I18n; period: I18n; current: boolean }
type FaqRow = { question: I18n; answer: I18n }
type Year = {
  id: number; year: string; slug: string; status: Status; public: boolean
  applyUrl: string; documents: I18n; documentsUrl: string; address: I18n; hours: I18n; phone: string; telegram: string
  dates: DateRow[]; faq: FaqRow[]; programsCount: number
}
const STATUS: Record<Status, { label: string; cls: string }> = {
  active: { label: 'Faol — saytda', cls: 'bg-[#DDFBF0] text-[#0B5A43]' },
  draft: { label: 'Qoralama', cls: 'bg-[#FFF4DB] text-[#8A5A00]' },
  archive: { label: 'Arxiv', cls: 'bg-[#F1F0F5] text-muted' },
}

const items = ref<Year[]>([])
const selected = ref<number | null>(null)
const form = reactive<Partial<Year>>({})
const saving = ref(false)
const error = ref('')
const notice = ref('')
const newYear = ref('')

async function load(keep?: number) {
  const r = await api.get<Paginated<Year>>('/admission-years', { sort: '-year', limit: 100, depth: 0 })
  items.value = r.docs
  const pick = items.value.find(y => y.id === (keep ?? selected.value)) ?? items.value.find(y => y.status === 'active') ?? items.value[0]
  if (pick) open(pick)
}
onMounted(() => load())

const current = computed(() => items.value.find(y => y.id === selected.value) ?? null)
const active = computed(() => items.value.find(y => y.status === 'active') ?? null)
const nextYear = computed(() => {
  const last = items.value.map(y => Number(y.year.slice(0, 4))).sort((a, b) => b - a)[0] ?? new Date().getFullYear()
  return `${last + 1}/${last + 2}`
})

function open(y: Year) {
  selected.value = y.id
  error.value = ''
  Object.assign(form, JSON.parse(JSON.stringify(y)))
}

async function save() {
  if (!current.value) return
  saving.value = true
  error.value = ''
  try {
    const { year, applyUrl, documents, documentsUrl, address, hours, phone, telegram, dates, faq } = form
    await api.patch(`/admission-years/${current.value.id}`, { year, applyUrl, documents, documentsUrl, address, hours, phone, telegram, dates, faq })
    notice.value = 'Saqlandi'
    await load(current.value.id)
  }
  catch (e) { error.value = (e as Error).message }
  finally { saving.value = false }
}

async function createYear() {
  const year = (newYear.value || nextYear.value).trim()
  error.value = ''
  try {
    const r = await api.post<{ doc: Year }>('/admission-years', { year, copyFrom: active.value?.id })
    newYear.value = ''
    notice.value = `${year} qoralama sifatida ochildi (joriy yildan nusxa). Saytda hali körinmaydi.`
    await load(r.doc.id)
  }
  catch (e) { error.value = (e as Error).message }
}

async function activate() {
  if (!current.value) return
  const ok = confirm(`DIQQAT! «${current.value.year}» faol qilinsinmi?\n\nSaytning hamma joyida (header, menyu, Qabul sahifasi) darhol şu yil körinadi. «${active.value?.year ?? ''}» arxivga ötadi.\n\nFaqat yuqori tashkilotlar qabul parametrlarini rasman tasdiqlaganidan keyin bosing.`)
  if (!ok) return
  try {
    await api.patch(`/admission-years/${current.value.id}`, { status: 'active' })
    notice.value = `${current.value.year} endi faol — saytda körinadi`
    await load(current.value.id)
  }
  catch (e) { error.value = (e as Error).message }
}

async function togglePublic(y: Year) {
  await api.patch(`/admission-years/${y.id}`, { public: !y.public })
  y.public = !y.public
  if (current.value?.id === y.id) form.public = y.public
}

async function remove() {
  if (!current.value || !confirm(`«${current.value.year}» butunlay öçirilsinmi? Qaytarib bölmaydi.`)) return
  await api.del(`/admission-years/${current.value.id}`)
  selected.value = null
  await load()
}

const addDate = () => form.dates?.push({ title: {}, period: {}, current: false })
const addFaq = () => form.faq?.push({ question: {}, answer: {} })
function move<T>(list: T[] | undefined, i: number, d: number) {
  if (!list || i + d < 0 || i + d >= list.length) return
  const [x] = list.splice(i, 1)
  list.splice(i + d, 0, x!)
}
</script>

<template>
  <div class="flex flex-col gap-[18px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 class="text-[28px] font-bold tracking-tight">Qabul yillari</h1>
        <p class="mt-1.5 max-w-3xl text-[15px] text-muted">Har öquv yili alohida saqlanadi. Yangi yilni oldindan qoralama sifatida tayyorlang — saytda faqat «faol» yil körinadi, eskilari arxivda qoladi.</p>
      </div>
      <a :href="`${SITE_URL}/qabul`" target="_blank" rel="noopener" class="btn-ghost h-[46px]">Saytda köriş ↗</a>
    </div>

    <!-- Ogohlantirish -->
    <div class="flex gap-3 rounded-[16px] border-2 border-[#F3B4BC] bg-[#FDECEE] px-4 py-3.5 text-[14px] leading-relaxed text-[#8E1324]" role="note">
      <Icon name="lock" :size="20" class="mt-0.5 shrink-0" />
      <p><b>Muhim:</b> qabul yilini faqat <b>yuqori tashkilotlar qabul parametrlarini rasman tasdiqlaganidan keyin</b> faol qiling. Faol qilingan yil saytning barça joyida (header «Qabul …» tugmasi, menyu, Qabul sahifasi) <b>darhol</b> körinadi.</p>
    </div>

    <p v-if="error" class="text-sm font-semibold text-[#C5192D]" role="alert">{{ error }}</p>
    <p v-else-if="notice" class="text-sm font-semibold text-[#0B5A43]" role="status">{{ notice }}</p>

    <div class="flex flex-wrap items-start gap-[18px]">
      <!-- Yillar ro'yxati -->
      <section class="card min-w-0 flex-[1_1_300px] px-5 py-[18px] lg:sticky lg:top-4">
        <h2 class="text-lg font-bold">Yillar</h2>
        <ul class="mt-3 flex flex-col gap-2">
          <li v-for="y in items" :key="y.id" class="flex items-center gap-2 rounded-[14px] border px-3 py-2.5" :class="selected === y.id ? 'border-2 border-brand-700' : 'border-[#F0EEF6]'">
            <button type="button" class="min-w-0 flex-1 text-left" @click="open(y)">
              <span class="block text-[16px] font-bold tabular-nums">{{ y.year }}</span>
              <span class="mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-semibold" :class="STATUS[y.status].cls">{{ STATUS[y.status].label }}</span>
            </button>
            <button
              v-if="y.status === 'archive'"
              type="button"
              class="grid size-9 shrink-0 place-items-center rounded-full transition-colors"
              :class="y.public ? 'bg-[#DDFBF0] text-[#0B5A43]' : 'bg-[#F1F0F5] text-muted'"
              :title="y.public ? 'Arxiv saytda körinadi — yaşiriş uçun bosing' : 'Arxiv saytda yaşirin — körsatiş uçun bosing'"
              @click="togglePublic(y)"
            >
              <Icon :name="y.public ? 'eye' : 'eyeOff'" :size="17" />
            </button>
          </li>
        </ul>
        <div class="mt-4 rounded-[14px] bg-[#F5F3FE] p-3">
          <label for="ay-new" class="label">Yangi öquv yili</label>
          <div class="flex gap-2">
            <input id="ay-new" v-model="newYear" class="field" :placeholder="nextYear">
            <button type="button" class="btn-primary h-[46px] shrink-0 gap-1.5" @click="createYear"><Icon name="plus" :size="16" /> Oçiş</button>
          </div>
          <p class="mt-1.5 text-xs text-muted">Joriy yildan nusxa olinadi (sanalar, hujjatlar, savol-javob) — qoralama, saytda körinmaydi.</p>
        </div>
      </section>

      <!-- Tanlangan yil -->
      <form v-if="current" class="card min-w-0 flex-[3_1_560px] px-5 py-[18px]" @submit.prevent="save">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h2 class="text-lg font-bold">Qabul {{ current.year }} <span class="ml-2 rounded-full px-2 py-0.5 align-middle text-xs font-semibold" :class="STATUS[current.status].cls">{{ STATUS[current.status].label }}</span></h2>
          <div class="flex flex-wrap gap-2">
            <button v-if="current.status !== 'active'" type="button" class="h-[46px] rounded-full bg-[#C5192D] px-5 text-sm font-bold text-white transition hover:bg-[#A31424]" @click="activate">Faol qiliş</button>
            <button v-if="current.status !== 'active'" type="button" class="btn-ghost h-[46px] text-[#C5192D]" @click="remove">Öçiriş</button>
          </div>
        </div>
        <p v-if="current.status === 'archive'" class="mt-2 text-sm text-muted">Arxiv: {{ current.programsCount }} ta yönalish va narxlari {{ current.year }} holatida saqlangan. Saytda: {{ current.public ? `/qabul/${current.slug}` : 'yaşirin' }}.</p>

        <div class="mt-4 grid gap-3.5 sm:grid-cols-2">
          <div><label for="ay-year" class="label">Öquv yili</label><input id="ay-year" v-model="form.year" class="field" placeholder="2027/2028"></div>
          <div><label for="ay-apply" class="label">Ariza topşiriş havolasi</label><input id="ay-apply" v-model="form.applyUrl" class="field" placeholder="https://my.uzbmb.uz"></div>
          <div><label for="ay-phone" class="label">Telefon</label><input id="ay-phone" v-model="form.phone" class="field"></div>
          <div><label for="ay-tg" class="label">Telegram</label><input id="ay-tg" v-model="form.telegram" class="field"></div>
        </div>
        <div class="mt-3.5 grid gap-3.5">
          <I18nFields v-model="form.address" label="Qabul komissiyasi manzili" layout="rows" id-prefix="ay-addr" />
          <I18nFields v-model="form.hours" label="Iş vaqti" layout="rows" id-prefix="ay-hours" />
          <I18nFields v-model="form.documents" label="Kerakli hujjatlar (har qatorda bittadan)" textarea :rows="4" layout="rows" id-prefix="ay-docs" />
          <div><label for="ay-docurl" class="label">Hujjatlar röyxati havolasi</label><input id="ay-docurl" v-model="form.documentsUrl" class="field"></div>
        </div>

        <!-- Muhim sanalar -->
        <div class="mt-6 flex items-center justify-between"><h3 class="text-base font-bold">Muhim sanalar</h3><button type="button" class="btn-ghost h-10 gap-1.5 text-sm" @click="addDate"><Icon name="plus" :size="15" /> Bosqiç</button></div>
        <ol class="mt-2 grid gap-2.5">
          <li v-for="(d, i) in form.dates" :key="i" class="rounded-[14px] border border-[#F0EEF6] p-3">
            <div class="mb-2 flex items-center justify-between gap-2">
              <span class="text-sm font-bold text-muted">{{ i + 1 }}-bosqiç</span>
              <span class="flex gap-1">
                <button type="button" class="btn-ghost h-8 px-2 text-xs" @click="move(form.dates, i, -1)">↑</button>
                <button type="button" class="btn-ghost h-8 px-2 text-xs" @click="move(form.dates, i, 1)">↓</button>
                <button type="button" class="btn-ghost h-8 px-2 text-xs text-[#C5192D]" @click="form.dates?.splice(i, 1)">Öçiriş</button>
              </span>
            </div>
            <div class="grid gap-2.5">
              <I18nFields v-model="d.title" label="Bosqiç nomi" :id-prefix="`ay-d${i}t`" />
              <I18nFields v-model="d.period" label="Muddat" :id-prefix="`ay-d${i}p`" />
              <ToggleSwitch v-model="d.current" label="Hozirgi bosqiç (saytda ajratib körsatiladi)" />
            </div>
          </li>
        </ol>

        <!-- Savol-javob -->
        <div class="mt-6 flex items-center justify-between"><h3 class="text-base font-bold">Köp söraladigan savollar</h3><button type="button" class="btn-ghost h-10 gap-1.5 text-sm" @click="addFaq"><Icon name="plus" :size="15" /> Savol</button></div>
        <ol class="mt-2 grid gap-2.5">
          <li v-for="(x, i) in form.faq" :key="i" class="rounded-[14px] border border-[#F0EEF6] p-3">
            <div class="mb-2 flex items-center justify-between gap-2">
              <span class="text-sm font-bold text-muted">{{ i + 1 }}-savol</span>
              <span class="flex gap-1">
                <button type="button" class="btn-ghost h-8 px-2 text-xs" @click="move(form.faq, i, -1)">↑</button>
                <button type="button" class="btn-ghost h-8 px-2 text-xs" @click="move(form.faq, i, 1)">↓</button>
                <button type="button" class="btn-ghost h-8 px-2 text-xs text-[#C5192D]" @click="form.faq?.splice(i, 1)">Öçiriş</button>
              </span>
            </div>
            <div class="grid gap-2.5">
              <I18nFields v-model="x.question" label="Savol" :id-prefix="`ay-f${i}q`" />
              <I18nFields v-model="x.answer" label="Javob" textarea :rows="3" :id-prefix="`ay-f${i}a`" />
            </div>
          </li>
        </ol>

        <p class="mt-5 text-xs text-muted">Yönalişlar va kontrakt narxlari «Ta’lim yönalişlari» bölimidan olinadi (qabulda körsatiladiganlari). Yil arxivga ötganda ular şu yil uçun saqlab qolinadi.</p>
        <div class="mt-4 flex gap-2">
          <button class="btn-primary h-[46px]" :disabled="saving">{{ saving ? 'Saqlanmoqda…' : 'Saqlaş' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>
